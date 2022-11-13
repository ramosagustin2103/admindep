from __future__ import unicode_literals
from datetime import date
from django.db import models
from clubes.models import *
from parametros.models import *
from creditos.models import *
from django_afip.models import *
from django_mercadopago.models import Preference, Payment
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from admindep.funciones import armar_link, emisor_mail
from django.urls import reverse
import base64
from django_afip.pdf import ReceiptBarcodeGenerator
from weasyprint import HTML
from django.core.files.uploadedfile import SimpleUploadedFile
from creditos.models import *

class Comprobante(models.Model):
	club = models.ForeignKey(Club, on_delete=models.CASCADE)
	socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
	punto = models.ForeignKey(PointOfSales, blank=True, null=True, on_delete=models.CASCADE)
	numero = models.PositiveIntegerField(blank=True, null=True)
	fecha = models.DateField(blank=True, null=True)
	descripcion = models.TextField(blank=True, null=True)
	asiento = models.ForeignKey(Asiento, on_delete=models.SET_NULL, blank=True, null=True)
	pdf = models.FileField(upload_to="comprobantes/pdf/", blank=True, null=True)
	anulado = models.DateField(blank=True, null=True)
	asiento_anulado = models.ForeignKey(Asiento, on_delete=models.SET_NULL, blank=True, null=True, related_name='asiento_comp_anulado')
	nota_credito = models.ForeignKey(Receipt, blank=True, null=True, on_delete=models.SET_NULL, related_name='nota_credito')
	nota_debito = models.ForeignKey(Receipt, blank=True, null=True, on_delete=models.SET_NULL, related_name='nota_debito')
	total = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
	nota_credito_anulado = models.ForeignKey(Receipt, blank=True, null=True, on_delete=models.SET_NULL, related_name='nota_credito_anulado')
	nota_debito_anulado = models.ForeignKey(Receipt, blank=True, null=True, on_delete=models.SET_NULL, related_name='nota_debito_anulado')
	asiento_anulado = models.ForeignKey(Asiento, on_delete=models.SET_NULL, blank=True, null=True, related_name='comprobante_anulado')
	pdf_anulado = models.FileField(upload_to="comprobantes/pdf/", blank=True, null=True)


	@property
	def notaDebito(self):
		if self.nota_debito:
			return self.nota_debito
		else:
			return self.nota_debito_anulado

	@property
	def notaCredito(self):
		if self.nota_credito:
			return self.nota_credito
		else:
			return self.nota_credito_anulado


	def formatoAfipRCX(self):
		agregado = "0"
		punto_numero = str(self.punto)
		largo = len(punto_numero)
		ceros = 4 - largo
		ceros = agregado * ceros
		punto_numero = ceros + punto_numero
		numero = str(self.numero)
		largo = len(numero)
		ceros = 8 - largo
		ceros = agregado * ceros
		numero = ceros + numero
		return "{}-{}".format(punto_numero, numero)

	def formatoAfipNDC(self):
		agregado = "0"
		punto_numero = str(self.notaDebito.point_of_sales)
		largo = len(punto_numero)
		ceros = 4 - largo
		ceros = agregado * ceros
		punto_numero = ceros + punto_numero
		numero = str(self.notaDebito.receipt_number)
		largo = len(numero)
		ceros = 8 - largo
		ceros = agregado * ceros
		numero = ceros + numero
		return "{}-{}".format(punto_numero, numero)

	def formatoAfipNCC(self):
		agregado = "0"
		punto_numero = str(self.notaCredito.point_of_sales)
		largo = len(punto_numero)
		ceros = 4 - largo
		ceros = agregado * ceros
		punto_numero = ceros + punto_numero
		numero = str(self.notaCredito.receipt_number)
		largo = len(numero)
		ceros = 8 - largo
		ceros = agregado * ceros
		numero = ceros + numero
		return "{}-{}".format(punto_numero, numero)

	def nombre(self):
		if self.punto:
			nombre = self.formatoAfipRCX()
		else:
			nombre = self.formatoAfipNCC()
		return nombre

	def tipo(self):
		if self.punto:
			tipo = "Recibo X"
		else:
			tipo = "Nota de Credito C"
		return tipo



	def __str__(self):
		return self.nombre()

	def hacer_pdfs(self):
		archivo = []
		enteros = []
		if self.punto:
			comprobante = self
			html_string = render_to_string('comprobantes/pdfs/Recibo.html', locals())
			html = HTML(string=html_string, base_url='https://sportingclubsalta.com/comprobantes/')
			pdfRecibo = html.render()
			enteros.append(pdfRecibo)
			for p in pdfRecibo.pages:
				archivo.append(p)

		if self.nota_credito:
			comprobante = self
			generator = ReceiptBarcodeGenerator(self.nota_credito)
			barcode = base64.b64encode(generator.generate_barcode()).decode("utf-8")
			html_string = render_to_string('comprobantes/pdfs/13.html', locals())
			html = HTML(string=html_string, base_url='https://sportingclubsalta.com/comprobantes/')
			pdfNCC = html.render()
			enteros.append(pdfNCC)
			for p in pdfNCC.pages:
				archivo.append(p)

		if self.nota_debito:
			comprobante = self
			generator = ReceiptBarcodeGenerator(self.nota_debito)
			barcode = base64.b64encode(generator.generate_barcode()).decode("utf-8")
			html_string = render_to_string('comprobantes/pdfs/12.html', locals())
			html = HTML(string=html_string, base_url='https://sportingclubsalta.com/comprobantes/')
			pdfNDC = html.render()
			enteros.append(pdfNDC)
			for p in pdfNDC.pages:
				archivo.append(p)

		if self.nota_credito_anulado:
			comprobante = self
			generator = ReceiptBarcodeGenerator(self.nota_credito_anulado)
			barcode = base64.b64encode(generator.generate_barcode()).decode("utf-8")
			html_string = render_to_string('comprobantes/pdfs/13.html', locals())
			html = HTML(string=html_string, base_url='https://sportingclubsalta.com/comprobantes/')
			pdfNCC = html.render()
			enteros.append(pdfNCC)
			for p in pdfNCC.pages:
				archivo.append(p)

		if self.nota_debito_anulado:
			comprobante = self
			generator = ReceiptBarcodeGenerator(self.nota_debito_anulado)
			barcode = base64.b64encode(generator.generate_barcode()).decode("utf-8")
			html_string = render_to_string('comprobantes/pdfs/12.html', locals())
			html = HTML(string=html_string, base_url='https://sportingclubsalta.com/comprobantes/')
			pdfNDC = html.render()
			enteros.append(pdfNDC)
			for p in pdfNDC.pages:
				archivo.append(p)

		pdf = enteros[0].copy(archivo).write_pdf()
		ruta = "{}_{}_{}.pdf".format(
			self.club.abreviatura,
			self.tipo(),
			self.nombre()
		)
		if self.anulado:
			self.pdf_anulado = SimpleUploadedFile(ruta, pdf, content_type='application/pdf')
		else:
			self.pdf = SimpleUploadedFile(ruta, pdf, content_type='application/pdf')
		self.save()

	def enviar_mail(self):
		if self.club.mails:
			socio = self.socio
			numero = self.nombre()
			valor = self.total
			link_comprobantes = armar_link(reverse('cobranzas-socio'))
			html_string = render_to_string('comprobantes/mail.html', locals())

			if socio.usuario:
				if socio.usuario.email:
					msg = EmailMultiAlternatives(
						subject="Nuevo Comprobante",
						body="",
						from_email=emisor_mail(self.club),
						to=[socio.usuario.email],
					)

					msg.attach_alternative(html_string, "text/html")
					msg.attach_file(self.pdf.path)
					msg.send()

			if socio.email:
				msg = EmailMultiAlternatives(
					subject="Nuevo comprobante",
					body="",
					from_email=emisor_mail(self.club),
					to=[socio.email],
				)
				msg.attach_alternative(html_string, "text/html")
				msg.attach_file(self.pdf.path)
				msg.send()

	def save(self, *args, **kw):
		if self.punto and not self.numero:
			numero_comp = 1
			try:
				ultima = Comprobante.objects.filter(
						club=self.club,
						punto=self.punto,
						).order_by('-numero')[0].numero
			except:
				ultima = 0
			self.numero = ultima + numero_comp
		super().save(*args, **kw)

	def hacer_contabilidad(self):

		""" Envia una lista de listas (Para procesar mas facil en el cron) """

		from contabilidad.models import Cuenta
		operaciones = []

		cajas = self.cajacomprobante_set.filter(valor__gt=0)
		if cajas:
			for c in cajas:
				operaciones.append([c.caja.cuenta_contable, c.valor])


		suma_capitales = 0
		suma_descuentos = 0
		suma_intereses = 0
		suma_intereses_nc = 0
		cobros = self.cobro_set.filter(subtotal__gt=0)
		if cobros:
			for c in cobros:
				if not self.punto: # Si es una "Nota de Credito C"
					operaciones.append([c.credito.ingreso.cuenta_contable, c.capital])
					suma_intereses_nc += c.int_desc
				else:
					suma_intereses += c.int_desc if c.int_desc > 0 else 0
				suma_capitales += c.capital
				suma_descuentos -= c.int_desc if c.int_desc < 0 else 0

		if suma_descuentos:
			operaciones.append([Cuenta.objects.get(numero=511125), suma_descuentos])
		if suma_intereses:
			operaciones.append([Cuenta.objects.get(numero=411103), -suma_intereses])
		if suma_capitales:
			operaciones.append([Cuenta.objects.get(numero=112101), -suma_capitales])


		saldos_utilizados = self.saldos_utilizados.filter(subtotal__lt=0)
		if saldos_utilizados:
			suma_saldos_utilizados = sum([-s.subtotal for s in saldos_utilizados])
			operaciones.append([Cuenta.objects.get(numero=112103), suma_saldos_utilizados])
		saldos_nuevos = self.saldos.filter(subtotal__gt=0, padre__isnull=True)
		if saldos_nuevos:
			suma_saldos_nuevos = sum([s.subtotal for s in saldos_nuevos])
			operaciones.append([Cuenta.objects.get(numero=112103), -suma_saldos_nuevos])

		return operaciones

	def reversar_operaciones(self):

		""" Reversar operaciones cuando se anula un comprobante """

		cajas = self.cajacomprobante_set.all()
		if cajas:
			for c in cajas:
				nueva_caja = c
				nueva_caja.pk = None
				nueva_caja.fecha = date.today()
				nueva_caja.valor = -nueva_caja.valor
				nueva_caja.save()

		cobros = self.cobro_set.all()
		if cobros:
			for c in cobros:
				# Creditos
				padre = c.credito.padre if c.credito.padre else c.credito
				id_padre = c.credito.padre.id if c.credito.padre else c.credito.id
				nuevo_credito = c.credito
				nuevo_credito.pk = None
				nuevo_credito.fecha = date.today()
				nuevo_credito.fin = None
				nuevo_credito.capital = c.capital # arreglamos esto, el credito se tiene que crear con el valor de lo que se cobro
				# No supimos porque estaba poniendo fecha de fin a los hijos del padre
				# hijos = padre.hijos.filter(fin__isnull=True)
				# if hijos:
				# 	for h in hijos:
				# 		h.fin = date.today()
				# 		h.save()
				nuevo_credito.padre_id = id_padre
				nuevo_credito.save()

				# Cobros
				nueva_cobro = c
				nueva_cobro.pk = None
				nueva_cobro.fecha = date.today()
				nueva_cobro.capital = -nueva_cobro.capital
				nueva_cobro.int_desc = -nueva_cobro.int_desc
				nueva_cobro.subtotal = -nueva_cobro.subtotal
				nueva_cobro.save()

		saldos_utilizados = self.saldos_utilizados.all()
		if saldos_utilizados:
			for s in saldos_utilizados:
				nuevo_saldo_utilizado = s
				nuevo_saldo_utilizado.pk = None
				nuevo_saldo_utilizado.fecha = date.today()
				nuevo_saldo_utilizado.subtotal = -nuevo_saldo_utilizado.subtotal
				nuevo_saldo_utilizado.save()

		saldos_nuevos = self.saldos.filter(padre__isnull=True)
		if saldos_nuevos:
			for s in saldos_nuevos:
				id_padre = s.id
				nuevo_saldo_nuevo = s
				nuevo_saldo_nuevo.pk = None
				nuevo_saldo_nuevo.fecha = date.today()
				nuevo_saldo_nuevo.subtotal = -nuevo_saldo_nuevo.subtotal
				nuevo_saldo_nuevo.padre_id = id_padre
				nuevo_saldo_nuevo.save()

	def anular(self):

		""" Anulacion del comprobante """

		from contabilidad.asientos.manager import AsientoCreator

		if not self.anulado:
			self.anulado = date.today()
			if self.nota_credito:
				self.nota_debito_anulado = Receipt(
					point_of_sales=self.nota_credito.point_of_sales,
					receipt_type=ReceiptType.objects.get(code="12"),
					concept=ConceptType.objects.get(code=2),
					document_type=self.socio.tipo_documento,
					document_number=self.socio.numero_documento,
					issued_date=date.today(),
					total_amount=self.nota_credito.total_amount,
					net_untaxed=0,
					net_taxed=self.nota_credito.total_amount,
					exempt_amount=0,
					service_start=date.today(),
					service_end=date.today(),
					expiration_date=date.today(),
					currency=CurrencyType.objects.get(code="PES"),
				)
				self.nota_debito_anulado.save()
				self.nota_debito_anulado.related_receipts.add(self.nota_credito)				
				self.nota_debito_anulado.validate()
			if self.nota_debito:
				self.nota_credito_anulado = Receipt(
					point_of_sales=self.nota_debito.point_of_sales,
					receipt_type=ReceiptType.objects.get(code="13"),
					concept=ConceptType.objects.get(code=2),
					document_type=self.socio.tipo_documento,
					document_number=self.socio.numero_documento,
					issued_date=date.today(),
					total_amount=self.nota_debito.total_amount,
					net_untaxed=0,
					net_taxed=self.nota_debito.total_amount,
					exempt_amount=0,
					service_start=date.today(),
					service_end=date.today(),
					expiration_date=date.today(),
					currency=CurrencyType.objects.get(code="PES"),
				)
				self.nota_credito_anulado.save()
				self.nota_credito_anulado.related_receipts.add(self.nota_debito)	
				self.nota_credito_anulado.validate()

			# Creacion del asiento
			descripcion = "Anulacion {} {}".format(self.tipo(), self.nombre())
			data_asiento = {
				'club': self.club,
				'fecha_asiento': date.today(),
				'descripcion': descripcion
			}
			operaciones = self.hacer_contabilidad()

			cuentas = set([o[0] for o in operaciones]) # Seteamos las cuentas
			data_operaciones = []
			for c in cuentas:
				diccionario = {
					'cuenta': c,
					'descripcion': descripcion
				}
				suma = 0
				for o in operaciones:
					if o[0] == c:
						suma += o[1] # Sumamos las cuentas
				if suma > 0:
					diccionario.update({
							'debe': 0,
							'haber': suma
						})
				else:
					diccionario.update({
							'haber': 0,
							'debe': -suma
						})
				data_operaciones.append(diccionario)
			crear_asiento = AsientoCreator(data_asiento, data_operaciones)
			asiento = crear_asiento.guardar()
			self.asiento_anulado = asiento
			self.hacer_pdfs()
			self.reversar_operaciones()
			self.save()


