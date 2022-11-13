from __future__ import unicode_literals
import calendar
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.db import models
from clubes.models import *
from parametros.models import *
from django_afip.models import PointOfSales
from contabilidad.models import *
from django.template.loader import render_to_string
from weasyprint import HTML
from django_afip.models import *
from django_afip.pdf import ReceiptBarcodeGenerator
import base64
from django.core.files.uploadedfile import SimpleUploadedFile
from admindep.funciones import armar_link, emisor_mail
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from contabilidad.asientos.manager import AsientoCreator
exposed_request = None

class Liquidacion(models.Model):
	club = models.ForeignKey(Club, on_delete=models.CASCADE)
	punto = models.ForeignKey(PointOfSales, on_delete=models.CASCADE)
	numero = models.PositiveIntegerField(blank=True, null=True)
	fecha = models.DateField(blank=True, null=True)
	capital = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
	ESTADO_CHOICES = (
		('en_proceso', 'En proceso'),
		('errores', 'Errores'),
		('confirmado', 'Confirmado'),
		)
	estado = models.CharField(max_length=15, choices=ESTADO_CHOICES)
	pdf = models.FileField(upload_to="liquidaciones/pdf/", blank=True, null=True)
	asiento = models.ForeignKey(Asiento, on_delete=models.SET_NULL, blank=True, null=True)
	mails = models.BooleanField(default=False)

	def puntof(self):
		agregado = "0"
		numero = str(self.punto.number)
		largo = len(numero)
		ceros = 4 - largo
		ceros = agregado * ceros
		numero = ceros + numero
		return numero

	def numerof(self):
		agregado = "0"
		numero = str(self.numero)
		largo = len(numero)
		ceros = 8 - largo
		ceros = agregado * ceros
		numero = ceros + numero
		return numero

	def formatoAfip(self):
		data = "%s-%s" % (self.puntof(), self.numerof())
		return data

	def __str__(self):
		nombre = self.formatoAfip()
		return nombre



	@property
	def suma_capitales(self):

		""" Suma los capitales de los creditos """

		return sum([c.capital for c in self.credito_set.filter(padre__isnull=True)])


	@property
	def suma_bonificaciones(self):

		""" Suma las bonificaciones de los creditos """

		return sum([c.bonificacion for c in self.credito_set.filter(padre__isnull=True)])


	@property
	def suma_brutos(self):

		""" Suma las bonificaciones de los creditos """

		return sum([c.bruto for c in self.credito_set.filter(padre__isnull=True)])



	def confirmar(self):

		"""
			Chequea si al finalizar el procesamiento de una liquidacion
			existen facturas no validadas por AFIP
		"""

		errores = self.factura_set.filter(receipt__receipt_number__isnull=True)
		if errores:
			self.estado = "errores"
		else:
			self.estado = "confirmado"
			self.hacer_pdf()
			self.hacer_asiento()
			self.mails = True
		self.save()

	def hacer_pdf(self):
		if not self.pdf:
			liquidacion = self
			html_string_pdf = render_to_string('creditos/pdfs/liquidacion.html', locals())
			html = HTML(string=html_string_pdf, base_url='https://sportingclubsalta.com/liquidaciones/')
			pdf = html.write_pdf()
			ruta = "{}_{}.pdf".format(
					str(self.club.abreviatura),
					str(self.formatoAfip())
				)
			self.pdf = SimpleUploadedFile(ruta, pdf, content_type='application/pdf')
			self.save()


	def hacer_asiento(self):

		""" Crea el asiento de la liquidacion """

		if not self.asiento:
			from contabilidad.asientos.manager import AsientoCreator
			from contabilidad.models import Cuenta
			descripcion = 'Liquidacion {}'.format(self.formatoAfip())
			if self.factura_set.first():
				fecha_asiento = self.factura_set.first().receipt.issued_date
			else:
				fecha_asiento = self.fecha
			data_asiento = {
				'club': self.club,
				'fecha_asiento': fecha_asiento,
				'descripcion': descripcion
			}
			data_operaciones = [
				{
					'cuenta': Cuenta.objects.get(numero=112101),
					'debe': self.suma_brutos,
					'haber': 0,
					'descripcion': descripcion

				}
			]

			creditos = self.credito_set.filter(padre__isnull=True)
			bonificaciones = set([credito.acc_bonif for credito in creditos if credito.acc_bonif])
			if bonificaciones:
				for bonificacion in bonificaciones:
					creditos_bonificacion = creditos.filter(acc_bonif=bonificacion)
					debe = sum([credito.bonificacion for credito in creditos_bonificacion])
					operacion = {
						'cuenta': bonificacion.cuenta_contable,
						'debe': debe,
						'haber': 0,
						'descripcion': descripcion
					}
					data_operaciones.append(operacion)



			ingresos = set([credito.ingreso for credito in creditos])
			for ingreso in ingresos:
				creditos_ingreso = creditos.filter(ingreso=ingreso)
				haber = sum([credito.capital for credito in creditos_ingreso])
				operacion = {
					'cuenta': ingreso.cuenta_contable,
					'debe': 0,
					'haber': haber,
					'descripcion': descripcion
				}
				data_operaciones.append(operacion)


			crear_asiento = AsientoCreator(data_asiento, data_operaciones)
			asiento = crear_asiento.guardar()
			self.asiento = asiento
			self.save()

	@property
	def cobrado(self):

		""" Retorna brutos de cobrados y pendientes """

		creditos = self.credito_set.filter(padre__isnull=True)
		pendientes = 0
		cobrados = 0
		for c in creditos:
			if c.saldo:
				pendientes += c.bruto
			else:
				cobrados += c.bruto

		return cobrados, pendientes


	def save(self, *args, **kw):

		if not self.numero:
			numero_liq = 1
			try:
				ultima = Liquidacion.objects.filter(
						club=self.club,
						punto=self.punto,
						).order_by('-numero')[0].numero
			except:
				ultima = 0
			self.numero = ultima + numero_liq
		super().save(*args, **kw)



