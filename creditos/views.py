from django.shortcuts import render, redirect
from datetime import timedelta
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Count, Sum
from django.utils.decorators import method_decorator
from formtools.wizard.views import SessionWizardView
from functools import partial, wraps
from django.views import generic

from admindep.funciones import *
from clubes.models import *
from parametros.models import *
from parametros.forms import *
from .models import *
from .forms import *
from contabilidad.asientos.funciones import asiento_liq
from .manager import *
from .filters import*
from comprobantes.funciones import *
from admindep.generic import *
from reportes.models import Cierre

envioAFIP = 'Liquidacion generada. En los proximos minutos la informacion se enviara a AFIP, te informaremos los resultados.'

@method_decorator(group_required('administrativo', 'contable'), name='dispatch')
class Index(OrderQS):

	""" Index de liquidaciones y creditos """
	model = Liquidacion
	filterset_class = LiquidacionFilter
	template_name = 'creditos/index.html'
	paginate_by = 10


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		# Saldo total de creditos pendientes
		saldo = Credito.objects.filter(club=club(self.request), fin__isnull=True, liquidacion__estado="confirmado").aggregate(saldo=Sum('capital'))['saldo']
		# Ultimo periodo
		ultima_liquidacion = Liquidacion.objects.filter(club=club(self.request), estado='confirmado').order_by('-id').first()
		context.update(locals())
		return context
	

@method_decorator(group_required('socio'), name='dispatch')
class IndexSocio(OrderQS):

	model = Credito
	template_name = 'creditos/socio/index.html'
	filterset_class = CreditoFilterSocio
	paginate_by = 50

	def get_queryset(self):
		socio = self.request.user.socio_set.first()
		grupo = socio.grupo_set.first()
		if grupo:
			socios = grupo.socios.all()
		else:
			socios = [socio]
		return super().get_queryset(
		padre__isnull=True,
		liquidacion__estado='confirmado',		
		socio__in=socios,
		)
		
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['bloqueo'] = bloqueador(self.get_queryset())
		context['bloqueo_descuento'] = bloqueador_descuentos(self.get_queryset())
		context['hoy'] = date.today()

		return context

