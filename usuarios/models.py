from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Inmobiliaria(models.Model):
    nombre = models.CharField(max_length=100)
    nit = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='logos_inmobiliarias/', blank=True, null=True)
    texto_contractual_captacion_venta = models.TextField(default="Texto contractual de captación para venta por defecto...", blank=True, null=True)
    texto_contractual_captacion_renta = models.TextField(default="Texto contractual de captación para renta por defecto...", blank=True, null=True)
    texto_contractual_entrega = models.TextField(default="Texto contractual por defecto...", blank=True, null=True)
    firma_autorizada = models.ImageField(upload_to='firmas_inmobiliarias/', blank=True, null=True)
    nombre_firma_autorizada = models.CharField(max_length=150, blank=True, help_text="Nombre del representante autorizado que firma")
    cedula_firma_autorizada = models.CharField(max_length=30, blank=True, help_text="Cédula o documento de identidad")

    def __str__(self):
        return self.nombre


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre_completo = models.CharField(max_length=150)
    cargo = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to='usuarios/fotos/', null=True, blank=True)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.user.username})"
