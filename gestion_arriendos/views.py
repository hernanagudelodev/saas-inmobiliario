from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ContratoMandato, PlantillaContrato
from usuarios.mixins import TenantRequiredMixin
from .forms import ContratoMandatoForm, PlantillaContratoForm
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy

@login_required
def home(request):
    """
    Vista principal para el módulo de gestión de arriendos.
    En el futuro, servirá como un dashboard con estadísticas y accesos rápidos.
    """
    # El 'section' nos ayudará a marcar el menú lateral como activo.
    context = {
        'section': 'arriendos'
    }
    return render(request, 'gestion_arriendos/home.html', context)

class ListaContratos(LoginRequiredMixin, TenantRequiredMixin, ListView):
    model = ContratoMandato
    template_name = 'gestion_arriendos/lista_contratos.html'
    context_object_name = 'contratos'
    paginate_by = 10 # Puedes ajustar el número de contratos por página

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'arriendos' # Para mantener el menú activo
        return context
    
@login_required
def crear_contrato_mandato(request):
    if request.method == 'POST':
        form = ContratoMandatoForm(request.POST)
        if form.is_valid():
            contrato = form.save(commit=False)
            try:
                contrato.inmobiliaria = request.user.profile.inmobiliaria
            except Exception:
                raise PermissionDenied("El usuario no tiene una inmobiliaria asignada.")
            
            # Aquí podrías añadir más lógica, como estado inicial, etc.
            # Por ahora, lo guardamos directamente.
            contrato.save()
            
            messages.success(request, "Contrato de Mandato creado exitosamente.")
            # Eventualmente, esto redirigirá al siguiente paso del "wizard" (crear el Contrato de Arrendamiento)
            # Por ahora, redirigimos a la lista de contratos.
            return redirect('gestion_arriendos:lista_contratos')
    else:
        form = ContratoMandatoForm()

    context = {
        'form': form,
        'section': 'arriendos'
    }
    return render(request, 'gestion_arriendos/crear_contrato_mandato.html', context)

class ListaPlantillas(LoginRequiredMixin, TenantRequiredMixin, ListView):
    model = PlantillaContrato
    template_name = 'gestion_arriendos/lista_plantillas.html'
    context_object_name = 'plantillas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'arriendos'
        return context

# gestion_arriendos/views.py

class CrearPlantilla(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = PlantillaContrato
    form_class = PlantillaContratoForm
    template_name = 'gestion_arriendos/crear_plantilla.html'
    success_url = reverse_lazy('gestion_arriendos:lista_plantillas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'arriendos'

        # Definimos las variables disponibles y las pasamos al template.
        context['variables_disponibles'] = {
            'Contrato': [
                {'variable': '{{ contrato.fecha_inicio }}', 'descripcion': 'Fecha de inicio del contrato.'},
                {'variable': '{{ contrato.fecha_fin }}', 'descripcion': 'Fecha de finalización del contrato.'},
                {'variable': '{{ contrato.valor_canon_en_letras }}', 'descripcion': 'El valor del canon de arrendamiento escrito en letras.'},
                {'variable': '{{ contrato.valor_canon_en_numeros }}', 'descripcion': 'El valor del canon de arrendamiento en números.'},
                {'variable': '{{ contrato.uso_inmueble_display }}', 'descripcion': 'El uso del inmueble arrendado.'},
                {'variable': '{{ contrato.cuenta_bancaria_pago.tipo_cuenta_display }}', 'descripcion': 'Tipo de cuenta bancaria del propietario.'},
                {'variable': '{{ contrato.cuenta_bancaria_pago.numero_cuenta }}', 'descripcion': 'Número de cuenta bancaria del propietario.'},
                {'variable': '{{ contrato.cuenta_bancaria_pago.nombre_banco }}', 'descripcion': 'Nombre del banco de la cuenta bancaria del propietario.'},
            ],
            'Propietario': [
                {'variable': '{{ propietario.nombre }}', 'descripcion': 'Nombre completo del propietario.'},
                {'variable': '{{ propietario.identificacion }}', 'descripcion': 'Documento de identidad del propietario.'},
            ],
            'Arrendatario': [
                {'variable': '{{ arrendatario.nombre }}', 'descripcion': 'Nombre completo del arrendatario.'},
                {'variable': '{{ arrendatario.identificacion }}', 'descripcion': 'Documento de identidad del arrendatario.'},
            ],
            'Inmueble': [
                {'variable': '{{ propiedad.direccion }}', 'descripcion': 'Dirección completa del inmueble.'},
                {'variable': '{{ propiedad.ciudad }}', 'descripcion': 'Ciudad donde se ubica el inmueble.'},
                {'variable': '{{ propiedad.matricula_inmobiliaria }}', 'descripcion': 'Matrícula inmobiliaria del inmueble.'},
                {'variable': '{{ propiedad.escritura_publica }}', 'descripcion': 'Número de escritura pública del inmueble.'},
                {'variable': '{{ propiedad.tipo_propiedad_display }}', 'descripcion': 'Tipo de propiedad del inmueble.'},
            ],
            'Inmobiliaria': [
                {'variable': '{{ inmobiliaria.nombre }}', 'descripcion': 'Nombre de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.nit }}', 'descripcion': 'NIT de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.direccion }}', 'descripcion': 'Dirección de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.telefono }}', 'descripcion': 'Teléfono de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.email }}', 'descripcion': 'Correo Electrónico de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.nombre_firma_autorizada }}', 'descripcion': 'Nombre de la firma autorizada (Representante Legal).'},
                {'variable': '{{ inmobiliaria.cedula_firma_autorizada }}', 'descripcion': 'Cédula de la firma autorizada (Representante Legal).'},
                {'variable': '{{ inmobiliaria.ciudad_domicilio }}', 'descripcion': 'Ciudad de domicilio de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.camara_registro }}', 'descripcion': 'Cámara de registro de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.numero_registro }}', 'descripcion': 'Número de registro de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.fecha_registro }}', 'descripcion': 'Fecha de registro de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.matricula_arrendador }}', 'descripcion': 'Matrícula de arrendador de la inmobiliaria.'},
                {'variable': '{{ inmobiliaria.pagina_web }}', 'descripcion': 'Página web de la inmobiliaria.'},
            ]
        }
        # ----------------------
        
        return context

