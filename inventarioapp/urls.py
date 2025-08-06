from django.urls import path
from . import views

app_name = 'inventarioapp'

urlpatterns = [
    path('', views.home,name='home'),
    path('clientes/lista/', views.ListaClientes.as_view(),name='lista_clientes'),
    path('clientes/crear/', views.CrearCliente.as_view(),name='crear_cliente'),
    path('clientes/actualizar/<int:pk>/', views.ActualizarCliente.as_view(), name='actualizar_cliente'),
    path('clientes/detalle/<int:pk>/', views.DetalleCliente.as_view(), name='detalle_cliente'),
    path('propiedades/lista/', views.ListaPropiedades.as_view(),name='lista_propiedades'),
    path('clientes/eliminar/<int:pk>/', views.EliminarCliente.as_view(), name='eliminar_cliente'),
    path('propiedades/nueva/', views.crear_propiedad, name='crear_propiedad'),
    path('propiedades/actualizar/<int:id>/', views.actualizar_propiedad, name='actualizar_propiedad'),
    path('propiedades/detalle/<int:id>/', views.detalle_propiedad, name='detalle_propiedad'),
    path('propiedad/<int:propiedad_id>/captacion/', views.seleccionar_cliente_para_captacion, name='crear_captacion'),
    path('propiedades/<int:propiedad_id>/agregar-relacion/', views.agregar_relacion_propiedad, name='agregar_relacion_propiedad'),
    path('relaciones/<int:relacion_id>/eliminar/', views.eliminar_relacion_propiedad, name='eliminar_relacion_propiedad'),
    path('captacion/nueva/<int:relacion_id>/', views.formulario_captacion_dinamico, name='formulario_captacion'),
    path('captacion/<int:captacion_id>/resumen/', views.resumen_formulario_captacion, name='resumen_formulario_captacion'),
    path('captacion/<int:captacion_id>/enviar/', views.enviar_formulario_captacion, name='enviar_formulario_captacion'),
    path('captacion/<int:captacion_id>/eliminar/', views.eliminar_captacion, name='eliminar_captacion'),
    path('captacion/<int:captacion_id>/editar/', views.editar_captacion, name='editar_captacion'),
    path('entrega/crear/<int:propiedad_id>/', views.crear_formulario_entrega, name='crear_formulario_entrega'),
    path('entrega/confirmar_eliminar/<int:entrega_id>/', views.confirmar_eliminar_entrega, name='confirmar_eliminar_entrega'),
    path('entrega/<int:entrega_id>/ambientes/', views.agregar_ambiente, name='agregar_ambiente'),
    path('ambiente/<int:ambiente_id>/editar-items/', views.editar_items_ambiente, name='editar_items_ambiente'),
    path('entrega/<int:entrega_id>/resumen/', views.resumen_formulario_entrega, name='resumen_formulario_entrega'),
    path('entrega/<int:entrega_id>/enviar/', views.enviar_formulario_pdf, name='enviar_formulario_pdf'),
    path('entrega/<int:entrega_id>/ver-pdf/', views.ver_pdf_formulario_entrega, name='ver_pdf_formulario_entrega'),
    # path('entrega/propiedad/<int:propiedad_id>/', views.formularios_entrega_propiedad, name='formularios_entrega_propiedad'), Lo retiro por impractico
    path('entrega/ambiente/<int:ambiente_id>/editar/', views.editar_ambiente, name='editar_ambiente'),
    path('entrega/ambiente/<int:ambiente_id>/eliminar/', views.eliminar_ambiente, name='eliminar_ambiente'),
    path('entrega/item/<int:item_id>/eliminar/', views.eliminar_item, name='eliminar_item'),
    path('entrega/<int:entrega_id>/confirmar-envio/', views.confirmar_envio_correo, name='confirmar_envio_correo'),
]