class Factura(models.Model):
	club = models.ForeignKey(Club, on_delete=models.CASCADE)
	receipt = models.ForeignKey(Receipt, blank=True, null=True ,on_delete=models.CASCADE)
	liquidacion = models.ForeignKey(Liquidacion, on_delete=models.CASCADE)
	socio = models.ForeignKey(Socio,  blank=True, null=True, on_delete=models.PROTECT)
	pdf = models.FileField(upload_to="facturas/pdf/", blank=True, null=True)
	observacion = models.TextField(blank=True, null=True)

	def __str__(self):
		nombre = 'Socio: {}. '.format(self.socio)
		if self.receipt.receipt_number:
			nombre += self.formatoAfip()
		else:
			nombre += 'No validada'
		return nombre


	def puntof(self):
		agregado = "0"
		numero = str(self.receipt.point_of_sales)
		largo = len(numero)
		ceros = 4 - largo
		ceros = agregado * ceros
		numero = ceros + numero
		return numero

	def numerof(self):
		agregado = "0"
		numero = str(self.receipt.receipt_number)
		largo = len(numero)
		ceros = 8 - largo
		ceros = agregado * ceros
		numero = ceros + numero
		return numero

	def formatoAfip(self):
		data = "%s-%s" % (self.puntof(), self.numerof())
		return data



	
	def incorporar_creditos(self):
		grupo = self.socio.grupo_set.first()
		if grupo:
			creditos = Credito.objects.filter(liquidacion=self.liquidacion, socio__in=grupo.socios.all())
		else:
			creditos = Credito.objects.filter(liquidacion=self.liquidacion, socio=self.socio)
		creditos.update(factura=self)
		return creditos


	def hacer_pdf(self):
		if not self.pdf:
			factura = self
			generator = ReceiptBarcodeGenerator(self.receipt)
			barcode = base64.b64encode(generator.generate_barcode()).decode("utf-8")
			html_string = render_to_string('creditos/pdfs/{}.html'.format(self.receipt.receipt_type.code), locals())
			html = HTML(string=html_string, base_url='https://sportingclubsalta.com/comprobantes/')
			pdf = html.write_pdf()
			ruta = "{}_{}_{}.pdf".format(
					str(self.club.abreviatura),
					str(self.receipt.receipt_type.code),
					str(self.formatoAfip())
				)
			self.pdf = SimpleUploadedFile(ruta, pdf, content_type='application/pdf')
			self.save()

	def validar_factura(self):

		"""
			Valida la factura y hace el PDF
			o le agrega el error de AFIP en observacion
		"""
		error = self.receipt.validate()
		if error:
			self.observacion = error
			self.save()
		else:
			self.hacer_pdf()




	@property
	def suma_capitales(self):

		""" Suma los capitales de los creditos """

		return sum([c.capital for c in self.credito_set.filter(padre__isnull=True)])


	@property
	def suma_bonificaciones(self):

		""" Suma las bonificaciones de los creditos """

		return sum([c.bonificacion for c in self.credito_set.filter(padre__isnull=True)])


	def enviar_mail(self):
		if self.receipt.is_validated and self.club.mails:
			socio = self.socio
			numero = self.formatoAfip()
			valor = self.receipt.total_amount
			link_facturacion = armar_link(reverse('facturacion-socio'))
			html_string = render_to_string('creditos/mail.html', locals())

			if socio.usuario:
				if socio.usuario.email:
					msg = EmailMultiAlternatives(
						subject="Nuevo factura",
						body="",
						from_email=emisor_mail(self.club),
						to=[socio.usuario.email],
					)
					msg.attach_alternative(html_string, "text/html")
					msg.attach_file(self.pdf.path)
					msg.send()

			if socio.email:
				msg = EmailMultiAlternatives(
					subject="Nuevo factura",
					body="",
					from_email=emisor_mail(self.club),
					to=[socio.email],
				)
				msg.attach_alternative(html_string, "text/html")
				msg.attach_file(self.pdf.path)
				msg.send()


	def descuentos(self):

		""" Retorna una lista de strings """

		accesorios = []
		for credito in self.credito_set.all():
			if credito.acc_desc:
				leyenda = "Descuento por pronto pago de {} hasta la fecha {} ".format(credito.ingreso, credito.gracia)
				if credito.acc_desc.tipo == "tasa":
					leyenda += "del {}%.".format(credito.acc_desc.monto)
				elif credito.acc_desc.tipo == "fijo":
					leyenda += "de ${}.".format(credito.acc_desc.monto)
				accesorios.append(leyenda)

		return set(accesorios)


	def detalles(self):

		""" Retorna una lista de strings """

		detalles = []
		for credito in self.credito_set.all():
			if credito.detalle_limpio:
				detalles.append(credito.detalle_limpio)
		
		return detalles


