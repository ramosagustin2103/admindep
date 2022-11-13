from django.db import transaction
from clubes.models import Club


@transaction.atomic
def eliminar_de_grupo():

	"""
 		Recorre todos los socios y reasigna su categoria (Si la nueva es automatica) 	
		Elimina del grupo a los socios que cumplieron el cambio y la nueva categoria tiene cantidad limite
	"""

	for club in Club.objects.all():
		# Iteracion por socio para reasignar categoria si debe
		for socio in club.socio_set.filter(es_socio=True, baja__isnull=True):
			socio.reasignar_categoria()

		# Eliminacion del grupo
		for grupo in club.grupo_set.all():
			for categoria in club.categorias.filter(cantidad_limite__isnull=False):
				cantidad_a_eliminar = grupo.socios.filter(categoria=categoria).count() - categoria.cantidad_limite
				if cantidad_a_eliminar > 0 :
					socios_a_eliminar = grupo.socios.filter(categoria=categoria).order_by('-fecha_nacimiento')[:cantidad_a_eliminar]  #los cantidad_a_eliminar con menor edad
					for socio in socios_a_eliminar:
						grupo.socios.remove(socio)
			if grupo.socios.filter(baja__isnull=True).count() < 2 :
				grupo.delete()
