from django import forms
from django.contrib.auth.models import User
from django.forms import Textarea, TextInput, NullBooleanSelect, Select
from parametros.models import *
from django.contrib.auth.forms import UserCreationForm


class FormControl:

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for field in iter(self.fields):
			clase = 'form-control'
			if "fecha" in field:
				clase += ' datepicker-autoclose'
			self.fields[field].widget.attrs.update({
	        			'class': clase
	        	})


class SignUpForm(FormControl, UserCreationForm):
	nombre = forms.CharField(max_length=80, required=True)
	apellido = forms.CharField(max_length=80, required=True)
	email = forms.EmailField(required=True)
	codigo = forms.CharField(max_length=5, required=True, label="Codigo de creacion", help_text="Para poder registrarte necesitas un código de creación de usuario. El código se encuentra en el email de bienvenida que recibiste, si no contas con uno, solicitalo a la administración de tu club")


	def save(self, commit=True):
		user = super().save(commit=False)
		user.email = self.cleaned_data["email"]
		user.first_name = self.cleaned_data["nombre"]
		user.last_name = self.cleaned_data["apellido"]
		if commit:
			user.save()
		return user

