from django.db import models
from usuarios.models import Inmobiliaria
from django.core.exceptions import ValidationError

# =======================
# CATÁLOGOS BÁSICOS
# =======================

class Ciudad(models.Model):
    nombre = models.CharField(max_length=200)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT) #Esta relación es para garantizar multitenencia 

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'

    def __str__(self):
        return self.nombre

class TipoPropiedad(models.Model):
    tipo_propiedad = models.CharField(max_length=200)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT) #Esta relación es para garantizar multitenencia 

    class Meta:
        ordering = ['tipo_propiedad']
        verbose_name = 'Tipo de Propiedades'
        verbose_name_plural = 'Tipos de Propiedades'

    def __str__(self):
        return self.tipo_propiedad

# =======================
# CLIENTES Y PROPIEDADES
# =======================

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    identificacion = models.CharField(max_length=200, blank=True, null=True)
    direccion_correspondiencia = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT) #Esta relación es para garantizar multitenencia 

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        #REGLA DE UNICIDAD COMBINADA
        constraints = [
            models.UniqueConstraint(fields=['identificacion', 'inmobiliaria'], name='unique_identificacion_inmobiliaria')
        ]

    def __str__(self):
        return self.nombre

class Propiedad(models.Model):
    ciudad = models.ForeignKey(Ciudad, related_name='ciudad_propiedad', blank=True, on_delete=models.DO_NOTHING)
    tipo_propiedad = models.ForeignKey(TipoPropiedad, related_name='propiedad_tipo', on_delete=models.DO_NOTHING)
    matricula_inmobiliaria = models.CharField(max_length=200, blank=True, null=True)
    direccion = models.CharField(max_length=200)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT) #Esta relación es para garantizar multitenencia 
    clientes = models.ManyToManyField(Cliente, through='PropiedadCliente', related_name='clientes_propiedad')
    created = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    escritura_publica = models.CharField(max_length=200, blank=True, help_text='Número de escritura pública, fecha de expedición, notaría y ciudad')

    class Meta:
        verbose_name = 'Propiedad'
        verbose_name_plural = 'Propiedades'
        indexes = [
            models.Index(fields=['-created']),
        ]
        ordering = ['-created']

    def __str__(self):
        return self.direccion

class PropiedadCliente(models.Model):
    PROPIETARIO = 'PR'
    APODERADO = 'AP'
    ARRENDATARIO = 'AR'
    CODEUDOR = 'CO'
    TipoRelacion = [
        (PROPIETARIO, 'Propietario'),
        (APODERADO, 'Apoderado'),
        (ARRENDATARIO, 'Arrendatario'),
        (CODEUDOR, 'Codeudor'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE)
    relacion = models.CharField(max_length=2, choices=TipoRelacion)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Propiedades y Clientes'
        verbose_name_plural = 'Propiedades y Clientes'
        constraints = [
            models.UniqueConstraint(fields=['cliente', 'propiedad', 'relacion'], name='unique_cliente_propiedad_relacion')
        ]

    def clean(self):
        # Validar consistencia de inmobiliaria
        if self.cliente.inmobiliaria != self.inmobiliaria or self.propiedad.inmobiliaria != self.inmobiliaria:
            raise ValidationError("La inmobiliaria debe coincidir en cliente, propiedad y esta relación.")

    def __str__(self):
        return f'El cliente {self.cliente} es {self.get_relacion_display()} de la {self.propiedad}'

# =======================
# CUENTAS BANCARIAS
# =======================

class CuentaBancaria(models.Model):
    """
    PORQUÉ: Almacena los datos bancarios de un cliente (propietario) de forma segura y separada.
    - Evita añadir campos bancarios al modelo Cliente, que es genérico para propietarios y arrendatarios.
    - Permite que un cliente pueda tener múltiples cuentas en el futuro si es necesario.
    - Se vincula directamente con el Cliente, manteniendo la información centralizada en la app 'core_inmobiliario'.
    """
    class TipoCuenta(models.TextChoices):
        AHORROS = 'AHORROS', 'Ahorros'
        CORRIENTE = 'CORRIENTE', 'Corriente'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cuentas_bancarias')
    nombre_banco = models.CharField(max_length=200)
    tipo_cuenta = models.CharField(max_length=20, choices=TipoCuenta.choices)
    numero_cuenta = models.CharField(max_length=50)
    nombre_titular = models.CharField(max_length=255, blank=True)
    identificacion_titular = models.CharField(max_length=50, blank=True)
    
    # Este campo permite marcar una cuenta como la principal para los pagos
    es_predeterminada = models.BooleanField(default=True)
    
    # Auditoría
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'

    def __str__(self):
        return f"Cuenta de {self.cliente.nombre} en {self.nombre_banco}"