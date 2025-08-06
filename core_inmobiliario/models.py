from django.db import models
from usuarios.models import Inmobiliaria

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
    identificacion = models.CharField(max_length=200, unique=True, blank=True, null=True)
    direccion_correspondiencia = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT) #Esta relación es para garantizar multitenencia 

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

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
    TipoRelacion = [
        (PROPIETARIO, 'Propietario'),
        (APODERADO, 'Apoderado'),
        (ARRENDATARIO, 'Arrendatario'),
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