class Cobro(models.Model):
	club = models.ForeignKey(Club, on_delete=models.CASCADE)
	socio = models.ForeignKey(Socio, blank=True, null=True, on_delete=models.SET_NULL)
	fecha = models.DateField(blank=True, null=True)
	credito = models.ForeignKey(Credito, blank=True, null=True, on_delete=models.CASCADE)
	capital = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
	int_desc = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
	subtotal = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
	comprobante = models.ForeignKey(Comprobante, blank=True, null=True, on_delete=models.SET_NULL)
	preference = models.ForeignKey(Preference, blank=True, null=True, on_delete=models.CASCADE)
	anulacion = models.BooleanField(default=False)

	def __str__(self):
		if self.preference:
			nombre = "{} - {}".format(self.socio, self.preference)
		else:
			nombre = str(self.socio)
		return nombre


	@property
	def nombre(self):

		""" No sabia si __str__ estaba en uso """

		if self.comprobante:
			nombre = "{} - {}. ".format(self.comprobante.tipo(), self.comprobante.nombre())
		else:
			nombre = "Cobro sin recibo"

		if self.subtotal < 0.00:
			nombre += 'ANULACION'
		return nombre


	def movimiento(self, valor):
		""" Naturaleza positiva o negativa """
		if self.comprobante and self.comprobante.receipt.receipt_type.code == "12":
			valor *= -1
		return valor


	@property
	def m_capital(self):
		""" Movimiento de capital (Positivo o negativo) """
		return self.movimiento(self.capital)


