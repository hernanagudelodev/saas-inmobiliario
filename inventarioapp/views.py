from django.shortcuts import render,get_object_or_404, redirect
from django.core.paginator import Paginator
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import *
from core_inmobiliario.models import Cliente, Propiedad, PropiedadCliente
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .forms import *
from datetime import datetime
from django.contrib import messages
from django.forms import formset_factory
from django.http import JsonResponse,HttpResponse,HttpResponseForbidden
import os
from django.core.files.base import ContentFile
import base64
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
# os.environ['WEASYPRINT_DLL_DIRECTORIES'] = r'C:\Program Files\GTK3-Runtime Win64\bin'
from weasyprint import HTML
from io import BytesIO
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError, PermissionDenied
from collections import defaultdict
import random
from dateutil.relativedelta import relativedelta
from usuarios.mixins import TenantRequiredMixin


def _get_secciones_valores(captacion):
    """
    Retorna una lista de tuplas (seccion, [(nombre_campo, valor), ...])
    para el formulario de captación dado.
    """
    secciones_dict = defaultdict(list)
    for valor in captacion.valores.select_related('campo__seccion').all():
        seccion = valor.campo.seccion
        # Formatea el valor según el tipo de campo
        if valor.campo.tipo == 'texto':
            val = valor.valor_texto
        elif valor.campo.tipo == 'numero':
            val = valor.valor_numero
        elif valor.campo.tipo == 'booleano':
            val = "Sí" if valor.valor_booleano else "No"
        else:
            val = ""
        secciones_dict[seccion].append((valor.campo.nombre, val))
    # Ordena las secciones por su campo 'orden'
    secciones = sorted(secciones_dict.keys(), key=lambda s: s.orden)
    return [(seccion, secciones_dict[seccion]) for seccion in secciones]

def numero_a_letras(num):
    unidades = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    especiales = ["", "once", "doce", "trece", "catorce", "quince"]
    decenas = ["", "diez", "veinte", "treinta"]
    if 10 < num < 16:
        return especiales[num-10]
    elif num == 10:
        return "diez"
    elif num == 20:
        return "veinte"
    elif num == 30:
        return "treinta"
    elif num < 10:
        return unidades[num]
    else:
        dec = num // 10
        uni = num % 10
        if dec == 2:
            return "veinti" + unidades[uni]
        else:
            if uni == 0:
                return decenas[dec]
            else:
                return decenas[dec] + " y " + unidades[uni]

def anio_a_letras(anio):
    # Solo para 2000 a 2099
    base = "dos mil"
    resto = anio - 2000
    if resto == 0:
        return base
    else:
        return base + " " + numero_a_letras(resto)

def meses_atras(fecha, n):
    return fecha - relativedelta(months=n)

@login_required
def home(request):
    
    captaciones_pendientes = FormularioCaptacion.objects.filter(is_firmado=False).order_by('-creado')[:5]
    entregas_pendientes = FormularioEntrega.objects.filter(is_firmado=False).order_by('-creado')[:5]

    now = timezone.now()
    meses_es = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
    nombre_mes = meses_es[now.month - 1]
    print(nombre_mes)

    captaciones_mes = FormularioCaptacion.objects.filter(
        creado__year=now.year, creado__month=now.month
    ).count()
    entregas_mes = FormularioEntrega.objects.filter(
        creado__year=now.year, creado__month=now.month
    ).count()

    # Lista de los últimos 6 meses
    meses = []
    captaciones_por_mes = []
    nombres_meses = []
    for i in range(5, -1, -1):  # 5 meses atrás hasta actual
        mes_fecha = meses_atras(now.replace(day=1), i)
        meses.append(mes_fecha)
        captaciones = FormularioCaptacion.objects.filter(
            creado__year=mes_fecha.year, creado__month=mes_fecha.month
        ).count()
        # Solo para pruebas:
        if captaciones == 0:
            captaciones = random.randint(1, 10)
        captaciones_por_mes.append(captaciones)
        nombres_meses.append(f"{meses_es[mes_fecha.month - 1].capitalize()} {mes_fecha.year}")

    estadisticas = {
    "total_propiedades": Propiedad.objects.count(),
    "total_clientes": Cliente.objects.count(),
    "captaciones_mes": captaciones_mes,
    "entregas_mes": entregas_mes,
    'nombre_mes': nombre_mes,
    }

    return render(
        request,
        'inventarioapp/home.html',
        {'section':'home',
            "estadisticas": estadisticas,
            'captaciones_pendientes': captaciones_pendientes,
            'entregas_pendientes': entregas_pendientes,
            'captaciones_labels': nombres_meses,   # ['Enero 2024', ..., 'Junio 2024']
            'captaciones_data': captaciones_por_mes,  # [4, 6, 3, 7, 8, 5]
        }
    )

