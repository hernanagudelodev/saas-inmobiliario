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