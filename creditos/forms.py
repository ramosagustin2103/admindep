from django import forms
from django.contrib.auth.models import User
from django.forms import Textarea, TextInput, NullBooleanSelect, Select
from clubes.models import *
from .models import *
from django_afip.models import *
from django.forms import formset_factory
from admindep.forms import FormControl



class CreditoForm(FormControl, forms.ModelForm):
	class Meta:
		model = Credito
		fields = [
			'socio', 'ingreso',
			'periodo', 'capital',
			'detalle'
		]
		labels = {
			'capital': "Subtotal",
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['socio'].queryset = Socio.objects.filter(club=club, baja__isnull=True)
		self.fields['ingreso'].queryset = Ingreso.objects.filter(club=club, inactivo=False)


class InicialForm(FormControl, forms.Form):
	
	"""formulario inicial de liquidaciones"""

	punto = forms.ModelChoiceField(queryset=PointOfSales.objects.none(), empty_label="-- Seleccionar Punto de gestion --", label="Punto de gestion")
	concepto = forms.ModelChoiceField(queryset=ConceptType.objects.all(), empty_label="-- Seleccionar Tipo de operacion --", label="Tipo de operacion")
	fecha_operacion = forms.DateField(label="Fecha de la operacion", widget=forms.TextInput(attrs={'placeholder':'YYYY-MM-DD'}))
	fecha_factura = forms.DateField(label="Fecha de la factura", widget=forms.TextInput(attrs={'placeholder':'YYYY-MM-DD'}))
	ingreso = forms.ModelChoiceField(queryset=Ingreso.objects.none(), empty_label="-- Seleccionar Ingreso --", label="Ingresos")
	grupos = forms.MultipleChoiceField(choices=((None,None),))


	def __init__(self, *args, **kwargs):
		club = kwargs.pop('club')

		try:
			ok_grupos = kwargs.pop('ok_grupos')
		except:
			ok_grupos = False

		try:
			ok_conceptos = kwargs.pop('ok_conceptos')
		except:
			ok_conceptos = False
		super().__init__(*args, **kwargs)

		if ok_grupos:
			gr = Grupo.objects.filter(club=club, baja__isnull=True)
			GRUPO_CHOICES = ((g.id, g.nombre) for g in gr)
			self.fields['grupos'].choices = GRUPO_CHOICES
		else:
			self.fields.pop('grupos')
		self.fields['punto'].queryset = PointOfSales.objects.filter(owner=club.contribuyente)

		if ok_conceptos:
			self.fields.pop('punto')
			self.fields.pop('concepto')
			self.fields.pop('fecha_factura')
			self.fields['ingreso'].queryset = Ingreso.objects.filter(club=club, inactivo=False)
		else:
			self.fields.pop('ingreso')


	def clean_fecha_factura(self):

		""" validacion de fecha de factura """

		data = self.cleaned_data

		validacion = data['punto'].receipts.filter(issued_date__gt=data['fecha_factura'], receipt_type=ReceiptType.objects.get(code="11"))
		if validacion:
			raise forms.ValidationError("El punto de venta seleccionado ha generado facturas con fecha posterior a la indicada.")

		if date.today() + timedelta(days=10) < data['fecha_factura'] or data['fecha_factura'] < date.today() - timedelta(days=10):
			raise forms.ValidationError("No puede diferir en mas de 10 dias de la fecha de hoy.")
		return data['fecha_factura']


class ConceptosForm(FormControl, forms.Form):

	""" Formulario individuales de liquidaciones """

	destinatario = forms.ChoiceField(label="Destinatario")
	subtotal = forms.DecimalField(max_digits=20, decimal_places=2)
	detalle = forms.CharField(max_length=30, required=False)

	def __init__(self, club, *args, **kwargs):
		super().__init__(*args, **kwargs)
		choices = [(None, '-- Seleccione Destinatario --')]
		choices.append((None, '------ Socios ------'))
		for socio in Socio.objects.filter(club=club, es_socio=True, baja__isnull=True):
			choices.append((socio.id, socio.nombre_completo))
		choices.append((None, '------ Clientes ------'))
		for cliente in Socio.objects.filter(club=club, es_socio=False, baja__isnull=True):
			choices.append((cliente.id, cliente.nombre_completo))
		self.fields['destinatario'].choices = choices



class IndividualesForm(FormControl, forms.Form):
	
	"""formulario individual de liquidaciones"""

	destinatario = forms.ChoiceField( label="Destinatario")
	ingreso = forms.ModelChoiceField(queryset=Ingreso.objects.none(), empty_label="-- Seleccionar Ingreso --", label="Ingreso")
	subtotal = forms.DecimalField(max_digits=20, decimal_places=2)
	detalle = forms.CharField(max_length=30, required=False)
	

	def __init__(self, club, *args, **kwargs):
		super().__init__(*args, **kwargs)
		choices = [(None, '-- Seleccione Destinatario --')]
		choices.append((None, '------ Socios ------'))
		for socio in Socio.objects.filter(club=club, es_socio=True, baja__isnull=True):
			choices.append((socio.id, socio.nombre_completo))
		choices.append((None, '------ Clientes ------'))
		for cliente in Socio.objects.filter(club=club, es_socio=False, baja__isnull=True):
			choices.append((cliente.id, cliente.nombre_completo))
		self.fields['destinatario'].choices = choices
		self.fields['ingreso'].queryset = Ingreso.objects.filter(club=club, inactivo=False)



class PlazoForm(FormControl, forms.Form):

	""" Paso de indicacion de los plazos """

	accesorio = forms.IntegerField()
	plazo = forms.DateField()


PlazoFormSet = formset_factory(
		form=PlazoForm,
		extra=10
	)



class MasivoForm(FormControl, forms.Form):
	
	"""formulario masivo de liquidaciones"""

	ingreso = forms.ModelChoiceField(queryset=Ingreso.objects.none(), empty_label="-- Seleccionar Ingreso --", label="Ingreso")
	criterio = forms.ChoiceField(label="Criterio")
	subtotal = forms.DecimalField(max_digits=20, decimal_places=2, required=False)
	

	def __init__(self, club, *args, **kwargs):
		super().__init__(*args, **kwargs)
		choices = [(None, '-- Seleccione Criterio de liquidacion --')]
		# Incorporacion de criterios
		choices.append(('socios', 'Todos los socios'))
		choices.append(('grupos', 'Todos los grupos familiares'))
		categorias = Categoria.objects.filter(club=club, baja__isnull=True)
		for categoria in categorias:
			value = 'categoria-{}'.format(categoria.id)
			label = 'Socios: {}'.format(categoria.nombre)
			choices.append((value, label))
		self.fields['criterio'].choices = choices
		self.fields['ingreso'].queryset = Ingreso.objects.filter(club=club, inactivo=False)




MasivoFormSet = formset_factory(
		form=MasivoForm,
		extra=10,
	)


class PreConceptoForm(FormControl, forms.Form):

	""" Formulario de carga de conceptos """

	conceptos = forms.MultipleChoiceField(choices=((None,None),), required=False)

	def __init__(self, *args, **kwargs):
		club = kwargs.pop('club')
		super().__init__(*args, **kwargs)
		conceptos = Credito.objects.filter(club=club, liquidacion__isnull=True)
		CONCEPTO_CHOICES = []
		for c in conceptos:
			periodo = "{}-{}".format(c.periodo.year, c.periodo.month)
			nombre = "{}. {} del socio: {}: por ${}".format(
				c.ingreso,
				periodo,
				c.socio,
				c.capital
			)
			CONCEPTO_CHOICES.append((c.id, nombre))
		self.fields['conceptos'].choices = CONCEPTO_CHOICES


class ConfirmacionForm(FormControl, forms.Form):

	""" Confirmacion de liquidacion """

	confirmacion = forms.BooleanField(required=False)

	def __init__(self, *args, **kwargs):
		try:
			mostrar = kwargs.pop('mostrar')
		except:
			mostrar = False
		super().__init__(*args, **kwargs)

		if not mostrar:
			self.fields['confirmacion'].widget = forms.HiddenInput()
		else:
			self.fields['confirmacion'].label = "Seleccione si desea cobrar de contado"