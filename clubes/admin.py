from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User
from .models import *
from contabilidad.models import *


admin.site.register(Tipo_Ocupante)
admin.site.register(Tipo_CU)
admin.site.register(Codigo_Provincia)


def cargar_plan(modeladmin, request, queryset):
	for club in queryset:
		try:
			plan = Plan.objects.get(club=club)
		except:
			plan = None
		if not plan:
			plan = Plan(
				club=club,
			)
			plan.save()
			plan.cuentas.add(*Cuenta.objects.filter(club__isnull=True))
			messages.add_message(request, messages.SUCCESS, "Plan cargado con exito.")

cargar_plan.short_description = "Cargar plan de cuentas basico"

def agregar_usuarios(modeladmin, request, queryset):
	for club in queryset:
		prefijo = "{}.".format(club.abreviatura)
		club.usuarios.add(*User.objects.filter(username__icontains=prefijo))
		messages.add_message(request, messages.SUCCESS, "Usuarios cargados con exito.")

agregar_usuarios.short_description = "Agregar usuarios con la abreviatura del club"

class ClubAdmin(admin.ModelAdmin):
	actions = [cargar_plan, agregar_usuarios]

admin.site.register(Club, ClubAdmin)