class WizardLiquidacionManager:
	"""administrador de liquidaciones"""


	TEMPLATES = {
		"inicial": "creditos/nuevo/inicial.html",
		"individuales": "creditos/nuevo/individuales.html",
		"masivo": "creditos/nuevo/masivo.html",
		"grupo": "creditos/nuevo/masivo.html",
		"plazos": "creditos/nuevo/plazos.html",
		"confirmacion": "creditos/nuevo/confirmacion.html",
		"preconceptos": "creditos/nuevo/preconceptos.html",
		"conceptos": "creditos/nuevo/conceptos.html",
	}
	def obtener_accesorios(self, ingresos):
		fecha_operacion = self.get_cleaned_data_for_step('inicial')['fecha_operacion']
		accesorios = Accesorio.objects.filter(ingreso__in=ingresos, finalizacion__isnull=True, plazo__isnull=False).distinct()
		for a in accesorios:
			a.fecha = fecha_operacion + timedelta(days=a.plazo)
		return accesorios

	
	def hacer_creditos(self, tipo):

		"""
		Crea lista de DICCIONARIOS de creditos. No lista de objetos
		Para poder utilizar mejor en manager.py
		"""

		data_inicial = self.get_cleaned_data_for_step('inicial')
		data_creditos = self.get_cleaned_data_for_step(tipo)
		data_plazos = self.get_cleaned_data_for_step('plazos')
		creditos = []

		if tipo == "individuales":
			for d in data_creditos:
				if d:
					if d['subtotal']:
						credito = {
							'club':club(self.request),
							'periodo':data_inicial['fecha_operacion'],
							'ingreso':d['ingreso'],
							'capital':d['subtotal'],
							'detalle' : d['detalle'],
						}
						# Establecer o cliente o dominio
						socio = Socio.objects.get(pk=d['destinatario'])
						credito['socio'] = socio
						credito['cabeza'] = socio.cabeza
						creditos.append(credito)

		elif tipo == "grupo":
			grupos = Grupo.objects.filter(id__in=data_inicial['grupos'])
			socios_de_los_grupos = Socio.objects.filter(id__in=[s.id for g in grupos for s in g.socios.filter(baja__isnull=True)]) 
			for d in data_creditos:
				if d:
					if d['subtotal']:
						base_credito = {
							'club':club(self.request),
							'periodo':data_inicial['fecha_operacion'],
							'ingreso':d['ingreso'],
						}
						criterio = d['criterio']
						if 'categoria' in criterio:
							categoria = Categoria.objects.get(id=criterio.split('categoria-')[1])
							socios_de_la_categoria = categoria.socios.filter(baja__isnull=True)
							for socio in socios_de_la_categoria:
								if socio in socios_de_los_grupos:
									credito = base_credito.copy()
									credito['detalle'] = 'cat'
									credito['socio'] = socio
									credito['capital'] = round(d['subtotal'],2)
									credito['cabeza'] = socio.cabeza
									creditos.append(credito)

						elif criterio == 'socios':
							for socio in socios_de_los_grupos:
								credito = base_credito.copy()
								credito['detalle'] = 'soc'
								credito['socio'] = socio
								credito['capital'] = round(d['subtotal'],2)								
								credito['cabeza'] = socio.cabeza
								creditos.append(credito)
						elif criterio == 'grupos':
							for grupo in grupos:
								credito = base_credito.copy()
								credito['detalle'] = 'gru'
								credito['socio'] = grupo.cabeza
								credito['capital'] = round(d['subtotal'],2)								
								credito['cabeza'] = grupo.cabeza
								creditos.append(credito)									

		elif tipo == "masivo":
			for d in data_creditos:
				if d:
					if d['subtotal']:
						base_credito = {
							'club':club(self.request),
							'periodo':data_inicial['fecha_operacion'],
							'ingreso':d['ingreso'],
						}
						criterio = d['criterio']
						if 'categoria' in criterio:
							categoria = Categoria.objects.get(id=criterio.split('categoria-')[1])
							socios_de_la_categoria = categoria.socios.filter(baja__isnull=True)
							for socio in socios_de_la_categoria:
								credito = base_credito.copy()
								credito['detalle'] = 'cat'
								credito['socio'] = socio
								credito['capital'] = round(d['subtotal'],2)
								credito['cabeza'] = socio.cabeza
								creditos.append(credito)
						elif criterio == 'socios':
							for socio in club(self.request).socio_set.filter(baja__isnull=True, es_socio=True):
								credito = base_credito.copy()
								credito['detalle'] = 'soc'
								credito['socio'] = socio
								credito['capital'] = round(d['subtotal'],2)								
								credito['cabeza'] = socio.cabeza
								creditos.append(credito)
						elif criterio == 'grupos':
							for grupo in club(self.request).grupo_set.filter(baja__isnull=True):
								credito = base_credito.copy()
								credito['detalle'] = 'gru'
								credito['socio'] = grupo.cabeza
								credito['capital'] = round(d['subtotal'],2)								
								credito['cabeza'] = grupo.cabeza
								creditos.append(credito)

		return creditos

	def hacer_plazos(self):

		""" Retorna una lista de diccionarios LIMPIO con "accesorio" y "plazo" """

		data_plazos = self.get_cleaned_data_for_step('plazos')
		plazos = []
		for d in data_plazos:
			if d:
				data = {
					'accesorio': Accesorio.objects.get(pk=d['accesorio']),
					'plazo': d['plazo']
				}
				plazos.append(data)
		return plazos


	def hacer_preconceptos(self):

		""" Retorna un QUERYSET con OBJETOS de tipo Credito """

		return Credito.objects.filter(id__in=self.get_cleaned_data_for_step('preconceptos')['conceptos'])


	def hacer_liquidacion(self, tipo):
		data_inicial = self.get_cleaned_data_for_step('inicial')
		data_creditos = self.hacer_creditos(tipo)
		preconceptos = None if tipo != "masivo" else self.hacer_preconceptos()
		data_plazos = self.hacer_plazos()
		liquidacion= LiquidacionCreator(
				data_inicial=data_inicial, 
				data_creditos=data_creditos, 
				data_plazos=data_plazos, 
				preconceptos=preconceptos
			)
		return liquidacion


