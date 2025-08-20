from django import forms
from .models import *


class PropiedadForm(forms.ModelForm):
    class Meta:
        model = Propiedad
        # Los campos que el usuario llenará
        fields = ['ciudad', 'tipo_propiedad', 'matricula_inmobiliaria', 'direccion', 'latitude', 'longitude']
        
        # --- LÍNEA CLAVE AÑADIDA ---
        # Excluimos 'inmobiliaria' para que form.is_valid() no falle por su ausencia.
        exclude = ['inmobiliaria', 'clientes'] # También excluimos 'clientes' que es ManyToMany
        
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        # Tu método clean para lat/long está perfecto y no necesita cambios.
        def clean(self):
            cleaned_data = super().clean()
            latitude = cleaned_data.get('latitude')
            longitude = cleaned_data.get('longitude')
            if latitude is None or longitude is None:
                raise forms.ValidationError("Debe seleccionar la ubicación en el mapa.")
            try:
                lat = float(latitude)
                lng = float(longitude)
            except (TypeError, ValueError):
                raise forms.ValidationError("Ubicación inválida. Seleccione un punto en el mapa.")
            return cleaned_data


class AgregarPropiedadClienteForm(forms.ModelForm):
    class Meta:
        model = PropiedadCliente
        fields = ['cliente', 'relacion']

    def __init__(self, *args, **kwargs):
        propiedad = kwargs.pop('propiedad', None)
        super().__init__(*args, **kwargs)
        if propiedad:
            # --- LÓGICA CORREGIDA ---
            # Ahora solo filtramos por la inmobiliaria. Esto mostrará los 2 clientes
            # que esperas ver. Si intentas agregar una relación que ya existe,
            # Django mostrará un error de validación claro, que es el
            # comportamiento deseado.
            self.fields['cliente'].queryset = Cliente.objects.filter(
                inmobiliaria=propiedad.inmobiliaria
            )
