from django.urls import path
from .views import *

urlpatterns = [
	# Indexs
	path('', Index.as_view(), name='cobranzas'),
	path('socio/', IndexSocio.as_view(), name='cobranzas-socio'), # Index para Socio

	# Creaciones
	path('RCX/', RCXWizard.as_view(), name='nuevo-rcx'),
	path('RCX/<int:pk>', RCXFacturaWizard.as_view(), name='nuevo-rcx-factura'), # pk de la factura a cobrar
	path('RCX/MP/', RCXMPWizard.as_view(), name='nuevo-rcxmp'),
	path('NCC/', NCCWizard.as_view(), name='nuevo-ncc'),

	# Registros
	path('registro/', Registro.as_view(), name='registro'),

	# Vistas particulares
	path('pdf/<int:pk>/', PDF.as_view(), name='pdf-comprobante'),
	path('ver/<int:pk>/', Ver.as_view(), name='ver-comprobante'),
	path('anular/<int:pk>/', Anular.as_view(), name='anular-comprobante'),


]