class Credito(models.Model):
	club = models.ForeignKey(Club, on_delete=models.CASCADE)
	liquidacion = models.ForeignKey(Liquidacion, blank=True, null=True, on_delete=models.CASCADE)
	factura = models.ForeignKey(Factura, blank=True, null=True, on_delete=models.CASCADE)
	fecha = models.DateField(blank=True, null=True)
	periodo = models.DateField(blank=True, null=True)
	ingreso = models.ForeignKey(Ingreso, blank=True, null=True, on_delete=models.CASCADE)
	socio = models.ForeignKey(Socio, blank=True, null=True, on_delete=models.CASCADE)
	acc_int = models.ForeignKey(Accesorio, blank=True, null=True, on_delete=models.PROTECT, related_name='acc_int')
	acc_desc = models.ForeignKey(Accesorio, blank=True, null=True, on_delete=models.PROTECT, related_name='acc_desc')
	acc_bonif = models.ForeignKey(Accesorio, blank=True, null=True, on_delete=models.PROTECT, related_name='acc_bonif')
	vencimiento = models.DateField(blank=True, null=True)
	gracia = models.DateField(blank=True, null=True)
	capital = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
	padre = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='hijos')
	detalle = models.CharField(max_length=30, blank=True, null=True)
	fin = models.DateField(blank=True, null=True)

	@property
	def nombre(self):

		""" Retorna el nombre. No utilizo __str__ porque nose donde la estoy mostrando """

		nombre = "Liquidacion {}.".format(self.liquidacion)
		if self.factura:
			nombre += "Factura C {}.".format(self.factura.formatoAfip())
		return nombre


	def calcular_accesorio(self, accesorio, fecha_operacion=None):

		""" Realiza el calculo de algun accesorio """
		calculo = 0

		if accesorio:
			if accesorio.tipo == "fijo":
				calculo = round(accesorio.monto, 2)
			else:
				if accesorio.clase == "bonificacion":
					calculo = round(self.capital * accesorio.monto / 100, 2)
				elif accesorio.clase == "descuento":
					calculo = round(self.bruto * accesorio.monto / 100, 2)
				elif accesorio.clase == "interes":
					bruto = self.bruto
					tasa = accesorio.monto
					reconocimiento = accesorio.reconocimiento
					base_calculo = accesorio.base_calculo
					periodos = ((fecha_operacion - self.vencimiento).days // reconocimiento)
					if not reconocimiento == 1: # por si se elije un reconocimiento distinto de 1, para agararse el interes aun no generado
						periodos += 1
					calculo = round((bruto*tasa*periodos)/(100*base_calculo//reconocimiento), 2)
		return calculo

	@property
	def bonificacion(self):
		return self.calcular_accesorio(self.acc_bonif)

	@property
	def bruto(self):
		return self.capital - self.bonificacion

	@property
	def ultimo_hijo(self):
		if self.hijos.all():
			return self.hijos.last()
		return		
	
	@property
	def actual(self):
		if self.ultimo_hijo:
			return self.ultimo_hijo
		return self

	@property
	def saldo(self, fecha_operacion=date.today(), condonacion=False):
		if self.ultimo_hijo:
			return self.ultimo_hijo.saldo
		else:
			if self.fin:
				return 0.00
			else:
				return self.subtotal(fecha_operacion=fecha_operacion, condonacion=condonacion)

	@property
	def saldo_socio(self):

		""" Devuelve el saldo del socio sumado el descuento, porque tenia deudas anteriores y no pago """

		if self.ultimo_hijo:
			return self.ultimo_hijo.saldo + self.descuento()
		else:
			if self.fin:
				return 0.00
			else:
				return self.subtotal() + self.descuento()

	@property
	def prioritario(self):
		return self.ingreso.prioritario



	def intereses(self, fecha_operacion=date.today()):
		intereses = 0
		# Si existe accesorio de interes
		if self.acc_int:
			if self.vencimiento < fecha_operacion:
				intereses = self.calcular_accesorio(self.acc_int, fecha_operacion)

		return Decimal("%.2f" % intereses)

	def descuento(self, fecha_operacion=date.today()):
		descuento = 0
		# Si existe accesorio de descuento
		if self.acc_desc:
			## Si el credito todavia no llego a la fecha del fin de la gracia
			if self.gracia > fecha_operacion or self.gracia == fecha_operacion:

				descuento = self.calcular_accesorio(self.acc_desc, fecha_operacion)

		return Decimal("%.2f" % descuento)

	def int_desc(self, fecha_operacion=date.today(), condonacion=False):
		valor = - self.descuento(fecha_operacion=fecha_operacion)
		if not condonacion:
			valor += self.intereses(fecha_operacion=fecha_operacion)
		return valor

	def subtotal(self, fecha_operacion=date.today(), condonacion=False):
		valor = self.bruto - self.descuento(fecha_operacion=fecha_operacion)
		if not condonacion:
			valor += self.intereses(fecha_operacion=fecha_operacion)
		return valor
	
	def detalle_acc(self, fecha_operacion=date.today(), condonacion=False):
		texto = ""
		if self.descuento(fecha_operacion=fecha_operacion):
			texto = "Descuento por pronto pago. Hasta el dia {}".format(self.gracia)
		elif self.intereses(fecha_operacion=fecha_operacion) and not condonacion:
			texto = "Intereses generados desde el dia {}".format(self.vencimiento)
		return texto

	@property
	def detalle_limpio(self):
		if self.detalle in ['cat', 'soc', 'gru'] or not self.detalle:
			return
		leyenda = "{}. {}. {}-{}: {}".format(self.socio, self.ingreso, self.periodo.year, self.periodo.month, self.detalle)

		return leyenda

	def __str__(self):
		nombre = '{} - {}'.format(self.periodo, self.ingreso)
		return nombre
