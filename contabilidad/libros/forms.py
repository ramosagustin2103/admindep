from django import forms
from django.forms import Textarea, TextInput, NullBooleanSelect, Select
from contabilidad.models import *

# class cuentaForm(forms.ModelForm):
# 	class Meta:
# 		model = Cuenta
# 		fields = ['dependencia', 'numero', 'nombre']
# 		labels = {
# 			'dependencia': 'Depende del rubro',
# 			'numero': 'Numero de cuenta',
# 			'nombre': 'Nombre de la cuenta',
# 		}

# 	def __init__(self, club=None, *args, **kwargs):
# 		self.club = club
# 		super(cuentaForm, self).__init__(*args, **kwargs)
# 		for field in iter(self.fields):
# 			self.fields[field].widget.attrs.update({
# 						'class': 'form-control',
# 				})
# 		self.fields['dependencia'].queryset = Plan.objects.get(club=club).cuentas.filter(nivel=3).order_by('numero')