''' 
A partir de este momento hacemos las vistas para manejar clientes. Estas se hacen
heredando de generic views.
'''

class ClienteBaseView(LoginRequiredMixin):
    section = 'clientes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = self.section
        return context

class CrearCliente(TenantRequiredMixin, ClienteBaseView, CreateView):
    model = Cliente
    fields = '__all__'
    success_url = reverse_lazy('inventarioapp:lista_clientes')
    template_name = "inventarioapp/clientes/form_cliente.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Oculta el campo inmobiliaria
        form.fields.pop('inmobiliaria', None)
        return form

    def form_valid(self, form):
        try:
            form.instance.inmobiliaria = self.request.user.profile.inmobiliaria
        except Exception:
            raise PermissionDenied("El usuario no tiene inmobiliaria asignada.")
        return super().form_valid(form)

    def form_valid(self, form):
        # asignar automáticamente la inmobiliaria del usuario
        try:
            form.instance.inmobiliaria = self.request.user.profile.inmobiliaria
        except Exception:
            raise PermissionDenied("El usuario no tiene inmobiliaria asignada.")
        return super().form_valid(form)

class ListaClientes(TenantRequiredMixin,ClienteBaseView, ListView):
    model = Cliente
    fields = '__all__'
    context_object_name = 'clientes'
    template_name = "inventarioapp/clientes/lista_clientes.html"
    paginate_by = 2

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) |
                Q(identificacion__icontains=query)
            )
        return queryset.order_by("nombre")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context

class ActualizarCliente(TenantRequiredMixin,ClienteBaseView, UpdateView):
    model = Cliente
    fields = '__all__'
    success_url = reverse_lazy('inventarioapp:lista_clientes')
    template_name = "inventarioapp/clientes/form_cliente.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Oculta el campo inmobiliaria
        form.fields.pop('inmobiliaria', None)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actualizar'] = True
        return context

class EliminarCliente(TenantRequiredMixin, ClienteBaseView, DeleteView):
    model = Cliente
    fields = '__all__'
    success_url = reverse_lazy('inventarioapp:lista_clientes')
    template_name = "inventarioapp/clientes/borrar_cliente.html"

class DetalleCliente(TenantRequiredMixin, ClienteBaseView, DetailView):
    model = Cliente
    fields = '__all__'
    success_url = reverse_lazy('inventarioapp:lista_clientes')
    template_name = "inventarioapp/clientes/detalle_cliente.html"

    

'''
A partir de esta linea se crearan las vistas para CRUD de propiedades
'''

class ListaPropiedades(LoginRequiredMixin,ListView):
    model = Propiedad
    fields = '__all__'
    context_object_name = 'propiedades'
    template_name = "inventarioapp/propiedades/lista_propiedades.html"
    paginate_by = 5   # Número de propiedades por página

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(direccion__icontains=query) |
                Q(ciudad__nombre__icontains=query) |  # si ciudad es FK a Ciudad
                Q(tipo_propiedad__tipo_propiedad__icontains=query) |
                Q(propiedadcliente__cliente__nombre__icontains=query)
            )
        return queryset.order_by("id").distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context

@login_required
def crear_propiedad(request):
    if request.method == 'POST':
        form = PropiedadForm(request.POST)
        if form.is_valid():
            propiedad = form.save()
            messages.success(request, "Propiedad creada exitosamente.")
            return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
        else:
            # Captura errores no de campos, sino generales (non_field_errors)
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = PropiedadForm()
    return render(request, 'inventarioapp/propiedades/form_propiedad.html', {
        'form': form,
        'section': 'propiedades',
    })

@login_required
def actualizar_propiedad(request, id):
    propiedad = get_object_or_404(Propiedad, id=id)
    if request.method == 'POST':
        form = PropiedadForm(request.POST, instance=propiedad)
        if form.is_valid():
            form.save()
            messages.success(request, "Propiedad actualizada exitosamente.")
            return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
        else:
            # Captura errores no de campos, sino generales (non_field_errors)
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = PropiedadForm(instance=propiedad)
    return render(request, 'core_inmobiliario/propiedades/form_propiedad.html', {
        'form': form,
        'actualizar': True,
        'propiedad': propiedad,
        'section': 'propiedades',
    })

