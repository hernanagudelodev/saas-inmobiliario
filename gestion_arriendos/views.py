from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.template import Context, Template, engines
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from core_inmobiliario.models import Propiedad
from inventarioapp.models import FormularioCaptacion
from .models import ContratoMandato, PlantillaContrato
from usuarios.mixins import TenantRequiredMixin
from .forms import ContratoMandatoForm, PlantillaContratoForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.template.loader import render_to_string

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
def crear_contrato_mandato(request, propiedad_id):
    inmobiliaria = request.user.profile.inmobiliaria
    propiedad = get_object_or_404(Propiedad, id=propiedad_id, inmobiliaria=inmobiliaria)
    
    ultima_captacion = FormularioCaptacion.objects.filter(
        propiedad_cliente__propiedad=propiedad,
        is_firmado=True,
        propiedad_cliente__relacion__in=['PR', 'AP']
    ).order_by('-fecha_firma').first()

    if not ultima_captacion:
        messages.error(request, "No se puede crear un contrato. Primero debe existir una captación firmada con un propietario o apoderado.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
    
    propietario = ultima_captacion.propiedad_cliente.cliente

    if request.method == 'POST':
        # Pasamos la inmobiliaria al formulario
        form = ContratoMandatoForm(request.POST, inmobiliaria=inmobiliaria)
        if form.is_valid():
            contrato = form.save(commit=False)
            contrato.propiedad = propiedad
            contrato.propietario = propietario
            contrato.inmobiliaria = inmobiliaria
            
            
            contrato.save()
            messages.success(request, "Borrador del Contrato de Mandato creado exitosamente.")
            # Redirigimos al detalle del contrato para el siguiente paso
            return redirect('gestion_arriendos:detalle_contrato_mandato', pk=contrato.pk)
    else:
        # Pasamos la inmobiliaria al formulario para que filtre las plantillas
        form = ContratoMandatoForm(inmobiliaria=inmobiliaria)
        form.fields['cuenta_bancaria_pago'].queryset = propietario.cuentas_bancarias.all()

    context = {
        'form': form,
        'propiedad': propiedad,
        'propietario': propietario,
        'section': 'arriendos'
    }
    return render(request, 'gestion_arriendos/crear_contrato_mandato.html', context)


class DetalleContratoMandato(LoginRequiredMixin, TenantRequiredMixin, DetailView):
    model = ContratoMandato
    template_name = 'gestion_arriendos/detalle_contrato_mandato.html'
    context_object_name = 'contrato'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'arriendos'

        contrato = self.get_object()

        if contrato.estado == 'BORRADOR':
            plantilla_obj = contrato.plantilla_usada
            template_string = "{% load letras_numeros %}" +plantilla_obj.cuerpo_texto

            contexto_render = {
                "propietario": contrato.propietario,
                "propiedad": contrato.propiedad,
                "inmobiliaria": contrato.inmobiliaria,
                "contrato": contrato
            }

            # Renderizamos primero las cláusulas del contrato
            template = engines['django'].from_string("{% load letras_numeros %}" + template_string)
            clausulas_renderizadas = template.render(contexto_render)

            # Ahora, pasamos las cláusulas a la plantilla maestra para generar el HTML completo
            contexto_final = {
                'inmobiliaria': contrato.inmobiliaria,
                'cuerpo_renderizado': clausulas_renderizadas
            }
            html_completo = render_to_string('gestion_arriendos/base_contrato_pdf.html', contexto_final)
            context['texto_borrador_renderizado'] = html_completo

        return context

@login_required
def finalizar_contrato_mandato(request, contrato_id):
    # Obtenemos el contrato, asegurándonos que pertenece al usuario
    contrato = get_object_or_404(ContratoMandato, id=contrato_id, inmobiliaria=request.user.profile.inmobiliaria)

    # Solo se puede finalizar si está en estado borrador
    if contrato.estado != 'BORRADOR':
        messages.error(request, "Este contrato ya ha sido finalizado y no puede modificarse.")
        return redirect('gestion_arriendos:detalle_contrato_mandato', pk=contrato.id)

    # Usamos la plantilla que se guardó en el borrador
    plantilla_obj = contrato.plantilla_usada
    template_string = "{% load letras_numeros %}" + plantilla_obj.cuerpo_texto

    contexto_render = {
        "propietario": contrato.propietario,
        "propiedad": contrato.propiedad,
        "inmobiliaria": contrato.inmobiliaria,
        "contrato": contrato
    }

     # Renderizamos las cláusulas
    template = engines['django'].from_string(template_string)
    clausulas_renderizadas = template.render(contexto_render)

    # Renderizamos la plantilla maestra para el guardado final
    contexto_final = {
        'inmobiliaria': contrato.inmobiliaria,
        'cuerpo_renderizado': clausulas_renderizadas
    }
    texto_renderizado = render_to_string('gestion_arriendos/base_contrato_pdf.html', contexto_final)
    
    contrato.texto_final_renderizado = texto_renderizado
    contrato.estado = 'FINALIZADO'
    contrato.save()

    messages.success(request, "El contrato ha sido finalizado y está listo para ser firmado.")
    return redirect('gestion_arriendos:detalle_contrato_mandato', pk=contrato.id)

''' Plantillas contratos '''

class ListaPlantillas(LoginRequiredMixin, TenantRequiredMixin, ListView):
    model = PlantillaContrato
    template_name = 'gestion_arriendos/lista_plantillas.html'
    context_object_name = 'plantillas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'arriendos'
        return context


# Crear plantilla de contrato.
class CrearPlantilla(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = PlantillaContrato
    form_class = PlantillaContratoForm
    template_name = 'gestion_arriendos/crear_plantilla.html'
    success_url = reverse_lazy('gestion_arriendos:lista_plantillas')

    def form_valid(self, form):
        """
        Este método se ejecuta cuando el formulario es válido.
        Usamos commit=False para poder añadir la inmobiliaria antes de guardar.
        """
        # 1. Crea el objeto en memoria, pero NO lo guardes en la BD todavía.
        plantilla = form.save(commit=False)
        
        # 2. Asigna la inmobiliaria del usuario actual al objeto.
        plantilla.inmobiliaria = self.request.user.profile.inmobiliaria
        
        # 3. Ahora que el objeto está completo, guárdalo en la BD.
        plantilla.save()

        # 4. ASIGNA EL OBJETO A LA VISTA. ¡Este es el paso que faltaba!
        self.object = plantilla

        # 5. Muestra un mensaje de éxito para el usuario.
        messages.success(self.request, "Plantilla de contrato creada exitosamente.")

        # 6. Redirige a la página de éxito.
        return redirect(self.get_success_url())

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

