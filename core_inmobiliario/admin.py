from django.contrib import admin
from .models import Ciudad, CuentaBancaria, TipoPropiedad, Cliente, Propiedad, PropiedadCliente

@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'inmobiliaria']
    search_fields = ['nombre']
    list_filter = ['inmobiliaria']

@admin.register(TipoPropiedad)
class TipoPropiedadAdmin(admin.ModelAdmin):
    list_display = ['tipo_propiedad', 'inmobiliaria']
    search_fields = ['tipo_propiedad']
    list_filter = ['inmobiliaria']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'identificacion', 'telefono', 'email', 'inmobiliaria']
    search_fields = ['nombre', 'identificacion', 'email']
    list_filter = ['inmobiliaria']

@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ['direccion', 'ciudad', 'tipo_propiedad', 'inmobiliaria', 'created']
    search_fields = ['direccion', 'matricula_inmobiliaria']
    list_filter = ['ciudad', 'tipo_propiedad', 'inmobiliaria']

@admin.register(PropiedadCliente)
class PropiedadClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'propiedad', 'relacion', 'inmobiliaria']
    list_filter = ['relacion', 'inmobiliaria']
    search_fields = ['cliente__nombre', 'propiedad__direccion']

@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'tipo_cuenta', 'numero_cuenta', 'nombre_banco']
    list_filter = ['tipo_cuenta']
    search_fields = ['cliente__nombre', 'numero_cuenta', 'nombre_banco']
