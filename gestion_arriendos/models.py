from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from usuarios.models import Inmobiliaria
from core_inmobiliario.models import Propiedad, Cliente

# ==============================================================================
# MODELO DE CONFIGURACIÓN OPERATIVA
# ==============================================================================

class ConfiguracionArriendos(models.Model):
    """
    PORQUÉ: Centraliza las políticas y reglas de negocio operativas de una inmobiliaria.
    - Evita "ensuciar" el modelo principal `usuarios.Inmobiliaria` con configuraciones específicas de este módulo.
    - Mantiene la app `gestion_arriendos` más autocontenida y modular.
    - Se conecta a cada Inmobiliaria a través de una relación uno a uno.
    """
    inmobiliaria = models.OneToOneField(
        Inmobiliaria, 
        on_delete=models.CASCADE, 
        related_name='configuracion_arriendos'
    )
    dias_plazo_pago_defecto = models.PositiveIntegerField(
        default=5,
        help_text="Plazo por defecto (en días) que se usará al crear nuevos contratos."
    )
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
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuración de Arriendos para {self.inmobiliaria.nombre}"

# ==============================================================================
# MODELOS DE PARÁMETROS Y PLANTILLAS
# ==============================================================================

class IPCAnual(models.Model):
    """
    PORQUÉ: Almacena los valores históricos del IPC para automatizar el cálculo del incremento anual.
    """
    anio = models.PositiveIntegerField(unique=True)
    valor = models.DecimalField(max_digits=5, decimal_places=2, help_text="Valor porcentual del IPC (ej. 5.62 para 5.62%)")
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.CASCADE)

    def __str__(self):
        return f"IPC {self.anio}: {self.valor}%"

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
    titulo = models.CharField(
        max_length=255, 
        help_text="El título principal que aparecerá en el documento (ej: CONTRATO DE MANDATO)"
    )
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
    PORQUÉ: Utiliza la herencia abstracta de Django para evitar la duplicación de código y asegurar consistencia.
    - Contiene todos los campos y la lógica que son comunes y transversales al "negocio" del arrendamiento,
      aplicando tanto al acuerdo con el propietario como con el inquilino.
    - Mantiene el código limpio y sigue el principio DRY (Don't Repeat Yourself).
    - No crea una tabla en la base de datos; solo sirve como plantilla para otros modelos.
    """
    class EstadoContrato(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador' # El contrato se acaba de crear. Sus términos comerciales (comisión, fechas, etc.) se pueden editar.
        FINALIZADO = 'FINALIZADO', 'Finalizado (Pendiente de Firma)' # Se ha generado el texto legal a partir de la plantilla. Ya no se puede editar. Está listo y pendiente de las firmas.
        VIGENTE = 'VIGENTE', 'Vigente (Firmado y Activo)' # El contrato ya fue firmado y se encuentra dentro de su período de ejecución (entre la fecha de inicio y fin).
        TERMINADO = 'TERMINADO', 'Terminado' # El contrato cumplió su ciclo y finalizó de forma natural.
        CANCELADO = 'CANCELADO', 'Cancelado' # El contrato se terminó de forma anticipada.

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
    estado = models.CharField(max_length=20, choices=EstadoContrato.choices, default=EstadoContrato.BORRADOR)
    periodicidad = models.CharField(max_length=20, choices=Periodicidad.choices, default=Periodicidad.MENSUAL)
    uso_inmueble = models.CharField(max_length=20, choices=UsoInmueble.choices)
    renovacion_automatica = models.BooleanField(default=True)
    meses_preaviso = models.PositiveIntegerField(default=3, help_text="Meses de antelación para notificar la renovación/terminación.")
    tipo_incremento = models.CharField(max_length=20, choices=TipoIncremento.choices, default=TipoIncremento.IPC)
    valor_incremento = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje o puntos a añadir al IPC.")
    observaciones = models.TextField(blank=True)
    plantilla_usada = models.ForeignKey(PlantillaContrato, on_delete=models.SET_NULL, null=True, blank=True)
    clausulas_adicionales = models.TextField(blank=True)
    # PERMITIMOS QUE EL TEXTO ESTÉ VACÍO INICIALMENTE
    texto_final_renderizado = models.TextField(
        editable=False, 
        help_text="El texto final del contrato tal como se firmó, para integridad legal.",
        blank=True, # Puede estar vacío
        null=True   # Permite valores nulos en la BD
    )
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
    cuenta_bancaria_pago = models.ForeignKey('core_inmobiliario.CuentaBancaria', on_delete=models.PROTECT, help_text="Cuenta bancaria donde se consignará el pago al propietario.")
    inmobiliaria_paga_administracion = models.BooleanField(
        default=True,
        help_text="Marca esta casilla si en el acuerdo la inmobiliaria es responsable de pagar la administración."
    )

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
    dias_plazo_pago = models.PositiveIntegerField(default=5)
    prorrateado = models.BooleanField(default=False, help_text="Indica si el primer pago corresponde a una fracción del mes.")

    def __str__(self):
        return f"Arrendamiento de {self.propiedad.direccion} a {self.arrendatario.nombre}"

# ==============================================================================
# MODELOS PARA HISTORIZACIÓN Y TRAZABILIDAD
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
    valor_canon = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor total que paga el arrendatario, incluida la administración si aplica.")

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = "Vigencia de Contrato"
        verbose_name_plural = "Vigencias de Contrato"

    def __str__(self):
        return f"{self.get_tipo_display()} ({self.fecha_inicio} a {self.fecha_fin}) - Canon: ${self.valor_canon}"

class RegistroCobroMensual(models.Model): #Nuevo modelo
    """
    PORQUÉ: Es el "libro contable" de cuentas por cobrar. Representa cada obligación de pago mensual.
    - La factura de cada mes se vincula a uno de estos registros, no al contrato, garantizando una trazabilidad perfecta.
    """
    class EstadoCobro(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Facturar'
        FACTURADO = 'FACTURADO', 'Facturado'
        PAGADO = 'PAGADO', 'Pagado'
        EN_MORA = 'EN_MORA', 'En Mora'

    vigencia = models.ForeignKey(VigenciaContrato, on_delete=models.CASCADE)
    mes = models.PositiveIntegerField()
    anio = models.PositiveIntegerField()
    valor_canon = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=EstadoCobro.choices, default=EstadoCobro.PENDIENTE)
    
    class Meta:
        unique_together = ('vigencia', 'mes', 'anio')

    def __str__(self):
        return f"Cobro de {self.mes}/{self.anio} para contrato {self.vigencia.contrato_arrendamiento.id}"

# ==============================================================================
# MODELOS DE DESCUENTOS, CARGOS Y LIQUIDACIONES
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

    # MODIFICADO: Se añade un período de validez para el descuento.
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
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

class RegistroDescuentoMensual(models.Model):
    """
    PORQUÉ: Es el "libro contable" de las obligaciones de descuento. Nace de tu idea de necesitar un estado.
    - Cada registro es una obligación mensual específica (ej. "Descontar Administración de Marzo").
    - Su estado (Pendiente/Aplicado) nos da la "memoria" para manejar descuentos que se registran tarde.
    - La Liquidación se vinculará a estos registros, no al historial, garantizando una trazabilidad perfecta.
    """
    class EstadoDescuento(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Aplicar'
        APLICADO = 'APLICADO', 'Aplicado en Liquidación'

    descuento = models.ForeignKey(DescuentoProgramado, on_delete=models.CASCADE)
    mes = models.PositiveIntegerField()
    anio = models.PositiveIntegerField()
    valor = models.DecimalField(max_digits=12, decimal_places=2, help_text="El valor que tenía el descuento en este mes específico.")
    estado = models.CharField(max_length=20, choices=EstadoDescuento.choices, default=EstadoDescuento.PENDIENTE)

    class Meta:
        unique_together = ('descuento', 'mes', 'anio')
        verbose_name = "Registro Mensual de Descuento"
        verbose_name_plural = "Registros Mensuales de Descuentos"

    def __str__(self):
        return f"Descuento de {self.descuento.concepto} para {self.mes}/{self.anio}"


class CargoAdicionalArrendatario(models.Model):
    """
    PORQUÉ: Modela los cobros únicos al inquilino (ej. multas, reparaciones a su cargo).
    """
    class EstadoCargo(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Cobro'
        COBRADO = 'COBRADO', 'Cobrado'

    contrato_arrendamiento = models.ForeignKey(ContratoArrendamiento, on_delete=models.CASCADE, related_name='cargos_adicionales')
    concepto = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=EstadoCargo.choices, default=EstadoCargo.PENDIENTE)

    def __str__(self):
        return f"Cargo a {self.contrato_arrendamiento.arrendatario.nombre}: {self.concepto}"


class DescuentoNoProgramado(models.Model):
    """
    PORQUÉ: Modela el "encabezado" de un gasto único o esporádico (ej. una reparación).
    - Define el concepto general, el valor total y el número de cuotas en que se dividirá.
    - Ya no contiene un estado; el estado ahora vive en cada cuota individual.
    """
    contrato_mandato = models.ForeignKey(ContratoMandato, on_delete=models.CASCADE, related_name='descuentos_no_programados')
    concepto = models.CharField(max_length=255)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    numero_cuotas = models.PositiveIntegerField(default=1)
    fecha_reporte = models.DateField()
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.concepto} (${self.valor_total} en {self.numero_cuotas} cuota(s))"


class CuotaDescuentoNoProgramado(models.Model):
    """
    PORQUÉ: Es el "libro contable" para las cuotas de los descuentos no programados. Nace de tu idea de unificar la lógica.
    - Cada registro es una obligación de descuento específica (ej. "Cuota 1 de 3 de Reparación Plomería para Marzo").
    - Su estado (Pendiente/Aplicado) nos da la "memoria" para manejar la aplicación de cada cuota.
    - La Liquidación se vinculará a estos registros, garantizando una trazabilidad perfecta, tal como lo sugeriste.
    """
    class EstadoCuota(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Aplicar'
        APLICADO = 'APLICADO', 'Aplicado en Liquidación'

    descuento_no_programado = models.ForeignKey(DescuentoNoProgramado, on_delete=models.CASCADE, related_name='cuotas')
    mes = models.PositiveIntegerField()
    anio = models.PositiveIntegerField()
    valor_cuota = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=EstadoCuota.choices, default=EstadoCuota.PENDIENTE)
    
    class Meta:
        unique_together = ('descuento_no_programado', 'mes', 'anio')
        verbose_name = "Cuota de Descuento No Programado"
        verbose_name_plural = "Cuotas de Descuentos No Programados"

    def __str__(self):
        return f"Cuota de {self.descuento_no_programado.concepto} para {self.mes}/{self.anio}"


class Liquidacion(models.Model):
    """
    PORQUÉ: Almacena la "foto" inmutable del cálculo de la liquidación mensual para un propietario.
    - Actúa como el pre-comprobante de egreso, registrando no solo los totales, sino también
      los vínculos explícitos a cada obligación de descuento que se aplicó.
    - Es la base para la contabilidad, la auditoría y la generación de informes.
    """
    contrato_mandato = models.ForeignKey(ContratoMandato, on_delete=models.PROTECT, related_name='liquidaciones')
    mes_liquidado = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    anio_liquidado = models.PositiveIntegerField()

    # --- Totales Calculados (La "foto" del momento) ---
    valor_arriendo_cobrado = models.DecimalField(max_digits=12, decimal_places=2, help_text="Canon cobrado al arrendatario en este período.")
    total_descuentos_programados = models.DecimalField(max_digits=12, decimal_places=2)
    total_descuentos_no_programados = models.DecimalField(max_digits=12, decimal_places=2)
    valor_comision = models.DecimalField(max_digits=12, decimal_places=2)
    iva_comision = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_a_pagar = models.DecimalField(max_digits=12, decimal_places=2, help_text="El valor final a pagar al propietario.")

    # --- Trazabilidad (La Clave de la Auditoría) ---
    # Vínculo a los registros de "obligaciones" que se aplicaron en este cálculo.
    descuentos_programados_aplicados = models.ManyToManyField(
        'RegistroDescuentoMensual', 
        blank=True,
        related_name="liquidaciones"
    )
    descuentos_no_programados_aplicados = models.ManyToManyField(
        'CuotaDescuentoNoProgramado', 
        blank=True,
        related_name="liquidaciones"
    )

    # --- Estado del Pago ---
    pagada = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('contrato_mandato', 'mes_liquidado', 'anio_liquidado')
        verbose_name = "Liquidación Mensual"
        verbose_name_plural = "Liquidaciones Mensuales"

    def __str__(self):
        return f"Liquidación para {self.contrato_mandato.propiedad.direccion} - {self.mes_liquidado}/{self.anio_liquidado}"