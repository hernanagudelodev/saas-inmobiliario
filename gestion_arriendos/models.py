from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from usuarios.models import Inmobiliaria
from core_inmobiliario.models import Propiedad, Cliente

# ==============================================================================
# MODELOS DE CONFIGURACIÓN Y PARÁMETROS
# ==============================================================================

class IPCAnual(models.Model):
    """
    PORQUÉ: Almacena los valores históricos del IPC (Índice de Precios al Consumidor).
    - Permite automatizar el cálculo del incremento anual del canon en contratos de vivienda.
    - Desacopla un dato externo y variable del resto de la lógica.
    - Cada inmobiliaria (tenant) gestiona sus propios valores de IPC.
    """
    anio = models.PositiveIntegerField(unique=True)
    valor = models.DecimalField(max_digits=5, decimal_places=2, help_text="Valor porcentual del IPC (ej. 5.62 para 5.62%)")
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.CASCADE)

    def __str__(self):
        return f"IPC {self.anio}: {self.valor}%"
    

class ConfiguracionArriendos(models.Model):
    """
    PORQUÉ: Centraliza las políticas y reglas de negocio operativas de una inmobiliaria.
    - Evita "ensuciar" el modelo principal `usuarios.Inmobiliaria` con configuraciones específicas de este módulo.
    - Mantiene la app `gestion_arriendos` más autocontenida y modular.
    - Facilita añadir nuevas configuraciones en el futuro sin alterar otros modelos.
    - Se conecta a cada Inmobiliaria a través de una relación uno a uno.
    """
    inmobiliaria = models.OneToOneField(
        Inmobiliaria, 
        on_delete=models.CASCADE, 
        related_name='configuracion_arriendos'
    )

    # Políticas de Cartera y Pagos
    dias_plazo_pago_defecto = models.PositiveIntegerField(
        default=5,
        help_text="Plazo por defecto (en días) que se usará al crear nuevos contratos."
    )

    # Políticas Fiscales y de Facturación
    cobra_iva_comision = models.BooleanField(
        default=True,
        help_text="Indica si se debe calcular y añadir el IVA sobre la comisión de la inmobiliaria."
    )
    porcentaje_iva = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=19.00,
        help_text="El porcentaje de IVA a aplicar (ej. 19.00 para 19%)."
    )
    requiere_factura_electronica = models.BooleanField(
        default=False,
        help_text="Activar si la inmobiliaria está obligada a emitir factura electrónica."
    )
    
    # Auditoría
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuración de Arriendos para {self.inmobiliaria.nombre}"

class PlantillaContrato(models.Model):
    """
    PORQUÉ: Permite a cada inmobiliaria crear y gestionar sus propias plantillas de contrato.
    - Otorga flexibilidad y personalización, un valor agregado clave del SaaS.
    - Estandariza los documentos legales de la inmobiliaria.
    - Facilita la generación de nuevos contratos usando 'variables' (placeholders).
    """
    class TipoContrato(models.TextChoices):
        MANDATO = 'MANDATO', 'Mandato con Propietario'
        ARRENDAMIENTO = 'ARRENDAMIENTO', 'Arrendamiento con Inquilino'

    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    tipo_contrato = models.CharField(max_length=20, choices=TipoContrato.choices)
    cuerpo_texto = models.TextField(help_text="Cuerpo de la plantilla. Usa variables como {{cliente_nombre}}.")
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_contrato_display()})"

# ==============================================================================
# MODELOS DE CONTRATOS
# ==============================================================================

