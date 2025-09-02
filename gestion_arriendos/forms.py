from django import forms

from core_inmobiliario.models import Cliente, PropiedadCliente
from .models import ContratoArrendamiento, ContratoMandato, PlantillaContrato

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
        fields = ['nombre','titulo', 'tipo_contrato', 'cuerpo_texto']
        widgets = {
            'cuerpo_texto': forms.Textarea(attrs={'rows': 15}),
        }


# --- FORMULARIO PARA EL CONTRATO DE ARRENDAMIENTO ---
class ContratoArrendamientoForm(forms.ModelForm):
    arrendatario = forms.ModelChoiceField(
        queryset=Cliente.objects.none(), # Se llenará dinámicamente en __init__
        label="Arrendatario",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    plantilla_usada = forms.ModelChoiceField(
        queryset=PlantillaContrato.objects.none(), # Se llenará dinámicamente en __init__
        label="Plantilla del Contrato",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ContratoArrendamiento
        fields = [
            'arrendatario',
            'plantilla_usada',
            'periodicidad',
            'uso_inmueble',
            'renovacion_automatica',
            'meses_preaviso',
            'dias_plazo_pago',
            'prorrateado',
            'observaciones',
            'clausulas_adicionales',
        ]
        # Aplicamos estilo a los campos de selección y checkboxes
        widgets = {
            'periodicidad': forms.Select(attrs={'class': 'form-select'}),
            'uso_inmueble': forms.Select(attrs={'class': 'form-select'}),
            'renovacion_automatica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prorrateado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # Capturamos los argumentos personalizados que pasamos desde la vista
        inmobiliaria = kwargs.pop('inmobiliaria', None)
        propiedad = kwargs.pop('propiedad', None)
        
        super().__init__(*args, **kwargs)
        
        # Filtramos las plantillas de contrato
        if inmobiliaria:
            self.fields['plantilla_usada'].queryset = PlantillaContrato.objects.filter(
                inmobiliaria=inmobiliaria, 
                tipo_contrato='ARRENDAMIENTO'
            )
        
        # Filtramos los clientes para mostrar solo los vinculados como Arrendatarios
        if propiedad:
            arrendatarios_pks = PropiedadCliente.objects.filter(
                propiedad=propiedad,
                relacion='AR'  # 'AR' es el código para 'Arrendatario'
            ).values_list('cliente_id', flat=True)
            
            self.fields['arrendatario'].queryset = Cliente.objects.filter(pk__in=arrendatarios_pks)