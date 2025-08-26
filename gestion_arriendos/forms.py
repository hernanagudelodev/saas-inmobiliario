from django import forms
from .models import ContratoMandato, PlantillaContrato

class ContratoMandatoForm(forms.ModelForm):
    class Meta:
        model = ContratoMandato
        # Seleccionamos los campos que el usuario llenará en este paso
        fields = [
            'propiedad',
            'propietario',
            'periodicidad',
            'uso_inmueble',
            'renovacion_automatica',
            'meses_preaviso',
            'tipo_incremento',
            'valor_incremento',
            'porcentaje_comision',
            'dia_corte_liquidaciones',
            'inmobiliaria_paga_administracion',
            'observaciones',
            'clausulas_adicionales',
        ]
        # En el futuro, podríamos añadir widgets para mejorar la experiencia,
        # como un selector de fechas.

class PlantillaContratoForm(forms.ModelForm):
    class Meta:
        model = PlantillaContrato
        fields = ['nombre', 'tipo_contrato', 'cuerpo_texto']
        widgets = {
            'cuerpo_texto': forms.Textarea(attrs={'rows': 15}),
        }