class BaseContrato(models.Model):
    """
    PORQUÉ: Utiliza la herencia abstracta de Django para evitar la duplicación de código.
    - Contiene todos los campos y la lógica que son comunes tanto al Contrato de Mandato como al de Arrendamiento.
    - Mantiene el código limpio y sigue el principio DRY (Don't Repeat Yourself).
    - No crea una tabla en la base de datos; solo sirve como plantilla para otros modelos.
    """
    class EstadoContrato(models.TextChoices):
        VIGENTE = 'VIGENTE', 'Vigente'
        FINALIZADO = 'FINALIZADO', 'Finalizado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    class Periodicidad(models.TextChoices):
        MENSUAL = 'MENSUAL', 'Mensual'
        TRIMESTRAL = 'TRIMESTRAL', 'Trimestral'
        SEMESTRAL = 'SEMESTRAL', 'Semestral'
        ANUAL = 'ANUAL', 'Anual'

    class UsoInmueble(models.TextChoices):
        VIVIENDA = 'VIVIENDA', 'Vivienda'
        COMERCIAL = 'COMERCIAL', 'Comercial'
    
    class TipoIncremento(models.TextChoices):
        IPC = 'IPC', 'Basado en IPC'
        PORCENTAJE_FIJO = 'PORCENTAJE_FIJO', 'Porcentaje Fijo'
        IPC_MAS_PUNTOS = 'IPC_MAS_PUNTOS', 'IPC + Puntos Adicionales'

    propiedad = models.ForeignKey(Propiedad, on_delete=models.PROTECT)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=EstadoContrato.choices, default=EstadoContrato.VIGENTE)
    periodicidad = models.CharField(max_length=20, choices=Periodicidad.choices, default=Periodicidad.MENSUAL)
    uso_inmueble = models.CharField(max_length=20, choices=UsoInmueble.choices)
    tipo_incremento = models.CharField(max_length=20, choices=TipoIncremento.choices, default=TipoIncremento.IPC)
    valor_incremento = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje o puntos a añadir al IPC.")
    renovacion_automatica = models.BooleanField(default=True)
    meses_preaviso = models.PositiveIntegerField(default=3, help_text="Meses de antelación para notificar la renovación/terminación.")
    observaciones = models.TextField(blank=True)
    plantilla_usada = models.ForeignKey(PlantillaContrato, on_delete=models.SET_NULL, null=True, blank=True)
    clausulas_adicionales = models.TextField(blank=True)
    texto_final_renderizado = models.TextField(editable=False, help_text="El texto final del contrato tal como se firmó, para integridad legal.")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ContratoMandato(BaseContrato):
    """
    PORQUÉ: Modela específicamente la relación con el propietario.
    - Contiene campos que SÓLO tienen sentido en el contexto del propietario (ej. % de comisión).
    - Mantiene la base de datos normalizada y la lógica de negocio clara.
    - Es el eje central para el cálculo de liquidaciones.
    """

    propietario = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    porcentaje_comision = models.DecimalField(max_digits=5, decimal_places=2)
    dia_corte_liquidaciones = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(28)])
    asumir_impuestos = models.BooleanField(default=False)

    def __str__(self):
        return f"Mandato de {self.propiedad.direccion} con {self.propietario.nombre}"

class ContratoArrendamiento(BaseContrato):
    """
    PORQUÉ: Modela específicamente la relación con el inquilino (arrendatario).
    - Contiene campos exclusivos de la gestión del inquilino (ej. días de plazo para pagar).
    - Se vincula directamente al Contrato de Mandato, creando una relación clara entre las tres partes.
    - Es la base para la facturación y gestión de cartera del inquilino.
    """
    arrendatario = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    contrato_mandato = models.ForeignKey(ContratoMandato, on_delete=models.CASCADE, related_name="contratos_arrendamiento")
    prorrateado = models.BooleanField(default=False, help_text="Indica si el primer pago corresponde a una fracción del mes.")

    def __str__(self):
        return f"Arrendamiento de {self.propiedad.direccion} a {self.arrendatario.nombre}"

# ==============================================================================
# MODELOS PARA HISTORIZACIÓN DE VALORES
# ==============================================================================

class VigenciaContrato(models.Model):
    """
    PORQUÉ: Almacena cada período (vigencia) de un contrato de arrendamiento.
    - Guarda la "foto" de las condiciones (fechas y canon) para cada período, incluyendo el inicial y cada renovación.
    - Es la fuente de verdad para auditorías e informes históricos (ej. certificados para impuestos).
    - Permite saber si un contrato ha sido renovado y bajo qué condiciones exactas.
    """
    class TipoVigencia(models.TextChoices):
        INICIAL = 'INICIAL', 'Vigencia Inicial'
        RENOVACION = 'RENOVACION', 'Renovación'

    contrato_arrendamiento = models.ForeignKey(ContratoArrendamiento, on_delete=models.CASCADE, related_name='vigencias')
    tipo = models.CharField(max_length=20, choices=TipoVigencia.choices, default=TipoVigencia.INICIAL)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    valor_canon = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = "Vigencia de Contrato"
        verbose_name_plural = "Vigencias de Contrato"

    def __str__(self):
        return f"{self.get_tipo_display()} ({self.fecha_inicio} a {self.fecha_fin}) - Canon: ${self.valor_canon}"

