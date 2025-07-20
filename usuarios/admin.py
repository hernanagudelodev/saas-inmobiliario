from django.contrib import admin
from .models import Inmobiliaria, Profile

@admin.register(Inmobiliaria)
class InmobiliariaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nit', 'telefono', 'email')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nombre_completo', 'cargo', 'inmobiliaria')
    search_fields = ('user__username', 'nombre_completo')
    list_filter = ('inmobiliaria',)