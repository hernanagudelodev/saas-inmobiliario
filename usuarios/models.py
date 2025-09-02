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
    ciudad_domicilio = models.CharField(max_length=100, blank=True, help_text="Ciudad de domicilio de la inmobiliaria")
    camara_registro = models.CharField(max_length=100, blank=True, help_text="Cámara de Comercio donde se registró la inmobiliaria")
    numero_registro = models.CharField(max_length=20, blank=True, help_text="Número de registro de la inmobiliaria en Cámara de Comercio")
    fecha_registro = models.DateField(blank=True, help_text="Fecha de registro de la inmobiliaria en Cámara de Comercio")
    matricula_arrendador = models.TextField(blank=True, help_text="Número de resolución de matrícula del arrendador y fecha de expedición")
    pagina_web = models.URLField(blank=True, help_text="Página web de la inmobiliaria")
    forma_recaudo = models.TextField(blank=True, help_text="Forma de recaudo de la inmobiliaria")


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
