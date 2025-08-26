# gestion_arriendos/urls.py

from django.urls import path
from . import views

app_name = 'gestion_arriendos'

urlpatterns = [
    path('', views.home, name='home'),
    path('contratos/', views.ListaContratos.as_view(), name='lista_contratos'),
    path('contratos/mandato/crear/', views.crear_contrato_mandato, name='crear_contrato_mandato'),

    path('plantillas/', views.ListaPlantillas.as_view(), name='lista_plantillas'),
    path('plantillas/crear/', views.CrearPlantilla.as_view(), name='crear_plantilla'),
]