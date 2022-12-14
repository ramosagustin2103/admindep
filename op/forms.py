from django import forms
from django.forms import Textarea, TextInput, NullBooleanSelect, Select
from parametros.models import *
from .models import *
from django_afip.models import *



class encabezadoForm(forms.ModelForm):
	class Meta:
		model = OP
		fields = [
			'punto', 'acreedor', 'fecha_operacion'
		]
		labels = {
			'punto': 'Punto de gestion',
			'fecha_operacion': 'Fecha de la operacion',
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super(encabezadoForm, self).__init__(*args, **kwargs)
		clase = 'form-control'
		for field in iter(self.fields):
			if field == 'fecha_operacion':
				clase += ' datepicker'
			self.fields[field].widget.attrs.update({
						'class': clase,
				})
		self.fields['punto'].queryset = PointOfSales.objects.filter(owner=club.contribuyente)
		self.fields['acreedor'].queryset = Acreedor.objects.filter(club=club)


class PagoParcialForm(forms.ModelForm):
	class Meta:
		model = OP
		fields = [
			'punto', 'total',
		]
		labels = {
			'punto': 'Punto de gestion',
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super(PagoParcialForm, self).__init__(*args, **kwargs)
		for field in iter(self.fields):
			self.fields[field].widget.attrs.update({
						'class': 'form-control',
				})
		self.fields['punto'].queryset = PointOfSales.objects.filter(owner=club.contribuyente)


class cajaForm(forms.ModelForm):
	class Meta:
		model = CajaOP
		fields = ['caja','referencia','valor']

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super(cajaForm, self).__init__(*args, **kwargs)
		for field in iter(self.fields):
			self.fields[field].widget.attrs.update({
						'class': 'form-control',
				})
		self.fields['caja'].queryset = Caja.objects.filter(club=self.club, primario=False).order_by("nombre")



class encabezadoDeudaForm(forms.ModelForm):
	class Meta:
		model = Deuda
		fields = [
			'acreedor', 'fecha', 'numero',
		]
		labels = {
			'fecha': 'Fecha del comprobante',
			'numero': 'Numero del comprobante',
		}
		widgets = {
			'fecha': TextInput(attrs={
					'id': 'datepicker-autoclose',
					'placeholder': 'AAAA-MM-DD',
					}),
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super(encabezadoDeudaForm, self).__init__(*args, **kwargs)
		for field in iter(self.fields):
			self.fields[field].widget.attrs.update({
						'class': 'form-control',
				})
		self.fields['acreedor'].queryset = Acreedor.objects.filter(club=club).order_by('nombre')

	def clean_numero(self):
		numero = self.cleaned_data['numero']
		if not numero:
			raise forms.ValidationError("Este campo es obligatorio.")
		return numero


class detallesDeudaForm(forms.ModelForm):
	class Meta:
		model = Deuda
		fields = [
			'observacion'
		]
		widgets = {
			'observacion': Textarea(attrs={'rows': 8}),
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super(detallesDeudaForm, self).__init__(*args, **kwargs)
		for field in iter(self.fields):
			self.fields[field].widget.attrs.update({
						'class': 'form-control',
				})
