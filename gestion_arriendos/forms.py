from django import forms

from core_inmobiliario.models import Cliente, CuentaBancaria, PropiedadCliente
from .models import ContratoArrendamiento, ContratoMandato, PlantillaContrato


class ContratoMandatoForm(forms.ModelForm):
    plantilla_usada = forms.ModelChoiceField(
        queryset=PlantillaContrato.objects.none(),
        label="Plantilla del Contrato",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cuenta_bancaria_pago = forms.ModelChoiceField(
        queryset=CuentaBancaria.objects.none(),
        label="Cuenta bancaria para pagos",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    es_contrato_migrado = forms.BooleanField(
        required=False, # No es obligatorio marcarlo
        label="¿Es un contrato existente (migrado)?",
        help_text="Marcar si este contrato ya existía antes de usar el sistema. Omitirá la validación de Captación.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = ContratoMandato
        fields = [
            'plantilla_usada', 
            'cuenta_bancaria_pago',
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
            'es_contrato_migrado',
        ]
        widgets = {
            'periodicidad': forms.Select(attrs={'class': 'form-select'}),
            'uso_inmueble': forms.Select(attrs={'class': 'form-select'}),
            'renovacion_automatica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # Capturamos y removemos nuestros argumentos personalizados ANTES de llamar al constructor padre
        inmobiliaria = kwargs.pop('inmobiliaria', None)
        propietario = kwargs.pop('propietario', None)
        
        # Llamamos al constructor padre, pero ya sin los argumentos personalizados
        super().__init__(*args, **kwargs)
        
        # Ahora usamos los argumentos capturados para filtrar los campos
        if inmobiliaria:
            self.fields['plantilla_usada'].queryset = PlantillaContrato.objects.filter(
                inmobiliaria=inmobiliaria, 
                tipo_contrato='MANDATO'
            )
        if propietario:
             self.fields['cuenta_bancaria_pago'].queryset = propietario.cuentas_bancarias.all()


# --- FORMULARIO PARA LA PLANTILLA DEL CONTRATO ---

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
        queryset=Cliente.objects.none(),
        label="Arrendatario Principal",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # --- NUEVO CAMPO PARA SELECCIONAR CODEUDORES ---
    codeudores = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.none(),
        label="Codeudores (selecciona uno o varios)",
        required=False, # Hacemos que no sea obligatorio tener codeudores
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'})
    )
    # -----------------------------------------------
    
    plantilla_usada = forms.ModelChoiceField(
        queryset=PlantillaContrato.objects.none(),
        label="Plantilla del Contrato",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # --- CAMPOS ADICIONALES PARA EL CONTRATO DE ARRENDAMIENTO, VIENEN DEL MODELO VIGENCIA. 
    # --- PERMITEN CREAR LA PRIMERA VIGENCIA DEL CONTRATO DE ARRENDAMIENTO EN UN SOLO FORM ---

    valor_canon = forms.DecimalField(
        label="Valor del Canon de Arrendamiento",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    fecha_inicio = forms.DateField(
        label="Fecha de Inicio del Contrato",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        label="Fecha de Finalización del Contrato",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    # --- Checkbox añadido ---
    es_contrato_migrado = forms.BooleanField(
        required=False,
        label="¿Es un contrato existente (migrado)?",
        help_text="Marcar si este contrato ya existía antes de usar el sistema. Omitirá validaciones iniciales.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    # -----------------------

    class Meta:
        model = ContratoArrendamiento
        # Añadimos 'codeudores' a la lista de campos
        fields = [
            'arrendatario',
            'codeudores',
            'plantilla_usada',
            'periodicidad',
            'uso_inmueble',
            'renovacion_automatica',
            'meses_preaviso',
            'dias_plazo_pago',
            'prorrateado',
            'observaciones',
            'clausulas_adicionales',
            'es_contrato_migrado', # <-- Añadido a la lista de fields
        ]
        widgets = {
            'periodicidad': forms.Select(attrs={'class': 'form-select'}),
            'uso_inmueble': forms.Select(attrs={'class': 'form-select'}),
            'renovacion_automatica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prorrateado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        inmobiliaria = kwargs.pop('inmobiliaria', None)
        propiedad = kwargs.pop('propiedad', None)
        
        super().__init__(*args, **kwargs)
        
        if inmobiliaria:
            self.fields['plantilla_usada'].queryset = PlantillaContrato.objects.filter(
                inmobiliaria=inmobiliaria, 
                tipo_contrato='ARRENDAMIENTO'
            )
        
        if propiedad:
            # Filtramos los clientes vinculados como 'Arrendatario'
            arrendatarios_pks = PropiedadCliente.objects.filter(
                propiedad=propiedad, relacion='AR'
            ).values_list('cliente_id', flat=True)
            self.fields['arrendatario'].queryset = Cliente.objects.filter(pk__in=arrendatarios_pks)

            # --- LÓGICA PARA FILTRAR CODEUDORES ---
            codeudores_pks = PropiedadCliente.objects.filter(
                propiedad=propiedad, relacion='CO' # 'CO' es el código para 'Codeudor'
            ).values_list('cliente_id', flat=True)
            self.fields['codeudores'].queryset = Cliente.objects.filter(pk__in=codeudores_pks)
            # ---------------------------------------------

# --- FORMULARIO PARA SUBIR EL MANDATO FIRMADO ---
class SubirMandatoFirmadoForm(forms.ModelForm):
    class Meta:
        model = ContratoMandato
        fields = ['archivo_pdf_firmado']
        widgets = {
            'archivo_pdf_firmado': forms.FileInput(attrs={'class': 'form-control'})
        }

# --- FORMULARIO PARA SUBIR EL ARRENDAMIENTO FIRMADO ---
class SubirArrendamientoFirmadoForm(forms.ModelForm):
    class Meta:
        model = ContratoArrendamiento
        fields = ['archivo_pdf_firmado']
        widgets = {
            'archivo_pdf_firmado': forms.FileInput(attrs={'class': 'form-control'})
        }