# @login_required
# def agregar_relacion_propiedad(request, propiedad_id):
#     propiedad = get_object_or_404(Propiedad, id=propiedad_id)
#     if request.method == 'POST':
#         form = AgregarPropiedadClienteForm(request.POST, propiedad=propiedad)
#         if form.is_valid():
#             relacion = form.save(commit=False)
#             relacion.propiedad = propiedad
#             relacion.save()
#             messages.success(request, "Relación agregada correctamente.")
#             return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
#     else:
#         form = AgregarPropiedadClienteForm(propiedad=propiedad)
#     return render(request, 'inventarioapp/propiedades/agregar_relacion.html', {
#         'form': form,
#         'propiedad': propiedad,
#         'section': 'propiedades',
#     })


@login_required
def agregar_relacion_propiedad(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    if request.method == 'POST':
        form = AgregarPropiedadClienteForm(request.POST, propiedad=propiedad)
        
        # Asignamos la propiedad y la inmobiliaria a la instancia del formulario
        # ANTES de llamar a la validación.
        form.instance.propiedad = propiedad
        try:
            form.instance.inmobiliaria = request.user.profile.inmobiliaria
            print("Asignando inmobiliaria:", form.instance.inmobiliaria)
        except Exception:
            # Es una buena práctica manejar el caso en que el usuario no tenga
            # una inmobiliaria asociada.
            raise PermissionDenied("El usuario actual no tiene una inmobiliaria asignada.")

        if form.is_valid():
            print("Formulario válido:", form.cleaned_data)
            form.save()  # Ahora guardamos la instancia ya validada y completa.
            messages.success(request, "Relación agregada correctamente.")
            return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
    else:
        form = AgregarPropiedadClienteForm(propiedad=propiedad)
    
    return render(request, 'inventarioapp/propiedades/agregar_relacion.html', {
        'form': form,
        'propiedad': propiedad,
        'section': 'propiedades',
    })

def eliminar_relacion_propiedad(request, relacion_id):
    relacion = get_object_or_404(PropiedadCliente, id=relacion_id)
    propiedad_id = relacion.propiedad.id
    if request.method == 'POST':
        relacion.delete()
        messages.success(request, "Relación eliminada correctamente.")
    return redirect('core_inmobiliario:detalle_propiedad', id=propiedad_id)

@login_required
def detalle_propiedad(request, id):
    propiedad = get_object_or_404(Propiedad, id=id)
    # Relacionados a la propiedad
    relaciones = propiedad.propiedadcliente_set.all()
    captaciones = FormularioCaptacion.objects.filter(propiedad_cliente__in=relaciones)
    entregas = FormularioEntrega.objects.filter(propiedad_cliente__in=relaciones)
    puede_entregar = FormularioCaptacion.objects.filter(
        propiedad_cliente__propiedad=propiedad,
        is_firmado=True
    ).exists()
    return render(
        request,
        'inventarioapp/propiedades/detalle_propiedad_completo.html',
        {
            'propiedad': propiedad,
            'captaciones': captaciones,
            'entregas': entregas,
            'puede_entregar': puede_entregar,
            'section': 'propiedades',
        }
    )


'''
FORMULARIO DE ENTREGA
A partir de esta linea se hacen las vistas para la creación de formularios de entrega
'''

'''
La primera vista crea la relación entre cliente y propiedad.
'''
""" @login_required
def crear_formulario_entrega(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    if request.method == 'POST':
        form = SeleccionarPropiedadClienteForm(request.POST, propiedad=propiedad)
        if form.is_valid():
            cliente = form.cleaned_data['cliente']
            # Busca o crea la relación arrendatario-propiedad
            prop_cliente, created = PropiedadCliente.objects.get_or_create(
                cliente=cliente,
                propiedad=propiedad,
                relacion=PropiedadCliente.ARRENDATARIO
            )
            # Verifica si hay captación firmada
            captacion_firmada = FormularioCaptacion.objects.filter(
                propiedad_cliente__propiedad=propiedad,
                is_firmado=True
            ).exists()
            if not captacion_firmada:
                messages.error(
                    request,
                    "No se puede crear un formulario de entrega: no existe una captación firmada para esta propiedad."
                )
                return redirect('core_inmobiliario:detalle_propiedad', propiedad_id=propiedad.id)

            entrega = FormularioEntrega.objects.create(propiedad_cliente=prop_cliente)
            messages.success(request, "Formulario de entrega creado exitosamente.")
            return redirect('inventarioapp:agregar_ambiente', entrega_id=entrega.id)
    else:
        form = SeleccionarPropiedadClienteForm(propiedad=propiedad)
    return render(request, 'inventarioapp/entrega/crear_formulario_entrega.html', {'form': form, 'propiedad': propiedad}) """


# inventarioapp/views.py

@login_required
def crear_formulario_entrega(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    if request.method == 'POST':
        form = SeleccionarPropiedadClienteForm(request.POST, propiedad=propiedad)

        # --- TU SOLUCIÓN (¡CORRECTA!) ---
        # Asignamos los datos que faltan a la instancia del formulario ANTES de validar.
        try:
            form.instance.inmobiliaria = request.user.profile.inmobiliaria
            form.instance.propiedad = propiedad
            form.instance.relacion = PropiedadCliente.ARRENDATARIO
        except Exception:
            # Maneja el caso en que el usuario no tenga inmobiliaria
            raise PermissionDenied("El usuario no tiene una inmobiliaria asignada.")

        if form.is_valid():
            cliente = form.cleaned_data['cliente']
            
            # Ahora que la validación pasó, podemos usar get_or_create con seguridad.
            prop_cliente, created = PropiedadCliente.objects.get_or_create(
                cliente=cliente,
                propiedad=propiedad,
                relacion=PropiedadCliente.ARRENDATARIO,
                defaults={'inmobiliaria': request.user.profile.inmobiliaria}
            )

            # Verifica si hay captación firmada
            captacion_firmada = FormularioCaptacion.objects.filter(
                propiedad_cliente__propiedad=propiedad,
                is_firmado=True
            ).exists()
            if not captacion_firmada:
                messages.error(
                    request,
                    "No se puede crear un formulario de entrega: no existe una captación firmada para esta propiedad."
                )
                return redirect('inventarioapp:detalle_propiedad', id=propiedad.id)

            entrega = FormularioEntrega.objects.create(propiedad_cliente=prop_cliente)
            messages.success(request, "Formulario de entrega creado exitosamente.")
            return redirect('inventarioapp:agregar_ambiente', entrega_id=entrega.id)
    else:
        form = SeleccionarPropiedadClienteForm(propiedad=propiedad)
    return render(request, 'inventarioapp/entrega/crear_formulario_entrega.html', {'form': form, 'propiedad': propiedad})


'''
Esta vista permite agregar ambiente al formulario de entrega.
'''
@login_required
def agregar_ambiente(request, entrega_id):
    entrega = get_object_or_404(FormularioEntrega, id=entrega_id)

    if entrega.is_firmado:
        messages.error(request, "Este formulario ya fue firmado y no puede modificarse.")
        return redirect('inventarioapp:ver_pdf_formulario_entrega', entrega_id=entrega.id)

    if request.method == 'POST':
        form = AmbienteEntregaForm(request.POST)
        if form.is_valid():
            ambiente = form.save(commit=False)
            ambiente.formulario_entrega = entrega
            ambiente.save()
            return redirect('inventarioapp:agregar_ambiente', entrega_id=entrega.id)
    else:
        form = AmbienteEntregaForm()

    ambientes_existentes = entrega.ambientes.all()
    return render(request, 'inventarioapp/entrega/agregar_ambiente.html', {
        'form': form,
        'entrega': entrega,
        'ambientes': ambientes_existentes
    })


'''
Esta vista permite modificar los items de un ambiente de un formulario de entrega
'''
@login_required
def editar_items_ambiente(request, ambiente_id):
    ambiente = get_object_or_404(AmbienteEntrega, id=ambiente_id)

    if request.method == 'POST':
        import pprint
        pprint.pp(request.POST)
        formset = ItemEntregaFormSet(request.POST, instance=ambiente)
        if formset.is_valid():
            print("Cambios detectados en formularios:",[f.changed_data for f in formset.forms])
            formset.save()          # guarda nuevos y modifica existentes
            return redirect(
                'inventarioapp:agregar_ambiente',
                entrega_id=ambiente.formulario_entrega.id
            )
    else:
        formset = ItemEntregaFormSet(instance=ambiente)

    return render(request, 'inventarioapp/entrega/editar_items_ambiente.html', {
        'ambiente': ambiente,
        'formset': formset,
    })
# def editar_items_ambiente(request, ambiente_id):
#     ambiente = get_object_or_404(AmbienteEntrega, id=ambiente_id)
#     formset = ItemEntregaFormSet(queryset=ambiente.items.all())

#     if request.method == 'POST':
#         formset = ItemEntregaFormSet(request.POST, queryset=ambiente.items.all())
#         if formset.is_valid():
#             # Guarda sin commit para asignar FK
#             items = formset.save(commit=False)

#             # Asigna el ambiente a cada nuevo ítem
#             for item in items:
#                 if item.pk is None:       # solo los nuevos
#                     item.ambiente = ambiente
#                 item.save()

#             # Borra los que hayan sido marcados para eliminar (por si acaso)
#             for obj in formset.deleted_objects:
#                 obj.delete()

#             return redirect(
#                 'inventarioapp:agregar_ambiente',
#                 entrega_id=ambiente.formulario_entrega.id
#             )
#         else:
#             print(formset.errors)

#     return render(request, 'inventarioapp/entrega/editar_items_ambiente.html', {
#         'ambiente': ambiente,
#         'formset': formset,
#     })

'''
Esta vista permite ver el resumen de un formulario de entrega y firmarlo
'''
@login_required
def resumen_formulario_entrega(request, entrega_id):
    entrega = get_object_or_404(FormularioEntrega, id=entrega_id)
    inmobiliaria = request.user.profile.inmobiliaria

    if request.method == 'POST':
        firma_data = request.POST.get('firma_base64')
        try:
            if firma_data and not entrega.firma_cliente:
                format, imgstr = firma_data.split(';base64,') 
                entrega.firma_cliente.save(f'firma_{entrega.id}.png', ContentFile(base64.b64decode(imgstr)), save=True)
                entrega.is_firmado = True
                entrega.fecha_firma = timezone.now()
                entrega.save()
                firma_dir = os.path.join(settings.MEDIA_ROOT, 'firmas')
                os.makedirs(firma_dir, exist_ok=True)

                file_path = os.path.join(firma_dir, f'firma_{entrega_id}.png')
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(firma_data.split(',')[1]))
                # Por si querés mostrar la URL luego:
                firma_url = settings.MEDIA_URL + f'firmas/firma_{entrega_id}.png'
                messages.success(request, "Firma guardada exitosamente.")
            else:
                messages.error(request, "No se recibió firma válida o ya estaba firmada.")
        except Exception as e:
            messages.error(request, f"Error al guardar la firma: {e}")
        return redirect('inventarioapp:resumen_formulario_entrega', entrega_id=entrega_id)
    
    ambientes = entrega.ambientes.prefetch_related('items').all()
    return render(request, 'inventarioapp/entrega/resumen_formulario.html', {
        'entrega': entrega,
        'ambientes': ambientes,
        'inmobiliaria': inmobiliaria,
    })

'''
Función para envio de formulario en pdf por correo electrónico
'''
@login_required
def enviar_formulario_pdf(request, entrega_id):
    entrega = get_object_or_404(FormularioEntrega, id=entrega_id)
    ambientes = entrega.ambientes.prefetch_related('items').all()
    inmobiliaria = request.user.profile.inmobiliaria
    MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    nombre_mes = MESES[entrega.fecha_firma.month - 1]

    dia_letras = numero_a_letras(entrega.fecha_entrega.day).capitalize()
    anio_letras = anio_a_letras(entrega.fecha_entrega.year)

    html_string = render_to_string('inventarioapp/entrega/resumen_pdf.html', {
        'entrega': entrega,
        'ambientes': ambientes,
        'inmobiliaria': inmobiliaria,
        'nombre_mes': nombre_mes,
        'dia_letras': dia_letras,
        'anio_letras': anio_letras,
    })

    pdf_file = BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(target=pdf_file)

    email = EmailMessage(
        'Formulario de Entrega',
        'Adjunto encontrarás el PDF del inventario firmado.',
        'comercial2.stanza@gmail.com',
        [entrega.propiedad_cliente.cliente.email],
    )
    email.attach(f'formulario_entrega_{entrega_id}.pdf', pdf_file.getvalue(), 'application/pdf')
    email.send()

    propiedad = entrega.propiedad

    messages.success(request, "Formulario enviado por correo.")
    return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)


