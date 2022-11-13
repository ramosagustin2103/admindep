
from clubes.models import Club
from django.db import transaction
from .models import Liquidacion


def procesar_liquidaciones():
	"""
		Procesamiento de liquidaciones .
		Le incorpora a los creditos sus accesorios.
		Envia la informacion a AFIP.
		Una vez terminado el recorrido por las facturas de la liquidacion, cambia su estado por "confimado" o "errores"
	"""

	for club in Club.objects.all():
		for liquidacion in club.liquidacion_set.filter(estado='en_proceso'):
			for factura in liquidacion.factura_set.filter(receipt__receipt_number__isnull=True):
				creditos = factura.incorporar_creditos()

				factura.validar_factura()

			liquidacion.confirmar()


def enviar_mails_facturas():

	""" Envia los mails de las liquidaciones donde mails=True """

	for liquidacion in Liquidacion.objects.filter(mails=True):
		for factura in liquidacion.factura_set.all():
			factura.enviar_mail()
		liquidacion.mails = False
		liquidacion.save()