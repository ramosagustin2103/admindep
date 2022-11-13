from django import forms
from django.contrib.auth.models import User
from django.forms import Textarea, TextInput, NullBooleanSelect, Select, HiddenInput
from clubes.models import *
from .models import *
from contabilidad.models import *
from django.db.models import Q
from django_afip.models import PointOfSales
from admindep.forms import FormControl


class ingresoForm(FormControl, forms.ModelForm):
	class Meta:
		model = Ingreso
		fields = [
			'nombre',
			'prioritario',
			'cuenta_contable'
		]
		labels = {
			'nombre': "Nombre del ingreso",
			'prioritario': "Tiene prioridad de cobro?",
		}
		widgets = {
			'prioritario': NullBooleanSelect(),
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['cuenta_contable'].queryset = Plan.objects.get(club=club).cuentas.filter(
				nivel=4,
				inactivo=False,
				numero__gte=300000,
				numero__lt=500000,
				).order_by("numero")
		if self.instance.primario:
			self.fields.pop('cuenta_contable')


class gastoForm(FormControl, forms.ModelForm):
	class Meta:
		model = Gasto
		fields = [
			'nombre', 'cuenta_contable'
		]
		labels = {
			'nombre': "Nombre del tipo de gasto",
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['cuenta_contable'].queryset = Plan.objects.get(club=club).cuentas.filter(nivel=4, inactivo=False).all().order_by("numero")


class cajaForm(FormControl,forms.ModelForm):
	class Meta:
		model = Caja
		fields = [ 'nombre', 'entidad', 'saldo', 'fecha', 'cuenta_contable']

		labels = {
			'saldo' : "Saldo trasladable",
			'fecha': "Fecha del saldo",
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['cuenta_contable'].queryset = Plan.objects.get(club=club).cuentas.filter(nivel=4, inactivo=False).order_by("numero")
		if self.instance.primario:
			self.fields.pop('entidad')
			self.fields.pop('cuenta_contable')


class socioForm(FormControl, forms.ModelForm):
	class Meta:
		model = Socio
		fields = [
			'numero', 'nombre', 'apellido', 'fecha_nacimiento', 'categoria',
			'es_extranjero', 'tipo_documento',
			'numero_documento',	'telefono',
			'domicilio', 'localidad',
			'provincia', 'profesion', 'fecha_de_ingreso'
			]
		labels = {
			'fecha_nacimiento': "Fecha de nacimiento",
			'es_extranjero': 'Es extranjero?',
			'tipo_documento': 'Tipo de Documento',
			'numero_documento': 'Numero de Documento',
			'numero' : 'Numero de Socio',
			'fecha_de_ingreso': 'Fecha de ingreso al club'
		}
		widgets = {
			'es_extranjero': NullBooleanSelect(),
			'numero_documento': TextInput(attrs={'type': 'number', 'min': '0', 'step':'1', 'required':True}),
			'fecha_nacimiento': TextInput(attrs={
					'placeholder': 'Fecha de nacimiento',
					}),
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['categoria'].queryset=Categoria.objects.filter(club=club)
		self.fields['tipo_documento'].required = True
		self.fields['numero'].required = True

class acreedorForm(FormControl, forms.ModelForm):
	class Meta:
		model = Acreedor
		fields = [
			'nombre',
			'tipo', 'tipo_documento',
			'numero_documento',
			'genera',
			'cuenta_contable'
			]
		labels = {
			'tipo': 'Tipo de Gasto',
			'tipo_documento': 'Tipo de documento',
			'numero_documento': 'Numero de documento',
			'genera': 'Genera retenciones?'
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['tipo'].queryset = Gasto.objects.filter(club=club, inactivo=False).order_by("nombre")
		self.fields['cuenta_contable'].queryset = Plan.objects.get(club=club).cuentas.filter(nivel=4, inactivo=False).order_by('numero')
		self.fields['tipo_documento'].required = True
		self.fields['numero_documento'].required = True
		if self.instance.primario:
			self.fields.pop('nombre')
			self.fields.pop('tipo_documento')
			self.fields.pop('numero_documento')
			self.fields.pop('cuenta_contable')
			self.fields.pop('genera')


class userForm(FormControl, forms.ModelForm):
	class Meta:
		model = User
		fields = ['username','first_name', 'last_name','email']
		labels = {
			'first_name': "Nombre",
			'last_name': "Apellido",
		}
		help_texts = {
			"username":"Se le agregara como prefijo la abreviatura de la entidad. Solo puede estar formado por letras, números y los caracteres @/./+/-/_.",
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)

	def clean_first_name(self):
		first_name = self.cleaned_data['first_name']
		if not first_name:
			raise forms.ValidationError("Este campo es obligatorio.")
		return first_name

	def clean_last_name(self):
		last_name = self.cleaned_data['last_name']
		if not last_name:
			raise forms.ValidationError("Este campo es obligatorio.")
		return last_name

	def clean_username(self):
		username = self.cleaned_data['username']
		nombre_usuario = self.club.abreviatura + "." + username
		try:
			existe = User.objects.get(username=nombre_usuario)
		except:
			existe = None
		if existe:
			error = "Ya existe usuario con el nombre %s." % nombre_usuario
			raise forms.ValidationError(error)
		return username


class desactivarUserForm(FormControl, forms.ModelForm):
	class Meta:
		model = User
		fields = ['is_active']


class interesForm(FormControl, forms.ModelForm):
	class Meta:
		model = Accesorio
		fields = ['nombre', 'ingreso','plazo','tipo','monto','base_calculo','reconocimiento',	'cuenta_contable']
		labels = {
			'nombre': "Titulo del interes",
			'plazo': "Dias de mora desde la fecha de liquidacion",
			'tipo': "Tipo de calculo",
			'monto': "Valor de calculo",
			'reconocimiento': "Reconocimiento",
			'base_calculo': "Base de calculo",
		}
	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['cuenta_contable'].queryset = Plan.objects.get(club=club).cuentas.filter(
				nivel=4,
				inactivo=False,
				numero__gte=400000,
				numero__lt=500000
				).order_by("numero")
		self.fields['ingreso'].queryset = Ingreso.objects.filter(club=club)
		for field in iter(self.fields):
			self.fields[field].required = True

class descuentoForm(FormControl, forms.ModelForm):
	class Meta:
		model = Accesorio
		fields = ['nombre','ingreso','plazo','tipo','monto','cuenta_contable',]
		labels = {
			'nombre': "Titulo del descuento",
			'plazo': "Dias de gracia desde la fecha de liquidacion",
			'tipo': "Tipo de calculo",
			'monto': "Valor de calculo",
		}
	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['cuenta_contable'].queryset = Plan.objects.get(club=club).cuentas.filter(
				nivel=4,
				inactivo=False,
				numero__gte=400000,
				).order_by("numero")
		self.fields['ingreso'].queryset = Ingreso.objects.filter(club=club)
		for field in iter(self.fields):
			self.fields[field].required = True

class bonificacionForm(FormControl, forms.ModelForm):
	class Meta:
		model = Accesorio
		fields = ['nombre','ingreso','tipo','monto','cuenta_contable','condicion']
		labels = {
			'nombre': "Titulo de la bonificacion",
			'tipo': "Tipo de calculo",
			'monto': "Valor de calculo",
			'condicion': 'Requisito para que opere la bonifiacion',
		}
	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['cuenta_contable'].queryset = Plan.objects.get(club=club).cuentas.filter(
				nivel=4,
				inactivo=False,
				numero__gte=400000,
				).order_by("numero")
		self.fields['ingreso'].queryset = Ingreso.objects.filter(club=club)
		for field in iter(self.fields):
			self.fields[field].required = True




class grupoForm(FormControl, forms.ModelForm):
	class Meta:
		model = Grupo
		fields = [
			'nombre', 'socios', 'cabeza',
			]
		labels = {
			'cabeza': 'Destinatario de la facturacion',
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['socios'].queryset = Socio.objects.filter(club=club, es_socio=True)
		self.fields['cabeza'].queryset = Socio.objects.filter(club=club, es_socio=True)


class clienteForm(FormControl, forms.ModelForm):
	class Meta:
		model = Socio
		fields = [
			'nombre', 'apellido', 'email', 'tipo_documento',
			'numero_documento', 'telefono',
			'domicilio', 'localidad',
			'provincia',
			]

		labels = {
			'tipo_documento': 'Tipo de documento',
			'numero_documento': 'Numero de documento'
		}

		widgets = {
			'numero_documento': TextInput(attrs={'type': 'number', 'min': '0', 'step':'1', 'required':True})
		}
		
	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['tipo_documento'].required = True

class categoriaForm(FormControl, forms.ModelForm):
	class Meta:
		model = Categoria
		fields = [
			'nombre',
			'edad_limite',
			'siguiente_categoria',
			'cantidad_limite',
			]

		help_texts = {
			'edad_limite': 'Edad limite para pertenecer a la categoria',
			'siguiente_categoria': 'Nueva categoria que se asignara al socio al superar la edad limite',
			'cantidad_limite': 'Numero maximo de socios permitidos de esta categoria por grupo familiar'
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super().__init__(*args, **kwargs)
		self.fields['siguiente_categoria'].queryset = Categoria.objects.filter(club=club)


class hiddenForm(forms.ModelForm):

	class Meta:
		model = Accesorio
		fields = ['finalizacion']

		widgets = {
			'finalizacion': HiddenInput(),
		}