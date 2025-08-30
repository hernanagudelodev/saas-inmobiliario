from django.contrib import admin
from .models import *

# --- CONFIGURACIÓN ---
@admin.register(ConfiguracionArriendos)
class ConfiguracionArriendosAdmin(admin.ModelAdmin):
    list_display = ('inmobiliaria', 'dias_plazo_pago_defecto', 'cobra_iva_comision', 'actualizado')

@admin.register(IPCAnual)
class IPCAnualAdmin(admin.ModelAdmin):
    list_display = ('anio', 'valor', 'inmobiliaria')
    list_filter = ('inmobiliaria',)

@admin.register(PlantillaContrato)
class PlantillaContratoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'titulo', 'tipo_contrato', 'inmobiliaria', 'creado')
    list_filter = ('inmobiliaria', 'tipo_contrato')

# --- CONTRATOS ---
class VigenciaContratoInline(admin.TabularInline):
    model = VigenciaContrato
    extra = 1

@admin.register(ContratoMandato)
class ContratoMandatoAdmin(admin.ModelAdmin):
    list_display = ('propietario', 'propiedad', 'estado', 'inmobiliaria')
    list_filter = ('inmobiliaria', 'estado')
    search_fields = ('propietario__nombre', 'propiedad__direccion')

@admin.register(ContratoArrendamiento)
class ContratoArrendamientoAdmin(admin.ModelAdmin):
    list_display = ('arrendatario', 'propiedad', 'estado', 'contrato_mandato')
    list_filter = ('inmobiliaria', 'estado')
    search_fields = ('arrendatario__nombre', 'propiedad__direccion')
    inlines = [VigenciaContratoInline]

# --- TRAZABILIDAD Y DESCUENTOS ---
@admin.register(DescuentoProgramado)
class DescuentoProgramadoAdmin(admin.ModelAdmin):
    list_display = ('concepto', 'contrato_mandato', 'fecha_inicio', 'fecha_fin')
    list_filter = ('inmobiliaria',)

@admin.register(DescuentoNoProgramado)
class DescuentoNoProgramadoAdmin(admin.ModelAdmin):
    list_display = ('concepto', 'contrato_mandato', 'valor_total', 'numero_cuotas')
    list_filter = ('inmobiliaria',)

@admin.register(Liquidacion)
class LiquidacionAdmin(admin.ModelAdmin):
    list_display = ('contrato_mandato', 'mes_liquidado', 'anio_liquidado', 'total_a_pagar', 'pagada')
    list_filter = ('inmobiliaria', 'pagada')

# --- REGISTROS DE "LIBRO CONTABLE" (Opcional registrarlos, pero útil para depurar) ---
# admin.site.register(RegistroCobroMensual)
# admin.site.register(HistorialValorDescuento)
# admin.site.register(RegistroDescuentoMensual)
# admin.site.register(CuotaDescuentoNoProgramado)
# admin.site.register(CargoAdicionalArrendatario)