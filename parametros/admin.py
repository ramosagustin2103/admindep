from import_export.resources import ModelResource
from import_export.admin import ImportExportMixin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from .models import *



class UserResource(ModelResource):
	def after_save_instance(self, instance, using_transactions, dry_run):
		instance.set_password(instance.username)
		instance.save()

	class Meta:
		model = User

def eliminar_de_grupo(modeladmin, request, queryset):
	# Reasignacion de categorias a los socios
	for socio in queryset:
		socio.reasignar_categoria()

	# Eliminacion del grupo
	club = socio.club
	for grupo in club.grupo_set.all():
		for categoria in club.categorias.filter(asignacion_automatica=True, cantidad_limite__isnull=False):
			cantidad_a_eliminar = grupo.socios.filter(categoria=categoria).count() - categoria.cantidad_limite
			if cantidad_a_eliminar > 0 :
				socios_a_eliminar = grupo.socios.filter(categoria=categoria).order_by('-fecha_nacimiento')[:cantidad_a_eliminar]  #los cantidad_a_eliminar con menor edad
				for socio in socios_a_eliminar:
					grupo.socios.remove(socio)
		if grupo.socios.all().count() == 1 :
			socio = grupo.socios.first()
			grupo.socios.remove(socio)
			grupo.delete()
	messages.success(request, "Hecho.")

eliminar_de_grupo.short_description = "PRUEBA GRUPO"

class UserAdmin(ImportExportMixin, UserAdmin):
	resource_class = UserResource

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class SocioResource(ModelResource):

    class Meta:
        model = Socio

    def for_delete(self, row, instance):
        return self.fields['nombre'].clean(row) == ''


def codigo(modeladmin, request, queryset):
	for socio in queryset:
		socio.generar_codigo()

	messages.add_message(request, messages.SUCCESS, "Hecho.")

codigo.short_description = "Generar codigo de creacion a Socio"

class SocioAdmin(ImportExportMixin, admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	ordering = ['-nombre']
	actions = [eliminar_de_grupo, codigo]
	resource_class = SocioResource

admin.site.register(Socio, SocioAdmin)

class CajaAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']

class IngresoAdmin(ImportExportMixin, admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	ordering = ['-nombre']

class GastoAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']

class AcreedorAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']

class GrupoResource(ModelResource):

    class Meta:
        model = Grupo


class GrupoAdmin(ImportExportMixin, admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']
	resource_class = GrupoResource

class CategoriaAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'club']
	list_filter = ['club']

admin.site.register(Acreedor, AcreedorAdmin)
admin.site.register(Caja, CajaAdmin)
admin.site.register(Gasto, GastoAdmin)
admin.site.register(Ingreso, IngresoAdmin)
admin.site.register(Grupo, GrupoAdmin)
admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Relacion)
admin.site.register(Accesorio)


