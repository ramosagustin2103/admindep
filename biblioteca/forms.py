# -*- coding: utf-8 -*-
from django import forms
from django.forms import NullBooleanSelect
from clubes.models import *
from .models import *

class LibroForm(forms.ModelForm):
	class Meta:
		model = Libro
		fields = ['nombre', 'ubicacion', 'categoria']
		labels = {
			'nombre': 'Nombre del documento',
			'ubicacion': 'Buscar',
			'categoria': 'Categoria del documento',
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super(LibroForm, self).__init__(*args, **kwargs)
		for field in iter(self.fields):
			self.fields[field].widget.attrs.update({
						'class': 'form-control',
				})
			self.fields['categoria'].queryset = Categoria.objects.filter(
				club=self.club
				)

	def clean_nombre(self):
		nombre = self.cleaned_data['nombre']
		try:
			documento = Libro.objects.get(club=self.club, nombre=nombre)
		except:
			documento = None
		if documento:
			raise forms.ValidationError("El nombre del documento coincide con uno ya existente.")
		return nombre


class CategoriaForm(forms.ModelForm):
	class Meta:
		model = Categoria
		fields = ['nombre', 'descripcion', 'galeria']
		labels = {
			'nombre': 'Nombre de la categoria',
			'descripcion': 'Breve descripcion',
			'galeria': 'Es una galeria de imagenes?'
		}
		widgets = {
			'galeria': NullBooleanSelect(),
		}

	def __init__(self, club=None, *args, **kwargs):
		self.club = club
		super(CategoriaForm, self).__init__(*args, **kwargs)
		for field in iter(self.fields):
			self.fields[field].widget.attrs.update({
						'class': 'form-control',
				})

	def clean_nombre(self):
		nombre = self.cleaned_data['nombre']
		try:
			categoria = Categoria.objects.get(club=self.club, nombre=nombre)
		except:
			categoria = None
		if categoria:
			raise forms.ValidationError("El nombre de la categoria coincide con uno ya existente.")
		return nombre