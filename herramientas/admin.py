from django.contrib import admin
from import_export.resources import ModelResource
from import_export.admin import ImportExportMixin
from django.contrib import messages

from .models import *

class BienvenidaResource(ModelResource):

    class Meta:
        model = Bienvenida

def enviar_bienvenida(modeladmin, request, queryset):
	for bienvenida in queryset:
		bienvenida.enviar()

	messages.add_message(request, messages.SUCCESS, "Enviado con exito.")

enviar_bienvenida.short_description = "Enviar mail de bienvenida"

class BienvenidaAdmin(ImportExportMixin, admin.ModelAdmin):
	list_display = ['__str__']
	actions = [enviar_bienvenida]
	resource_class = BienvenidaResource

admin.site.register(Bienvenida, BienvenidaAdmin)
