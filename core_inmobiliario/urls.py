from django.urls import path
from . import views

app_name = 'core_inmobiliario'

urlpatterns = [
    path('clientes/lista/', views.ListaClientes.as_view(),name='lista_clientes'),
    path('clientes/crear/', views.CrearCliente.as_view(),name='crear_cliente'),
    path('clientes/actualizar/<int:pk>/', views.ActualizarCliente.as_view(), name='actualizar_cliente'),
    path('clientes/detalle/<int:pk>/', views.DetalleCliente.as_view(), name='detalle_cliente'),
    path('propiedades/lista/', views.ListaPropiedades.as_view(),name='lista_propiedades'),
    path('clientes/eliminar/<int:pk>/', views.EliminarCliente.as_view(), name='eliminar_cliente'),
    path('propiedades/nueva/', views.crear_propiedad, name='crear_propiedad'),
    path('propiedades/actualizar/<int:id>/', views.actualizar_propiedad, name='actualizar_propiedad'),
    path('propiedades/detalle/<int:id>/', views.detalle_propiedad, name='detalle_propiedad'),
    path('propiedades/<int:propiedad_id>/agregar-relacion/', views.agregar_relacion_propiedad, name='agregar_relacion_propiedad'),
    path('relaciones/<int:relacion_id>/eliminar/', views.eliminar_relacion_propiedad, name='eliminar_relacion_propiedad'),
]