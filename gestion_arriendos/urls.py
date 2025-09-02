# gestion_arriendos/urls.py

from django.urls import path
from . import views

app_name = 'gestion_arriendos'

urlpatterns = [
    path('', views.home, name='home'),
    path('contratos/', views.ListaContratos.as_view(), name='lista_contratos'),
    path('contratos/mandato/crear/<int:propiedad_id>/', views.crear_contrato_mandato, name='crear_contrato_mandato'),
    path('contratos/mandato/<int:pk>/', views.DetalleContratoMandato.as_view(), name='detalle_contrato_mandato'),
    path('contratos/mandato/<int:contrato_id>/finalizar/', views.finalizar_contrato_mandato, name='finalizar_contrato_mandato'),
    path('contratos/mandato/<int:contrato_id>/descargar-borrador/', views.descargar_borrador_contrato_mandato, name='descargar_borrador_contrato_mandato'),

     path('contratos/arrendamiento/crear/<int:mandato_id>/', views.crear_contrato_arrendamiento, name='crear_contrato_arrendamiento'),

    path('plantillas/', views.ListaPlantillas.as_view(), name='lista_plantillas'),
    path('plantillas/crear/', views.CrearPlantilla.as_view(), name='crear_plantilla'),
]