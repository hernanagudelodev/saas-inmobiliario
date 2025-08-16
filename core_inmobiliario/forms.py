from django import forms
from .models import *
from .models import *

class PropiedadForm(forms.ModelForm):
    class Meta:
        model = Propiedad
        # Incluye solo los campos relevantes
        fields = ['ciudad', 'tipo_propiedad', 'matricula_inmobiliaria', 'direccion', 'latitude', 'longitude']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
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
            # Excluir clientes ya asociados a esa propiedad
            clientes_asociados = propiedad.propiedadcliente_set.values_list('cliente_id', flat=True)
            self.fields['cliente'].queryset = Cliente.objects.exclude(id__in=clientes_asociados)
