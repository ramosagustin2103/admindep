from import_export.resources import ModelResource
from import_export.admin import ImportExportMixin
from django.contrib import admin
from django.contrib import messages
from .models import *
from django.urls import reverse
from admindep.funciones import armar_link


def hacer_asiento(modeladmin, request, queryset):
	for liquidacion in queryset:
		liquidacion.hacer_asiento()
		messages.success(request, "Hecho")

hacer_asiento.short_description = "Hacer asiento de esta liquidacion"


def enviar_mail_factura(modeladmin, request, queryset):
	for factura in queryset:
		factura.enviar_mail()
		messages.success(request, 'Enviado')

enviar_mail_factura.short_description = "Enviar mail de esta factura"

class LiquidacionAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	actions = [hacer_asiento]
admin.site.register(Liquidacion, LiquidacionAdmin)


class FacturaAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	actions = [enviar_mail_factura]

admin.site.register(Factura, FacturaAdmin)


class CreditoResource(ModelResource):

    class Meta:
        model = Credito


class CreditoAdmin(ImportExportMixin, admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	resource_class = CreditoResource

admin.site.register(Credito, CreditoAdmin)