@method_decorator(group_required('administrativo'), name='dispatch')
class IndividualesWizard(WizardLiquidacionManager, SessionWizardView):

	form_list = [
		('inicial', InicialForm),
		('individuales', IndividualesForm),
		('plazos', PlazoFormSet),
		('confirmacion', ConfirmacionForm),
	]

	def get_template_names(self):
		return [self.TEMPLATES[self.steps.current]]


	def get_context_data(self, form, **kwargs):
		context = super().get_context_data(form=form, **kwargs)
		tipo = "Individuales"
		if self.steps.current == 'plazos':
			data_individuales = self.get_cleaned_data_for_step('individuales')
			ingresos = set([data['ingreso'] for data in data_individuales if data])
			accesorios = self.obtener_accesorios(ingresos)

		elif self.steps.current == 'confirmacion':
			data_plazos = self.hacer_plazos()
			liquidacion = self.hacer_liquidacion('individuales')

		context.update(locals())

		return context

	def get_form_kwargs(self, step):
		kwargs = super().get_form_kwargs()
		if step in ["inicial", "individuales"]:
			kwargs.update({
					'club': club(self.request)
				})
		if step == "confirmacion":
			liquidacion = self.hacer_liquidacion('individuales')
			mostrar = len(liquidacion.listar_documentos()) == 1
			kwargs.update({
					'mostrar': mostrar
				})
		return kwargs


	def get_form(self, step=None, data=None, files=None):
		form = super().get_form(step, data, files)
		formset = False
		if data:
			if 'individuales' in data['individuales_wizard-current_step']:
				formset = True
		if step == "individuales":
			formset = True

		if formset:
			formset = formset_factory(wraps(IndividualesForm)(partial(IndividualesForm, club=club(self.request))), extra=1)
			form = formset(prefix='individuales', data=data)
		return form

	@transaction.atomic
	def done(self, form_list, **kwargs):
		liquidacion = self.hacer_liquidacion('individuales')
		liquidacion = liquidacion.guardar()
		contado = self.get_cleaned_data_for_step('confirmacion')['confirmacion']
		if contado:
			factura = liquidacion.factura_set.first()
			creditos = factura.incorporar_creditos()
			factura.validar_factura()

			liquidacion.confirmar()
			if liquidacion.estado == "confirmado":
				return redirect('nuevo-rcx-factura', pk=factura.pk)
			else:
				messages.error(self.request, factura.observacion)
		else:
			messages.success(self.request, envioAFIP)
		return redirect('facturacion')


@method_decorator(group_required('administrativo'), name='dispatch')
class MasivoWizard(WizardLiquidacionManager, SessionWizardView):

	form_list = [
		('inicial', InicialForm),
		('masivo', MasivoFormSet),
		('plazos', PlazoFormSet),
		('preconceptos', PreConceptoForm),
		('confirmacion', ConfirmacionForm),
	]

	def get_template_names(self):
		return [self.TEMPLATES[self.steps.current]]

	def get_context_data(self, form, **kwargs):
		context = super().get_context_data(form=form, **kwargs)
		tipo = 'Masivo'
		data_masivo = self.get_cleaned_data_for_step('masivo')
		if data_masivo:
			ingresos = set([data['ingreso'] for data in data_masivo if data])
			accesorios = self.obtener_accesorios(ingresos)


		if self.steps.current == 'confirmacion':
			data_preconceptos = self.hacer_preconceptos()
			liquidacion = self.hacer_liquidacion('masivo')
			data_plazos = self.hacer_plazos()


		context.update(locals())

		return context


	def get_form_kwargs(self, step):
		kwargs = super().get_form_kwargs()
		if step in ["inicial", "preconceptos"]:
			kwargs.update({
					'club': club(self.request)
				})
		return kwargs

	def get_form(self, step=None, data=None, files=None):
		form = super().get_form(step, data, files)
		formset = False
		if data:
			if 'masivo' in data['masivo_wizard-current_step']:
				formset = True
		if step == "masivo":
			formset = True

		if formset:
			formset = formset_factory(wraps(MasivoForm)(partial(MasivoForm, club=club(self.request))), extra=1)
			form = formset(prefix='masivo', data=data)
		return form

	@transaction.atomic
	def done(self, form_list, **kwargs):
		liquidacion = self.hacer_liquidacion('masivo')
		liquidacion = liquidacion.guardar()
		messages.success(self.request, envioAFIP)
		return redirect('facturacion')




