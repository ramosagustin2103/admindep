from django.urls import path
from .views import *

urlpatterns = [
	path('clubes', cons_index, name='clubes'),
	path('clubes/registro/', cons_registro, name='cons_registro'),
	path('clubes/set/', cons_nuevo_1, name='cons_nuevo'),
	path('clubes/set/<int:cont>/', cons_nuevo_1, name='cons_set'),
	path('clubes/set2/<int:contribuyente>/', cons_nuevo_2, name='cons_nuevo_2'),
	path('clubes/set3/<int:cons>/', cons_nuevo_3, name='cons_nuevo_3'),
	path('usuarios', us_index, name='usuarios'),
	path('usuarios/registro/', us_registro, name='us_registro'),
	path('usuarios/nuevo/', us_nuevo, name='us_nuevo'),
]
