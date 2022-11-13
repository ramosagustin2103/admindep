from django.contrib import admin
from .models import *

class GastoDeudaInline(admin.TabularInline):
	model = GastoDeuda


class DeudaAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	inlines = [GastoDeudaInline]

class GastoOPInline(admin.TabularInline):
	model = GastoOP

class DeudaOPInline(admin.TabularInline):
	model = DeudaOP

class RetencionOPInline(admin.TabularInline):
	model = RetencionOP

class CajaOPInline(admin.TabularInline):
	model = CajaOP

class OPAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	inlines = [
		GastoOPInline,
		DeudaOPInline,
		RetencionOPInline,
		CajaOPInline,
	]

admin.site.register(Deuda, DeudaAdmin)
admin.site.register(OP, OPAdmin)