@method_decorator(group_required('administrativo'), name='dispatch')
class GrupoWizard(WizardLiquidacionManager, SessionWizardView):

	form_list = [
		('inicial', InicialForm),
		('grupo', MasivoFormSet),
		('plazos', PlazoFormSet),
		('confirmacion', ConfirmacionForm),
	]

	def get_template_names(self):
		return [self.TEMPLATES[self.steps.current]]

	def get_context_data(self, form, **kwargs):
		context = super().get_context_data(form=form, **kwargs)
		tipo = 'Por Grupos'
		data_grupo = self.get_cleaned_data_for_step('grupo')
		if data_grupo:
			ingresos = set([data['ingreso'] for data in data_grupo if data])
			accesorios = self.obtener_accesorios(ingresos)

		if self.steps.current == 'confirmacion':
			liquidacion = self.hacer_liquidacion('grupo')
			data_plazos = self.hacer_plazos()

		context.update(locals())

		return context


	def get_form_kwargs(self, step):
		kwargs = super().get_form_kwargs()
		if step == "inicial":
			kwargs.update({
					'club': club(self.request),
					'ok_grupos': True
				})
		return kwargs

	def get_form(self, step=None, data=None, files=None):
		form = super().get_form(step, data, files)
		formset = False
		if data:
			if 'grupo' in data['grupo_wizard-current_step']:
				formset = True
		if step == "grupo":
			formset = True

		if formset:
			formset = formset_factory(wraps(MasivoForm)(partial(MasivoForm, club=club(self.request))), extra=1)
			form = formset(prefix='grupo', data=data)
		return form

	@transaction.atomic
	def done(self, form_list, **kwargs):
		liquidacion = self.hacer_liquidacion('grupo')
		liquidacion = liquidacion.guardar()
		messages.success(self.request, envioAFIP)
		return redirect('facturacion')



@method_decorator(group_required('administrativo', 'contable'), name='dispatch')
class RegistroLiquidaciones(OrderQS):

	"""Registro de liquidaciones"""
	model = Liquidacion
	filterset_class = LiquidacionFilter
	template_name = 'creditos/registros/liquidaciones.html'
	paginate_by = 50


@method_decorator(group_required('administrativo', 'contable'), name='dispatch')
class RegistroCreditos(OrderQS):
	
	"""Registro de creditos"""
	model = Credito
	filterset_class = CreditoFilter
	template_name = 'creditos/registros/creditos.html'
	paginate_by = 50

	def get_queryset(self):
		return super().get_queryset(padre__isnull=True, liquidacion__estado='confirmado')


class HeaderExeptMixin:
	
	def dispatch(self, request, *args, **kwargs):
		try:
			objeto = self.model.objects.get(club=club(self.request), pk=kwargs['pk'])
		except:
			messages.error(request, 'No se pudo encontrar.')
			return redirect('facturacion')

		return super().dispatch(request, *args, **kwargs)



@method_decorator(group_required('administrativo', 'contable'), name='dispatch')
class Ver(HeaderExeptMixin, generic.DetailView):

	""" Ver una liquidacion """

	model = Liquidacion
	template_name = 'creditos/ver/liquidacion.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		liquidacion = self.get_object()
		creditos = liquidacion.credito_set.filter(liquidacion=liquidacion, padre__isnull=True)
		context.update(locals())
		return context

	def dispatch(self, request, *args, **kwargs):
		sup = super().dispatch(request, *args, **kwargs)
		if sup.status_code == 200 and self.get_object().estado in ["errores", "en_proceso"]:
			messages.error(request, 'No se pudo encontrar.')
			return redirect('facturacion')
		return sup



