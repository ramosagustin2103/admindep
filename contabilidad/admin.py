from django.contrib import admin
from .models import *

class AsientoAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']


admin.site.register(Asiento, AsientoAdmin)

admin.site.register(Cuenta)
admin.site.register(Plan)
admin.site.register(Ejercicio)