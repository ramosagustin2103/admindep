from django.db import transaction
from clubes.models import Club
from datetime import date
from .models import *
from .funciones import asiento_diario

@transaction.atomic
def hacer_asiento():

	""" Realizacion de asiento diario de comprobantes """

	hoy = date.today()
	for club in Club.objects.all():
		comprobantes = club.comprobante_set.filter(asiento__isnull=True, fecha=hoy)
		asiento_diario(hoy, club, comprobantes)