# ==============================================================================
# MODELOS DE DESCUENTOS Y LIQUIDACIONES (A IMPLEMENTAR EN FUTURAS FASES)
# ==============================================================================

class DescuentoProgramado(models.Model):
    """
    PORQUÉ: Modela los descuentos recurrentes (ej. administración, servicios públicos).
    - Separa los costos fijos de los gastos esporádicos.
    - Su valor no se almacena aquí directamente, sino en un historial, para manejar cambios a lo largo del tiempo.
    """
    contrato_mandato = models.ForeignKey(ContratoMandato, on_delete=models.CASCADE, related_name='descuentos_programados')
    concepto = models.CharField(max_length=255)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.concepto} para contrato {self.contrato_mandato.id}"

class HistorialValorDescuento(models.Model):
    """
    PORQUÉ: Registra los cambios de valor de un descuento programado (ej. la administración sube en marzo).
    - Proporciona una auditoría completa y permite calcular liquidaciones pasadas con precisión.
    """
    descuento = models.ForeignKey(DescuentoProgramado, on_delete=models.CASCADE, related_name='historial_valores')
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_inicio_vigencia = models.DateField()

    class Meta:
        ordering = ['-fecha_inicio_vigencia']
        verbose_name = "Historial de Valor de Descuento"
        verbose_name_plural = "Historiales de Valores de Descuentos"

    def __str__(self):
        return f"Valor ${self.valor} desde {self.fecha_inicio_vigencia}"

class DescuentoNoProgramado(models.Model):
    """
    PORQUÉ: Modela los gastos únicos o en cuotas (ej. una reparación, una cuota extra).
    - Es flexible para manejar tanto pagos de una sola vez como pagos diferidos.
    - Su estado (Pendiente, Aplicado) es clave para la automatización del proceso de liquidación.
    """
    class EstadoDescuento(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de aplicar'
        APLICADO = 'APLICADO', 'Aplicado en liquidación'
        POSPUESTO = 'POSPUESTO', 'Pospuesto para siguiente mes'

    contrato_mandato = models.ForeignKey(ContratoMandato, on_delete=models.CASCADE, related_name='descuentos_no_programados')
    concepto = models.CharField(max_length=255)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    numero_cuotas = models.PositiveIntegerField(default=1)
    cuotas_aplicadas = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=EstadoDescuento.choices, default=EstadoDescuento.PENDIENTE)
    fecha_reporte = models.DateField()
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.concepto} (${self.valor_total})"

class Liquidacion(models.Model):
    """
    PORQUÉ: Almacena la "foto" del resultado del cálculo de la liquidación mensual para un propietario.
    - Crea un registro inmutable de cada pago, detallando todos sus componentes.
    - Es la base para la generación del Comprobante de Egreso y la contabilidad.
    """
    contrato_mandato = models.ForeignKey(ContratoMandato, on_delete=models.PROTECT)
    mes_liquidado = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    anio_liquidado = models.PositiveIntegerField()
    valor_arriendo_cobrado = models.DecimalField(max_digits=12, decimal_places=2)
    total_descuentos_programados = models.DecimalField(max_digits=12, decimal_places=2)
    total_descuentos_no_programados = models.DecimalField(max_digits=12, decimal_places=2)
    valor_comision = models.DecimalField(max_digits=12, decimal_places=2)
    iva_comision = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_a_pagar = models.DecimalField(max_digits=12, decimal_places=2)
    descuentos_aplicados = models.ManyToManyField(DescuentoNoProgramado, blank=True)
    pagada = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('contrato_mandato', 'mes_liquidado', 'anio_liquidado')

    def __str__(self):
        return f"Liquidación para {self.contrato_mandato.propiedad.direccion} - {self.mes_liquidado}/{self.anio_liquidado}"