@method_decorator(group_required('administrativo', 'contable'), name='dispatch')
class VerErrores(HeaderExeptMixin, generic.DeleteView):


	model = Liquidacion
	template_name = 'creditos/ver/liquidacion-errores.html'
	success_url = '/facturacion/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		liquidacion = self.get_object()
		facturas_invalidas = liquidacion.factura_set.filter(receipt__receipt_number__isnull=True)
		context.update(locals())
		return context

	def delete(self, request, *args, **kwargs):
		liquidacion = self.get_object()
		liquidacion.estado = 'en_proceso'
		liquidacion.save()
		messages.success(self.request, envioAFIP)
		return HttpResponseRedirect(self.success_url)

	def dispatch(self, request, *args, **kwargs):
		sup = super().dispatch(request, *args, **kwargs)
		if sup.status_code == 200 and self.get_object().estado in ["confirmado", "en_proceso"]:
			messages.error(request, 'No se pudo encontrar.')
			return redirect('facturacion')
		return sup




@method_decorator(group_required('administrativo', 'contable'), name='dispatch')
class PDFLiquidacion(HeaderExeptMixin, generic.DetailView):
	
	model = Liquidacion
	template_name = 'credito/ver/liquidacion.html'

	def get(self, request, *args, **kwargs):
		liquidacion = self.get_object()	
		response = HttpResponse(liquidacion.pdf, content_type='application/pdf')
		nombre = "Liquidacion_%s.pdf" % (liquidacion.formatoAfip())
		content = "inline; filename='%s'" % nombre
		response['Content-Disposition'] = content
		return response


	def dispatch(self, request, *args, **kwargs):
		sup = super().dispatch(request, *args, **kwargs)
		if sup.status_code == 200 and self.get_object().estado in ["errores", "en_proceso"]:
			messages.error(request, 'No se pudo encontrar.')
			return redirect('facturacion')
		return sup


@method_decorator(group_required('administrativo', 'contable'), name='dispatch')
class PDFFactura(HeaderExeptMixin, generic.DetailView):
	
	model = Factura
	template_name = 'credito/ver/liquidacion.html'

	def get(self, request, *args, **kwargs):
		factura = self.get_object()	
		response = HttpResponse(factura.pdf, content_type='application/pdf')
		nombre = "{}_{}.pdf".format(
			factura.receipt.receipt_type.code,
			factura.formatoAfip(),
		)
		content = "inline; filename='%s'" % nombre
		response['Content-Disposition'] = content
		return response


	def dispatch(self, request, *args, **kwargs):
		sup = super().dispatch(request, *args, **kwargs)
		if sup.status_code == 200:
			if request.user.groups.first().name == "socio" and self.get_object().socio != request.user.socio_set.first():
				messages.error(request, 'No se pudo encontrar.')
				return redirect('facturacion')
		return sup



@method_decorator(group_required('administrativo', 'contable'), name='dispatch')
class IndexConceptos(generic.ListView):

	""" Index y registro de conceptos """

	model = Credito
	filterset_class = CreditoFilter
	template_name = "creditos/conceptos/index.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['conceptos'] = Credito.objects.filter(club=club(self.request), liquidacion__isnull=True)
		return context


