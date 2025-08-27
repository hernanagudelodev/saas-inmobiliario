from django import forms
from .models import ContratoMandato, PlantillaContrato

class ContratoMandatoForm(forms.ModelForm):
    plantilla_usada = forms.ModelChoiceField(
        queryset=PlantillaContrato.objects.none(), # El queryset se llenará en la vista
        label="Plantilla del Contrato",
        required=True
    )

    class Meta:
        model = ContratoMandato
        # Seleccionamos los campos que el usuario llenará en este paso
        fields = [
            'plantilla_usada', 
            'periodicidad',
            'uso_inmueble',
            'renovacion_automatica',
            'meses_preaviso',
            'tipo_incremento',
            'valor_incremento',
            'porcentaje_comision',
            'dia_corte_liquidaciones',
            'inmobiliaria_paga_administracion',
            'cuenta_bancaria_pago',
            'observaciones',
            'clausulas_adicionales',
        ]

    def __init__(self, *args, **kwargs):
        # Sacamos la inmobiliaria que pasaremos desde la vista
        inmobiliaria = kwargs.pop('inmobiliaria', None)
        super().__init__(*args, **kwargs)
        
        if inmobiliaria:
            # Filtramos el queryset para mostrar solo las plantillas de mandato de esa inmobiliaria
            self.fields['plantilla_usada'].queryset = PlantillaContrato.objects.filter(
                inmobiliaria=inmobiliaria, 
                tipo_contrato='MANDATO'
            )
    # En el futuro, podríamos añadir widgets para mejorar la experiencia,
    # como un selector de fechas.

class PlantillaContratoForm(forms.ModelForm):
    class Meta:
        model = PlantillaContrato
        fields = ['nombre', 'tipo_contrato', 'cuerpo_texto']
        widgets = {
            'cuerpo_texto': forms.Textarea(attrs={'rows': 15}),
        }