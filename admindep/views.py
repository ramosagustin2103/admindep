import datetime
from datetime import date, timedelta
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from clubes.models import *
from parametros.models import *
from creditos.models import *
from comprobantes.models import *
from op.models import *
from .funciones import *
from parametros.forms import *
from django.db import transaction
from django.views import generic
from .forms import SignUpForm
from django.forms.utils import ErrorList

def simplesolutions(request):

	return HttpResponseRedirect('https://www.simplesolutions.com.ar/sporting/')

def front(request):

	if request.user.is_authenticated:
		return redirect(home)
	else:
		return redirect('login')

	return render(request, 'front/index.html', locals())

@login_required
def home(request):

	if request.user.groups.all()[0].name == "superusuario":
		return HttpResponseRedirect('admindepdj')

	elif request.user.groups.all()[0].name == "socio":
		socio = request.user.socio_set.first()
		if socio:
			comprobantes = Comprobante.objects.filter(
					socio=socio
				).order_by('-id')[:5]
			creditos = Credito.objects.filter(
				liquidacion__estado="confirmado",
				socio=socio,
				fin__isnull=True
			)
	else:
		ops = OP.objects.filter(
				club=club(request),
				confirmado=True,
				).order_by('-id')[:5]
		comprobantes = Comprobante.objects.filter(
				club=club(request),
			).order_by('-id')[:5]

	if request.user.groups.all()[0].name in ["socio", "superusuario"]:
		template = request.user.groups.all()[0].name
	else:
		template = "mayoria"
	template = 'home/%s.html' % template


	return render(request, template, locals())

@login_required
def mantenimiento(request):

	return render(request, "mantenimiento.html", locals())


class SignUp(generic.FormView):


	""" Registracion """

	template_name = 'registration/signup.html'
	form_class = SignUpForm
	success_url = '/home'


	@transaction.atomic
	def form_valid(self, form):
		codigo = form.cleaned_data['codigo']
		try:
			socio = Socio.objects.get(codigo=codigo)
		except:
			form._errors["codigo"] = ErrorList([u"El codigo que ingresaste es erroneo."])
			return super().form_invalid(form)

		# Guardado del usuario
		self.object = form.save()
		self.object.groups.add(Group.objects.get(name='socio'))

		# Incorporacion del usuario al socio y al club
		socio.usuario = self.object
		socio.save()
		socio.club.usuarios.add(self.object)

		from django.contrib.auth import login, authenticate

		username = form.cleaned_data.get('username')
		raw_password = form.cleaned_data.get('password1')
		user = authenticate(username=username, password=raw_password)
		login(self.request, user)



		return super().form_valid(form)