@method_decorator(group_required('administrativo'), name='dispatch')
class ConceptoWizard(WizardLiquidacionManager, SessionWizardView):

	""" Index y registro de conceptos """

	form_list = [
		('inicial', InicialForm),
		('conceptos', ConceptosForm),
		('plazos', PlazoFormSet)
	]

	def hacer_creditos(self):

		"""
		Crea lista de DICCIONARIOS de creditos. No lista de objetos
		Para poder utilizar mejor en manager.py
		"""

		data_inicial = self.get_cleaned_data_for_step('inicial')
		data_conceptos = self.get_cleaned_data_for_step('conceptos')
		data_plazos = self.get_cleaned_data_for_step('plazos')
		ingreso = data_inicial['ingreso']
		creditos = []

		for d in data_conceptos:
			if d:
				if d['subtotal']:
					credito = {
						'club':club(self.request),
						'periodo':data_inicial['fecha_operacion'],
						'ingreso':ingreso,
						'capital':d['subtotal'],
						'detalle' : d['detalle'],
					}
					# Establecer o cliente o dominio
					socio = Socio.objects.get(pk=d['destinatario'])
					credito['socio'] = socio
					credito['cabeza'] = socio.cabeza
					creditos.append(credito)

		return creditos


	def get_template_names(self):
		return [self.TEMPLATES[self.steps.current]]

	def get_context_data(self, form, **kwargs):
		context = super().get_context_data(form=form, **kwargs)
		tipo = "Carga de Conceptos previos"
		data_inicial = self.get_cleaned_data_for_step('inicial')
		if data_inicial:
			accesorios = self.obtener_accesorios([data_inicial['ingreso']])

		context.update(locals())

		return context


	def get_form_kwargs(self, step):
		kwargs = super().get_form_kwargs()
		if step in ["inicial", "conceptos"]:
			kwargs.update({
					'club': club(self.request),
				})
		if step == "inicial":
			kwargs.update({
				'ok_conceptos': True
			})
		return kwargs

	def get_form(self, step=None, data=None, files=None):
		form = super().get_form(step, data, files)
		formset = False
		if data:
			if 'conceptos' in data['concepto_wizard-current_step']:
				formset = True
		if step == "conceptos":
			formset = True

		if formset:
			formset = formset_factory(wraps(ConceptosForm)(partial(ConceptosForm, club=club(self.request))), extra=1)
			form = formset(prefix='conceptos', data=data)
		return form

	@transaction.atomic
	def done(self, form_list, **kwargs):
		data_inicial = self.get_cleaned_data_for_step('inicial')
		data_inicial['punto'] = club(self.request).contribuyente.points_of_sales.first()
		data_inicial['concepto'] = None # "Producto", "Servicio", "Productos y servicios"
		data_inicial['fecha_factura'] = None
		data_creditos = self.hacer_creditos()
		data_plazos = self.hacer_plazos()
		conceptos = LiquidacionCreator(data_inicial=data_inicial, data_creditos=data_creditos, data_plazos=data_plazos)
		grupo_de_creditos = conceptos.reagrupar_creditos()
		creditos = []
		for grupo in grupo_de_creditos:
			for c in grupo:
				creditos.append(conceptos.hacer_credito(c))
		Credito.objects.bulk_create(creditos)
		messages.success(self.request, "Conceptos Guardados con exito")
		return redirect('conceptos')



@method_decorator(group_required('administrativo'), name='dispatch')
class EditarConcepto(HeaderExeptMixin, generic.UpdateView):

	""" Para modificar una instancia de cualquier modelo excepto Punto """

	template_name = "creditos/conceptos/editar.html"
	model = Credito
	form_class = CreditoForm
	success_url = "/facturacion/conceptos/"

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs.update({
				'club': club(self.request),
			})
		return kwargs

	def dispatch(self, request, *args, **kwargs):
		disp = super().dispatch(request, *args, **kwargs)
		if disp.status_code == 200 and self.get_object().liquidacion:
			messages.error(request, 'No se pudo encontrar.')
			return redirect('conceptos')
		return disp


@method_decorator(group_required('administrativo'), name='dispatch')
class EliminarConcepto(HeaderExeptMixin, generic.DeleteView):

	""" Para modificar una instancia de cualquier modelo excepto Punto """

	template_name = "creditos/conceptos/eliminar.html"
	model = Credito
	form_class = CreditoForm
	success_url = "/facturacion/conceptos/"

	def dispatch(self, request, *args, **kwargs):
		disp = super().dispatch(request, *args, **kwargs)
		if disp.status_code == 200 and self.get_object().liquidacion:
			messages.error(request, 'No se pudo encontrar.')
			return redirect('conceptos')
		return disp