from django import forms
from django.forms import inlineformset_factory
from .models import *
from core_inmobiliario.models import Cliente, Propiedad, Ciudad, TipoPropiedad, PropiedadCliente
from django.forms.formsets import Form, BaseFormSet, formset_factory, ValidationError


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

'''
A partir de esta linea se hacen los forms para creación de formulario de entrega
'''


class SeleccionarPropiedadClienteForm(forms.ModelForm):
    class Meta:
        model = PropiedadCliente
        fields = ['cliente']
    
    def __init__(self, *args, **kwargs):
        propiedad = kwargs.pop('propiedad', None)
        super().__init__(*args, **kwargs)
        if propiedad:
            self.fields['cliente'].queryset = Cliente.objects.filter(
                propiedadcliente__propiedad=propiedad,
                propiedadcliente__relacion=PropiedadCliente.ARRENDATARIO
            ).distinct()
        else:
            self.fields['cliente'].queryset = Cliente.objects.none()


class AmbienteEntregaForm(forms.ModelForm):
    class Meta:
        model = AmbienteEntrega
        fields = ['tipo_ambiente', 'numero_ambiente', 'nombre_personalizado']


ItemEntregaFormSet = inlineformset_factory(
    parent_model=AmbienteEntrega,
    model=ItemEntrega,
    fields=['nombre_item', 'estado', 'cantidad', 'material', 'observaciones'],
    extra=0,          # fila vacía para ítem nuevo
    can_delete=False  # seguimos usando tu botón "Eliminar"
)


'''
ModelForm para hacer la creación del formulario de captación
'''
class FormularioCaptacionDinamico(forms.ModelForm):
    class Meta:
        model = FormularioCaptacion
        fields = ['tipo_captacion', 'observaciones_generales']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secciones = []
        secciones = SeccionCaptacion.objects.prefetch_related('campos').order_by('orden')
        for seccion in secciones:
            campos_lista = []
            for campo in seccion.campos.all().order_by('orden'):
                field_name = f'campo_{campo.id}'
                campos_lista.append(field_name)
                if campo.tipo == 'texto':
                    self.fields[field_name] = forms.CharField(
                        label=campo.nombre,
                        required=campo.obligatorio
                    )
                elif campo.tipo == 'numero':
                    self.fields[field_name] = forms.FloatField(
                        label=campo.nombre,
                        required=campo.obligatorio
                    )
                elif campo.tipo == 'booleano':
                    self.fields[field_name] = forms.BooleanField(
                        label=campo.nombre,
                        required=False
                    )
            # Guardamos el nombre y los campos de la sección para el template
            self.secciones.append({'nombre': seccion.nombre, 'campos': campos_lista})
