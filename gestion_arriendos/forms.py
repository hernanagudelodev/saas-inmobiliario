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

class RegistrarContratoExistenteForm(forms.Form):
    """
    Formulario para registrar un contrato existente (migrado) directamente 
    como VIGENTE, omitiendo los flujos de borrador y firma.
    """
    # --- Datos del Propietario/Mandato ---
    propietario = forms.ModelChoiceField(
        queryset=Cliente.objects.none(), # Se filtrará en __init__
        label="Propietario Principal",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cuenta_bancaria_pago = forms.ModelChoiceField(
        queryset=CuentaBancaria.objects.none(), # Se filtrará en __init__
        label="Cuenta bancaria para pagos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    porcentaje_comision = forms.DecimalField(
        label="Porcentaje Comisión (%)",
        max_digits=5, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    # --- NUEVOS CAMPOS AÑADIDOS ---
    periodicidad = forms.ChoiceField(
        label="Periodicidad de Pago",
        choices=ContratoMandato.Periodicidad.choices,
        initial=ContratoMandato.Periodicidad.MENSUAL,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    uso_inmueble = forms.ChoiceField(
        label="Uso del Inmueble",
        choices=ContratoMandato.UsoInmueble.choices,
        initial=ContratoMandato.UsoInmueble.VIVIENDA,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # ------------------------------
    
    # --- Datos del Arrendatario/Arrendamiento ---
    arrendatario = forms.ModelChoiceField(
        queryset=Cliente.objects.none(), # Se filtrará en __init__
        label="Arrendatario Principal",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    codeudores = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.none(), # Se filtrará en __init__
        label="Codeudores (Opcional)",
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '3'})
    )
    valor_canon = forms.DecimalField(
        label="Valor Canon Actual",
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # --- Datos de Vigencia (Comunes) ---
    fecha_inicio_vigencia = forms.DateField(
        label="Fecha Inicio Vigencia Actual",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin_vigencia = forms.DateField(
        label="Fecha Fin Vigencia Actual",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # --- Documento (Opcional) ---
    archivo_pdf_firmado = forms.FileField(
        label="Subir PDF del contrato (Opcional)",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        # La vista debe pasar 'propiedad' e 'inmobiliaria'
        propiedad = kwargs.pop('propiedad')
        inmobiliaria = kwargs.pop('inmobiliaria')
        
        super().__init__(*args, **kwargs)
        
        # Filtrar Propietarios (PR o AP relacionados con la propiedad)
        propietario_pks = PropiedadCliente.objects.filter(
            propiedad=propiedad, relacion__in=['PR', 'AP']
        ).values_list('cliente_id', flat=True)
        self.fields['propietario'].queryset = Cliente.objects.filter(pk__in=propietario_pks)
        
        # Filtrar Arrendatarios (AR relacionados con la propiedad)
        arrendatario_pks = PropiedadCliente.objects.filter(
            propiedad=propiedad, relacion='AR'
        ).values_list('cliente_id', flat=True)
        self.fields['arrendatario'].queryset = Cliente.objects.filter(pk__in=arrendatario_pks)
        
        # Filtrar Codeudores (CO relacionados con la propiedad)
        codeudor_pks = PropiedadCliente.objects.filter(
            propiedad=propiedad, relacion='CO'
        ).values_list('cliente_id', flat=True)
        self.fields['codeudores'].queryset = Cliente.objects.filter(pk__in=codeudor_pks)
        
        # Filtrar Cuentas (Cualquier cuenta de la inmobiliaria)
        # Nota: Idealmente se filtra por propietario con JS, pero esto es funcional.
        self.fields['cuenta_bancaria_pago'].queryset = CuentaBancaria.objects.filter(
            cliente__inmobiliaria=inmobiliaria
        )

    def clean(self):
        cleaned_data = super().clean()
        propietario = cleaned_data.get('propietario')
        cuenta_bancaria_pago = cleaned_data.get('cuenta_bancaria_pago')

        # Validar que la cuenta seleccionada pertenezca al propietario seleccionado
        if propietario and cuenta_bancaria_pago:
            if cuenta_bancaria_pago.cliente != propietario:
                self.add_error('cuenta_bancaria_pago', 
                               "Esta cuenta bancaria no pertenece al propietario seleccionado.")
        
        return cleaned_data