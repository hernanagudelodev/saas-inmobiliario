from django.urls import path
from . import views

urlpatterns = [
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/editar/exito/', views.perfil_editado, name='perfil_editado'),
    path('registro/', views.registro_usuario, name='register'),
]