from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm, RegistroUsuarioForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User


@login_required
def editar_perfil(request):
    profile = request.user.profile 
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('perfil_editado')  # Redirige a una página de éxito o al perfil mismo
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'usuarios/editar_perfil.html', {'form': form})


@login_required
def perfil_editado(request):
    return render(request, 'usuarios/perfil_editado.html')


def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password'])
            usuario.save()
            # Autentica y loguea al usuario automáticamente
            user = authenticate(username=usuario.username, password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('editar_perfil')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'usuarios/registro_usuario.html', {'form': form})
