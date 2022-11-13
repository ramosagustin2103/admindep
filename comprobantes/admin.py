from django.urls import reverse
from datetime import date
from django.contrib import admin
from django.contrib import messages
from django.urls import reverse
from import_export.resources import ModelResource
from import_export.admin import ImportExportMixin

from .models import *
from admindep.funciones import armar_link
from .funciones import asiento_diario

def hacer_pdf(modeladmin, request, queryset):
	for comprobante in queryset:
		comprobante.hacer_pdfs()
		messages.add_message(request, messages.SUCCESS, "Hecho.")
hacer_pdf.short_description = "Hacer PDF"

def reenviar_mail(modeladmin, request, queryset):
	for comprobante in queryset:
		comprobante.enviar_mail()
		messages.add_message(request, messages.SUCCESS, "Mail enviado con exito.")
reenviar_mail.short_description = "Enviar mail de este comprobante"

def hacer_asiento_diario(modeladmin, request, queryset):
	if len(queryset) > 1:
		messages.error(request, 'Debe seleccionar un solo comprobante.')
	else:
		comprobante = queryset.first()
		dia = comprobante.fecha
		hoy = date.today()
		if dia == hoy:
			messages.error(request, 'El comprobante seleccionado es de hoy.')
		else:
			club = comprobante.club
			comprobantes_dia_con_asiento = Comprobante.objects.filter(club=club, fecha=dia, asiento__isnull=False)
			asiento = Asiento.objects.filter(
				comprobante__in=comprobantes_dia_con_asiento
			).distinct().first()
			comprobantes_dia = Comprobante.objects.filter(club=club, fecha=dia)
			if asiento:
				if len(asiento.comprobante_set.all()) != len(comprobantes_dia):
					asiento.delete()
					asiento_diario(dia, club, comprobantes_dia)
					messages.success(request, 'Asiento RECREADO con exito.')
				else:
					messages.error(request, 'Todos los comprobantes de ese dia ya tenian asiento.')
			else:
				asiento_diario(dia, club, comprobantes_dia)
				messages.success(request, 'Asiento CREADO con exito.')


hacer_asiento_diario.short_description = "Hacer asiento diario"



class CobroInline(admin.TabularInline):
	model = Cobro

class CajaComprobanteInline(admin.TabularInline):
	model = CajaComprobante

class SaldosUtilizadosInlineComprobante(admin.TabularInline):
	model = Saldo
	fk_name = 'comprobante_destino'

class SaldosUtilizadosInlineCompensacion(admin.TabularInline):
	model = Saldo
	fk_name = 'compensacion_destino'

class SaldoNuevoInline(admin.TabularInline):
	model = Saldo
	fk_name = 'comprobante_origen'


class ComprobanteAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	actions = [
		reenviar_mail,
		hacer_asiento_diario,
	]
	inlines = [
		CobroInline,
		CajaComprobanteInline,
		SaldosUtilizadosInlineComprobante,
		SaldoNuevoInline
	]


admin.site.register(Comprobante, ComprobanteAdmin)
admin.site.register(Cobro)


class SaldoResource(ModelResource):

    class Meta:
        model = Saldo


class SaldoAdmin(ImportExportMixin, admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	resource_class = SaldoResource



admin.site.register(Saldo, SaldoAdmin)