class Saldo(models.Model):
	club = models.ForeignKey(Club, on_delete=models.CASCADE)
	socio = models.ForeignKey(Socio, blank=True, null=True, on_delete=models.SET_NULL)
	fecha = models.DateField(blank=True, null=True)
	comprobante_origen = models.ForeignKey(Comprobante, blank=True, null=True, on_delete=models.SET_NULL, related_name='saldos')
	comprobante_destino = models.ForeignKey(Comprobante, blank=True, null=True, on_delete=models.SET_NULL, related_name='saldos_utilizados')
	subtotal = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True) # Para poder homogeneizar se lo llama subtotal
	padre = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='hijos')
	anulacion = models.BooleanField(default=False)

	class Meta:
		ordering = ['fecha']

	@property
	def nombre(self):
		if self.comprobante_origen:
			return "Saldo {} {}".format(self.comprobante_origen.tipo(), self.comprobante_origen.nombre())
		else:
			return "Saldo inicial"



	@property
	def utilizacion(self):
		if self.comprobante_destino:
			return '{}: {}'.format(self.comprobante_destino.tipo(), self.comprobante_destino.nombre())

	def saldo(self, fecha=date.today()):
		sub = self.subtotal
		hijos = self.hijos.filter(fecha__lte=fecha)
		if hijos:
			for utilizacion in hijos:
				sub += utilizacion.subtotal
		return sub


	@property
	def subtotal_invertido(self):
		return -self.subtotal


class CajaComprobante(models.Model):
	club = models.ForeignKey(Club, on_delete=models.CASCADE)
	socio = models.ForeignKey(Socio, blank=True, null=True, on_delete=models.SET_NULL)
	fecha = models.DateField(blank=True, null=True)
	comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE)
	caja = models.ForeignKey(Caja, blank=True, null=True, on_delete=models.CASCADE)
	referencia = models.CharField(max_length=10, blank=True, null=True)
	valor = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
	anulacion = models.BooleanField(default=False)

	def __str__(self):
		return self.caja.nombre

	@property
	def nombre(self):

		""" Retorna el nombre. No utilizo __str__ porque nose donde la estoy mostrando """

		nombre = "{} {}. ".format(self.comprobante.tipo(), self.comprobante.nombre())

		if self.anulacion:
			nombre += 'ANULACION'

		return nombre

	@property
	def registro(self):
		return self.valor, "{} - {}".format(self.comprobante.receipt.receipt_type, self.comprobante.formatoAfip())