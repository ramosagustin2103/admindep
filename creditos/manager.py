from datetime import date
from creditos.models import *
from django_afip.models import *
from django.db import transaction



class LiquidacionCreator:

	""" Creador y Listador de objetos pre-confirmacion y para guardar """

	def __init__(
			self,
			data_inicial, # Diccionario LIMPIO que contiene "punto", "fecha_operacion", "concepto"
			data_creditos, # Lista de Diccionarios LIMPIOS que contiene "campos basicos para crear objetos de credito". Ver en views.py
			data_plazos=None, # Lista de Diccionarios LIMPIOS que contienen "accesorio" y "plazo"
			preconceptos=None # QUERYSET con Objetos de tipo Credito para incorporar a la liquidacion
		):
		self.punto = data_inicial['punto']
		self.club = self.punto.owner.club_set.first()
		self.periodo = data_inicial['fecha_operacion']
		self.fecha_factura = data_inicial['fecha_factura']
		self.concepto = data_inicial['concepto']
		self.creditos = data_creditos
		self.data_plazos = data_plazos
		self.preconceptos = preconceptos or Credito.objects.none()

	def reagrupar_creditos(self):

		""" Reagrupacion de creditos por destinatario de factura """

		cabezas = set([credito['cabeza'] for credito in self.creditos])
		grupos_de_creditos = [[credito for credito in self.creditos if credito['cabeza'] == cabeza] for cabeza in cabezas]
		return grupos_de_creditos

	def colocar_accesorios(self, credito):

		""" Le agrega los accesorios al credito """

		accesorios = credito.ingreso.accesorio_set.filter(finalizacion__isnull=True)
		if accesorios:
			for a in accesorios:
				if a.clase == "descuento":
					credito.acc_desc = a
				elif a.clase == "bonificacion":
					if a.condicion == "grupo":
						if credito.socio.grupo_set.first() and credito.detalle == "cat":
							credito.acc_bonif = a
				elif a.clase == "interes":
					credito.acc_int = a

		return credito


	def hacer_total(self, socio, grupo_creditos=None, grupo_preconceptos=None):

		"""
		Calcula el total por factura.
		"""

		suma = 0
		if grupo_creditos:
			for credito in grupo_creditos:
				suma += credito.bruto
		preconceptos_socio = self.preconceptos.filter(socio=socio)
		if grupo_preconceptos:
			for credito in grupo_preconceptos:
				suma += credito.bruto

		return suma

	def colocar_plazos(self, credito):

            """ Recibe objeto de tipo credito y le coloca fecha de vencimiento y fecha de gracia si es que encuentra """

            for a in self.data_plazos:
                if credito.ingreso in a['accesorio'].ingreso.all():
                    if a['accesorio'].clase == "interes":
                        credito.vencimiento = a['plazo']
                    elif a['accesorio'].clase == "descuento":
                        credito.gracia = a['plazo']


	def hacer_credito(self, c):

		""" Crea los objetos de tipo Credito """

		# Creacion de los creditos
		data = c.copy()
		del data['cabeza']
		data['fecha'] = self.fecha_factura
		credito = Credito(**data)
		# Colocacion de vencimiento y gracia
		self.colocar_plazos(credito)
		self.colocar_accesorios(credito)
		if credito.bruto == 0.00:
			credito.fin = self.fecha_factura			
		return credito


	def hacer_documento(self, cabeza, grupo_creditos=None, grupo_preconceptos=None):

		""" Crea diccionario con receipt, factura y creditos por la cabeza """

		# Creacion del receipt sin totales ni finalizacion de conceptos
		receipt = Receipt(
			point_of_sales=self.punto,
			receipt_type=ReceiptType.objects.get(code="11"),
			concept=self.concepto,
			document_type=cabeza.tipo_documento,
			document_number=cabeza.numero_documento,
			issued_date=self.fecha_factura,
			net_untaxed=0,
			exempt_amount=0,
			expiration_date=self.fecha_factura,
			currency=CurrencyType.objects.get(code="PES"),
		)
		# Agregar finalizacion de conceptos en el receipt recien creado
		if not self.concepto.code == "1":
			receipt.service_start = self.fecha_factura
			receipt.service_end = self.fecha_factura

		# Creacion de la factura. Nada tiene que ver con el receipt. Por ahora
		factura = Factura(
			club=self.club,
			socio=cabeza,
		)

		# Creacion de los creditos
		creditos = []
		if grupo_creditos:
			for c in grupo_creditos:
				credito = self.hacer_credito(c)
				if credito:
					creditos.append(credito)


		total_factura = self.hacer_total(socio=cabeza, grupo_creditos=creditos, grupo_preconceptos=grupo_preconceptos)
		receipt.total_amount = total_factura
		receipt.net_taxed = total_factura
		documento = {
			'receipt': receipt,
			'factura': factura,
			'creditos': creditos,
			'preconceptos': grupo_preconceptos
		}
		return documento


	def cabezas_preconceptos(self):

		cabezas = []
		if self.preconceptos:
			for credito in self.preconceptos:
				if credito.socio.grupo_set.first():
					cabeza = credito.socio.grupo_set.first().cabeza
				else:
					cabeza = credito.socio
				cabezas.append(cabeza)
		return set(cabezas)


	def listar_documentos(self):

		""" Lista todos los documentos que se pueden realizar una vez recibidos los creditos """

		grupos_de_creditos = self.reagrupar_creditos()
		documentos = []
		for grupo_creditos in grupos_de_creditos:
			cabeza = grupo_creditos[0]['cabeza']
			socios = [cabeza]
			grupo = cabeza.grupo_set.first()
			if grupo:
				for socio in grupo.socios.all():
					socios.append(socio)
			preconceptos_cabeza = self.preconceptos.filter(socio__in=socios)			
			documentos.append(self.hacer_documento(cabeza=cabeza, grupo_creditos=grupo_creditos, grupo_preconceptos=preconceptos_cabeza))
		if not grupos_de_creditos:
			cabezas = self.cabezas_preconceptos()
			for cabeza in cabezas:
				socios = [cabeza]
				grupo = cabeza.grupo_set.first()
				if grupo:
					for socio in grupo.socios.all():
						socios.append(socio)
				preconceptos_cabeza = self.preconceptos.filter(socio__in=socios)
				documentos.append(self.hacer_documento(cabeza=cabeza, grupo_preconceptos=preconceptos_cabeza))



		return documentos



	def guardar_preconceptos(self, liquidacion):

		self.preconceptos.update(liquidacion=liquidacion)
		self.preconceptos.update(fecha=self.fecha_factura)


	@transaction.atomic
	def guardar(self):
		"""incorpora los objetos procesados en esta clase en la base de datos"""

		liquidacion = Liquidacion(
			club = self.club,
			punto = self.punto,
			fecha = date.today(),
			estado = 'errores'
		)
		liquidacion.save()
		facturas = []
		creditos= []
		for documento in self.listar_documentos():
			receipt = documento['receipt']
			receipt.save()
			documento['factura'].receipt = receipt
			documento['factura'].liquidacion = liquidacion
			facturas.append(documento['factura'])
			for credito in documento['creditos']:
				credito.liquidacion = liquidacion
				creditos.append(credito)
		Factura.objects.bulk_create(facturas)
		Credito.objects.bulk_create(creditos)
		self.guardar_preconceptos(liquidacion)
		
		liquidacion.estado = 'en_proceso'
		liquidacion.save()
		
		return liquidacion
