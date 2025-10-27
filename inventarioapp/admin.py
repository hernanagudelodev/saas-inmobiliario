from django.contrib import admin
from .models import *


class CampoCaptacionInline(admin.TabularInline):
    model = CampoCaptacion
    extra = 1

@admin.register(SeccionCaptacion)
class SeccionCaptacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'orden']
    inlines = [CampoCaptacionInline]

@admin.register(CampoCaptacion)
class CampoCaptacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'seccion', 'tipo', 'obligatorio', 'orden']
    list_filter = ['seccion', 'tipo']
    search_fields = ['nombre']

@admin.register(ItemBase)
class ItemBaseAdmin(admin.ModelAdmin):
    list_display = ('nombre_item', 'tipo_ambiente')
    list_filter = ('tipo_ambiente',)
    search_fields = ('nombre_item',)


class ItemEntregaInline(admin.TabularInline):
    model = ItemEntrega
    extra = 0


class AmbienteEntregaInline(admin.TabularInline):
    model = AmbienteEntrega
    extra = 0


@admin.register(FormularioEntrega)
class FormularioEntregaAdmin(admin.ModelAdmin):
    list_display = ('propiedad_cliente', 'fecha_entrega', 'creado')
    list_filter = ('propiedad_cliente__propiedad',)
    inlines = [AmbienteEntregaInline]


@admin.register(AmbienteEntrega)
class AmbienteEntregaAdmin(admin.ModelAdmin):
    list_display = ('formulario_entrega', 'tipo_ambiente', 'numero_ambiente')
    inlines = [ItemEntregaInline]


class ValorCampoCaptacionInline(admin.TabularInline):
    model = ValorCampoCaptacion
    extra = 0 # No mostrar filas vacías por defecto
    # Opcional: define qué campos mostrar y si son editables
    fields = ('campo', 'valor_texto', 'valor_numero', 'valor_booleano')
    readonly_fields = ('campo',) # Generalmente no querrás cambiar el campo asociado aquí

@admin.register(FormularioCaptacion)
class FormularioCaptacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'propiedad', 'cliente', 'tipo_captacion', 'fecha', 'is_firmado', 'creado')
    list_filter = ('propiedad_cliente__propiedad', 'propiedad_cliente__cliente', 'tipo_captacion', 'is_firmado')
    search_fields = ('propiedad_cliente__propiedad__direccion', 'propiedad_cliente__cliente__nombre')
    readonly_fields = ('fecha', 'creado', 'fecha_firma') # Campos no editables
    inlines = [ValorCampoCaptacionInline] # Añade los valores como inline