'''
Función para descargar el pdf una vez firmado.
'''
@login_required
def ver_pdf_formulario_entrega(request, entrega_id):
    entrega = get_object_or_404(FormularioEntrega, id=entrega_id)
    ambientes = entrega.ambientes.prefetch_related('items').all()

    html_string = render_to_string('inventarioapp/entrega/resumen_pdf.html', {
        'entrega': entrega,
        'ambientes': ambientes
    })

    pdf_file = BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(target=pdf_file)

    response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=formulario_entrega_{entrega_id}.pdf'
    return response


'''
Función que carga el formulario de entregas de una propiedad
'''
@login_required
def formularios_entrega_propiedad(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    entregas = FormularioEntrega.objects.filter(propiedad_cliente__propiedad=propiedad)
    return render(request, 'inventarioapp/entrega/lista_entregas.html', {
        'propiedad': propiedad,
        'entregas': entregas
    })

'''
Función para eliminar una entrega en borrador
'''
@login_required
def confirmar_eliminar_entrega(request, entrega_id):
    entrega = get_object_or_404(FormularioEntrega, id=entrega_id)
    propiedad_id = entrega.propiedad_cliente.propiedad.id
    if entrega.is_firmado:
        messages.error(request, "No se puede eliminar un formulario de entrega ya firmado.")
        return redirect('core_inmobiliario:detalle_propiedad', propiedad_id)
    
    if request.method == "POST":
        entrega.delete()
        messages.success(request, "Formulario de entrega en borrador eliminado exitosamente.")
        return redirect('core_inmobiliario:detalle_propiedad', propiedad_id)
    
    return render(request, 'inventarioapp/entrega/confirmar_eliminar_entrega.html', {
        'entrega': entrega,
        'propiedad': entrega.propiedad_cliente.propiedad
    })

'''
función para editar ambiente, el objetivo es editar el nombre del ambiente, esto lo permite hacer en la pantalla de agregar ambiente
'''
@login_required
def editar_ambiente(request, ambiente_id):
    ambiente = get_object_or_404(AmbienteEntrega, id=ambiente_id)
    entrega = ambiente.formulario_entrega

    if entrega.is_firmado:
        messages.error(request, "No se puede editar un ambiente en un formulario firmado.")
        return redirect('inventarioapp:agregar_ambiente', entrega_id=entrega.id)

    if request.method == 'POST':
        nuevo_nombre = request.POST.get('nombre')
        if nuevo_nombre:
            ambiente.nombre_personalizado = nuevo_nombre
            ambiente.save()
            messages.success(request, "Ambiente actualizado exitosamente.")
            return redirect('inventarioapp:agregar_ambiente', entrega_id=entrega.id)
        else:
            messages.error(request, "El nombre no puede estar vacío.")

    return render(request, 'inventarioapp/entrega/editar_ambiente.html', {'ambiente': ambiente})

'''
Función para eliminar ambiente, esta será llamada desde la vista de agregar ambiente
'''
@login_required
def eliminar_ambiente(request, ambiente_id):
    ambiente = get_object_or_404(AmbienteEntrega, id=ambiente_id)
    entrega = ambiente.formulario_entrega

    if entrega.is_firmado:
        messages.error(request, "No se puede eliminar un ambiente en un formulario firmado.")
        return redirect('inventarioapp:agregar_ambiente', entrega_id=entrega.id)

    if request.method == 'POST':
        ambiente.delete()
        messages.success(request, "Ambiente eliminado exitosamente.")
        return redirect('inventarioapp:agregar_ambiente', entrega_id=entrega.id)

    return render(request, 'inventarioapp/entrega/confirmar_eliminar_ambiente.html', {'ambiente': ambiente})

'''
Función de eliminar items de ambientes
'''
@login_required
def eliminar_item(request, item_id):
    item = get_object_or_404(ItemEntrega, id=item_id)
    ambiente = item.ambiente_entrega
    entrega = ambiente.formulario_entrega

    if entrega.is_firmado:
        messages.error(request, "No se puede eliminar un ítem de un formulario firmado.")
        return redirect('inventarioapp:editar_items_ambiente', ambiente_id=ambiente.id)

    if request.method == 'POST':
        item.delete()
        messages.success(request, "Ítem eliminado exitosamente.")
        return redirect('inventarioapp:editar_items_ambiente', ambiente_id=ambiente.id)

    return render(request, 'inventarioapp/entrega/confirmar_eliminar_item.html', {'item': item})

'''
Función para confirmar envío por correo electrónico del formulario de entrega
'''
@login_required
def confirmar_envio_correo(request, entrega_id):
    entrega = get_object_or_404(FormularioEntrega, id=entrega_id)
    cliente = entrega.propiedad_cliente.cliente

    if not entrega.is_firmado:
        messages.error(request, "El formulario debe estar firmado antes de enviarlo.")
        return redirect('inventarioapp:resumen_formulario_entrega', entrega_id=entrega.id)

    if request.method == 'POST':
        correo_ingresado = request.POST.get('correo')
        try:
            validate_email(correo_ingresado)
            cliente.email = correo_ingresado
            cliente.save()
            return redirect('inventarioapp:enviar_formulario_pdf', entrega_id=entrega.id)
        except ValidationError:
            messages.error(request, "Por favor, ingresa un correo electrónico válido.")

    return render(request, 'inventarioapp/entrega/confirmar_envio_correo.html', {
        'entrega': entrega,
        'cliente_email': cliente.email or ''
    })


'''
NUEVAS VISTAS MODELO DE CAPTACION
A partir de esta linea se implementa un nuevo modelo de inventario de captación
'''

'''
Función para vista que obtiene los clientes relacionados con una propiedad
'''
@login_required
def seleccionar_cliente_para_captacion(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    relaciones = PropiedadCliente.objects.filter(
        propiedad=propiedad,
        relacion__in=['PR', 'AP']
    )
    # Si NO hay relaciones válidas para captación, redirige y muestra mensaje
    if not relaciones.exists():
        messages.warning(
            request,
            "Debes asociar primero un propietario o apoderado a esta propiedad para poder crear una captación."
        )
        return redirect('inventarioapp:agregar_relacion_propiedad', propiedad_id=propiedad.id)
    
    if request.method == 'POST':
        relacion_id = request.POST.get('relacion_id')
        return redirect('inventarioapp:formulario_captacion', relacion_id=relacion_id)
    return render(request, 'inventarioapp/captacion/seleccionar_cliente_captacion.html', {
        'propiedad': propiedad,
        'relaciones': relaciones,
    })

'''
Función para crear el formulario de captación dínamico según lo guardado en CampoCaptacion y SeccionCaptacion
'''
@login_required
def formulario_captacion_dinamico(request, relacion_id):
    relacion = get_object_or_404(PropiedadCliente, id=relacion_id)
    if request.method == 'POST':
        form = FormularioCaptacionDinamico(request.POST)
        if form.is_valid():
            # 1. Guardar el formulario de captación con los campos de modelo
            captacion = form.save(commit=False)
            captacion.propiedad_cliente = relacion
            captacion.creado = timezone.now()
            captacion.save()
            # 2. Guardar cada campo
            for key, value in form.cleaned_data.items():
                if key.startswith('campo_'):
                    campo_id = int(key.replace('campo_', ''))
                    campo = CampoCaptacion.objects.get(id=campo_id)
                    if campo.tipo == 'texto':
                        ValorCampoCaptacion.objects.create(
                            formulario=captacion,
                            campo=campo,
                            valor_texto=value
                        )
                    elif campo.tipo == 'numero':
                        ValorCampoCaptacion.objects.create(
                            formulario=captacion,
                            campo=campo,
                            valor_numero=value
                        )
                    elif campo.tipo == 'booleano':
                        ValorCampoCaptacion.objects.create(
                            formulario=captacion,
                            campo=campo,
                            valor_booleano=value
                        )
            # 3. Redirigir a una vista de éxito, detalle, o lo que prefieras
            propiedad_id = captacion.propiedad_cliente.propiedad.id
            return redirect('core_inmobiliario:detalle_propiedad', id=propiedad_id)
    else:
        form = FormularioCaptacionDinamico()
    secciones_fields = []
    for seccion in form.secciones:
        campos = [form[field_name] for field_name in seccion['campos']]
        secciones_fields.append({'nombre': seccion['nombre'], 'campos': campos})

    return render(request, 'inventarioapp/captacion/formulario_captacion_dinamico.html', {
        'form': form,
        'relacion': relacion,
        'secciones_fields': secciones_fields,
    })

'''
Función para vista de resumen de formulario de captación
'''
@login_required
def resumen_formulario_captacion(request, captacion_id):
    captacion = get_object_or_404(FormularioCaptacion, id=captacion_id)
    inmobiliaria = request.user.profile.inmobiliaria

    if request.method == 'POST':
        firma_data = request.POST.get('firma_base64')
        try:
            if firma_data and not captacion.firma_cliente:
                format, imgstr = firma_data.split(';base64,')
                captacion.firma_cliente.save(f'firma_captacion_{captacion.id}.png', ContentFile(base64.b64decode(imgstr)), save=True)
                captacion.is_firmado = True
                captacion.fecha_firma = timezone.now()
                captacion.save()
                firma_dir = os.path.join(settings.MEDIA_ROOT, 'firmas_captacion')
                os.makedirs(firma_dir, exist_ok=True)
                file_path = os.path.join(firma_dir, f'firma_captacion_{captacion_id}.png')
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(imgstr))
                firma_url = settings.MEDIA_URL + f'firmas_captacion/firma_captacion_{captacion_id}.png'
                messages.success(request, "Firma guardada exitosamente.")
            else:
                messages.error(request, "No se recibió firma válida o ya estaba firmada.")
        except Exception as e:
            messages.error(request, f"Error al guardar la firma: {e}")
        return redirect('inventarioapp:resumen_formulario_captacion', captacion_id=captacion_id)

    secciones_valores = _get_secciones_valores(captacion)

    return render(request, 'inventarioapp/captacion/resumen_formulario_captacion.html', {
        'captacion': captacion,
        'secciones_valores': secciones_valores,
        'inmobiliaria': inmobiliaria,
    })

'''
Función para envio de formulario de captación por correo electrónico, en pdf
'''
@login_required
def enviar_formulario_captacion(request, captacion_id):
    captacion = get_object_or_404(FormularioCaptacion, id=captacion_id)
    propiedad_id = captacion.propiedad_cliente.propiedad.id
    cliente = captacion.cliente
    cliente_email = cliente.email
    inmobiliaria = request.user.profile.inmobiliaria
    MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    nombre_mes = MESES[captacion.fecha.month - 1]
    dia_letras = numero_a_letras(captacion.fecha_firma.day).capitalize()
    anio_letras = anio_a_letras(captacion.fecha_firma.year)

    if request.method == 'POST':
        correo = request.POST.get('correo')
        # Render HTML del PDF
        html_string = render_to_string('inventarioapp/captacion/resumen_pdf_captacion.html', {
            'captacion': captacion,
            # Pasa también las secciones/campos si los usas en el PDF:
            'secciones_valores': _get_secciones_valores(captacion),
            'inmobiliaria': inmobiliaria,
            'nombre_mes': nombre_mes,
            'dia_letras': dia_letras,
            'anio_letras': anio_letras,
        })
        pdf_file = BytesIO()
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(target=pdf_file)

        email = EmailMessage(
            'Formulario de Captación Firmado',
            'Adjunto encontrarás el PDF del formulario de captación firmado.',
            'comercial2.stanza@gmail.com',  # Cambia si quieres
            [correo],
        )
        email.attach(f'formulario_captacion_{captacion.id}.pdf', pdf_file.getvalue(), 'application/pdf')
        email.send()
        messages.success(request, "Formulario enviado por correo.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad_id)

    return render(request, 'inventarioapp/captacion/confirmar_envio_captacion.html', {
        'captacion': captacion,
        'cliente_email': cliente_email,
        'inmobiliaria': inmobiliaria,
        'nombre_mes': nombre_mes,
    })


'''
Función de eliminar captación en borrador
'''
@login_required
def eliminar_captacion(request, captacion_id):
    captacion = get_object_or_404(FormularioCaptacion, id=captacion_id)
    propiedad_id = captacion.propiedad_cliente.propiedad.id

    if captacion.is_firmado:
        messages.error(request, "No se puede eliminar una captación ya firmada.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad_id)

    if request.method == 'POST':
        captacion.delete()
        messages.success(request, "Captación eliminada correctamente.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad_id)

    return render(request, 'inventarioapp/captacion/confirmar_eliminar_captacion.html', {
        'captacion': captacion,
        'propiedad_id': propiedad_id,
    })

'''
Función que permite editar un formulario de captación, utiliza el mismo Formulario para crear la captación
'''
@login_required
def editar_captacion(request, captacion_id):
    captacion = get_object_or_404(FormularioCaptacion, id=captacion_id)
    # Prepara initial para los campos dinámicos
    initial = {}
    # Carga valores de los campos dinámicos guardados
    for valor in captacion.valores.all():  # Asegúrate de tener related_name='valores' en ValorCampoCaptacion
        field_name = f'campo_{valor.campo.id}'
        if valor.campo.tipo == 'texto':
            initial[field_name] = valor.valor_texto
        elif valor.campo.tipo == 'numero':
            initial[field_name] = valor.valor_numero
        elif valor.campo.tipo == 'booleano':
            initial[field_name] = valor.valor_booleano

    if request.method == 'POST':
        form = FormularioCaptacionDinamico(request.POST, instance=captacion)
        # Los campos dinámicos toman sus valores de request.POST directamente
        if form.is_valid():
            captacion = form.save()
            # Actualiza campos dinámicos
            for key, value in form.cleaned_data.items():
                if key.startswith('campo_'):
                    campo_id = int(key.replace('campo_', ''))
                    campo = CampoCaptacion.objects.get(id=campo_id)
                    valor_obj, created = ValorCampoCaptacion.objects.get_or_create(
                        formulario=captacion,
                        campo=campo,
                    )
                    if campo.tipo == 'texto':
                        valor_obj.valor_texto = value
                    elif campo.tipo == 'numero':
                        valor_obj.valor_numero = value
                    elif campo.tipo == 'booleano':
                        valor_obj.valor_booleano = value
                    valor_obj.save()
            return redirect('core_inmobiliario:detalle_propiedad', id=captacion.propiedad_cliente.propiedad.id)
    else:
        # Instancia del model, initial para los dinámicos
        form = FormularioCaptacionDinamico(instance=captacion, initial=initial)

    secciones_fields = []
    for seccion in form.secciones:
        campos = [form[field_name] for field_name in seccion['campos']]
        secciones_fields.append({'nombre': seccion['nombre'], 'campos': campos})

    return render(request, 'inventarioapp/captacion/formulario_captacion_dinamico.html', {
        'form': form,
        'relacion': captacion.propiedad_cliente,
        'modo_edicion': True,
        'secciones_fields': secciones_fields,
    })


