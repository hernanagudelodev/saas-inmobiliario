from django.shortcuts import render
from django.shortcuts import render,get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import *
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from .forms import *
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from usuarios.mixins import TenantRequiredMixin
from inventarioapp.models import *
from gestion_arriendos.models import ContratoMandato, ContratoArrendamiento
from django.http import HttpResponseRedirect # Necesario para redirigir en POST



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
    success_url = reverse_lazy('core_inmobiliario:lista_clientes')
    template_name = "core_inmobiliario/clientes/form_cliente.html"

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
    template_name = "core_inmobiliario/clientes/lista_clientes.html"
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
    success_url = reverse_lazy('core_inmobiliario:lista_clientes')
    template_name = "core_inmobiliario/clientes/form_cliente.html"

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
    success_url = reverse_lazy('core_inmobiliario:lista_clientes')
    template_name = "core_inmobiliario/clientes/borrar_cliente.html"

class DetalleCliente(TenantRequiredMixin, ClienteBaseView, DetailView): # Mantén tus mixins
    model = Cliente
    # fields = '__all__' # Ya no se necesita si usas template_name
    # success_url = reverse_lazy('core_inmobiliario:lista_clientes') # No aplica directamente aquí
    template_name = "core_inmobiliario/clientes/detalle_cliente.html"
    context_object_name = 'cliente' # Define el nombre del objeto cliente en la plantilla

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.get_object() # Obtiene el cliente actual
        # Añade la lista de cuentas bancarias del cliente
        context['cuentas_bancarias'] = cliente.cuentas_bancarias.all()
        # Añade una instancia vacía del formulario para crear nuevas cuentas
        # Solo añade el formulario si no viene uno con errores del método POST
        if 'cuenta_form' not in context:
            context['cuenta_form'] = CuentaBancariaForm()
        return context

    def post(self, request, *args, **kwargs):
        # Necesitamos obtener el cliente al que pertenece esta vista de detalle
        self.object = self.get_object()
        # Creamos una instancia del formulario con los datos del POST
        form = CuentaBancariaForm(request.POST)

        if form.is_valid():
            # Creamos la cuenta pero no la guardamos aún (commit=False)
            nueva_cuenta = form.save(commit=False)
            # Asignamos el cliente actual a la nueva cuenta
            nueva_cuenta.cliente = self.object
            # Ahora sí guardamos la cuenta en la base de datos
            nueva_cuenta.save()
            messages.success(request, "Cuenta bancaria agregada exitosamente.")
            # Redirigimos a la misma página de detalle del cliente (GET request)
            return HttpResponseRedirect(reverse('core_inmobiliario:detalle_cliente', kwargs={'pk': self.object.pk}))
        else:
            # Si el formulario no es válido, volvemos a renderizar la página
            # pero esta vez pasamos el formulario con los errores.
            # Usamos get_context_data para obtener el contexto base (detalles del cliente, etc.)
            context = self.get_context_data(object=self.object)
            # Añadimos el formulario inválido al contexto para mostrar los errores
            context['cuenta_form'] = form
            # Renderizamos la plantilla con el contexto actualizado
            return self.render_to_response(context)

    

'''
A partir de esta linea se crearan las vistas para CRUD de propiedades
'''

class ListaPropiedades(TenantRequiredMixin,LoginRequiredMixin,ListView):
    model = Propiedad
    fields = '__all__'
    context_object_name = 'propiedades'
    template_name = "core_inmobiliario/propiedades/lista_propiedades.html"
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
        # Ahora form.is_valid() funcionará, porque excluimos 'inmobiliaria' de su validación.
        if form.is_valid():
            # Creamos el objeto en memoria, sin enviarlo aún a la base de datos.
            propiedad = form.save(commit=False)
            try:
                # Asignamos la inmobiliaria del usuario actual.
                propiedad.inmobiliaria = request.user.profile.inmobiliaria
            except Exception:
                raise PermissionDenied("El usuario no tiene una inmobiliaria asignada.")
            
            # Ahora sí, guardamos el objeto completo en la base de datos.
            propiedad.save()
            
            messages.success(request, "Propiedad creada exitosamente.")
            return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
        else:
            # Captura errores no de campos, sino generales (non_field_errors)
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = PropiedadForm()
    return render(request, 'core_inmobiliario/propiedades/form_propiedad.html', {
        'form': form,
        'section': 'propiedades',
    })

@login_required
def actualizar_propiedad(request, id):
    propiedad = get_object_or_404(Propiedad, id=id, inmobiliaria=request.user.profile.inmobiliaria)
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
        except Exception:
            # Es una buena práctica manejar el caso en que el usuario no tenga
            # una inmobiliaria asociada.
            raise PermissionDenied("El usuario actual no tiene una inmobiliaria asignada.")

        if form.is_valid():
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
    # Obtenemos la propiedad, asegurándonos de que pertenece a la inmobiliaria del usuario
    propiedad = get_object_or_404(Propiedad, id=id, inmobiliaria=request.user.profile.inmobiliaria)
    
    # --- LÓGICA DEL PANEL DE CONTROL ---
    
    # 1. Etapa de Captación: Buscamos la última captación firmada
    captacion_firmada = FormularioCaptacion.objects.filter(
        propiedad_cliente__propiedad=propiedad,
        is_firmado=True
    ).order_by('-fecha_firma').first()

    # --- Buscar captaciones pendientes ---
    captaciones_pendientes = FormularioCaptacion.objects.filter(
        propiedad_cliente__propiedad=propiedad,
        is_firmado=False # <-- Buscar las NO firmadas
    ).order_by('-creado') # Ordenar por fecha de creación, más reciente primero
    # ----------------------------------------

    # 2. Etapa de Contratación: Buscamos los contratos asociados a esta propiedad
    contrato_mandato = ContratoMandato.objects.filter(propiedad=propiedad).first()
    contrato_arrendamiento = ContratoArrendamiento.objects.filter(propiedad=propiedad).first() # Asumimos uno por ahora

    # 3. Etapa de Entrega: Buscamos los inventarios de entrega
    entrega_firmada = FormularioEntrega.objects.filter(
        propiedad_cliente__propiedad=propiedad,
        is_firmado=True
    ).order_by('-fecha_firma').first()

    # Obtenemos todas las relaciones cliente-propiedad para listarlas
    relaciones_clientes = propiedad.propiedadcliente_set.all()

    # Preparamos el contexto para enviarlo a la plantilla
    context = {
        'propiedad': propiedad,
        'captacion_firmada': captacion_firmada,
        'contrato_mandato': contrato_mandato,
        'captaciones_pendientes': captaciones_pendientes, # <-- Pasar las pendientes
        'contrato_arrendamiento': contrato_arrendamiento,
        'entrega_firmada': entrega_firmada,
        'relaciones_clientes': relaciones_clientes, # <-- Pasamos la lista al contexto
        'section': 'propiedades', # Para mantener el menú lateral activo
    }
    
    return render(request, 'core_inmobiliario/propiedades/detalle_propiedad_completo.html', context)

""" @login_required
def detalle_propiedad(request, id):
    propiedad = get_object_or_404(Propiedad, id=id, inmobiliaria=request.user.profile.inmobiliaria)
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
        'core_inmobiliario/propiedades/detalle_propiedad_completo.html',
        {
            'propiedad': propiedad,
            'captaciones': captaciones,
            'entregas': entregas,
            'puede_entregar': puede_entregar,
            'section': 'propiedades',
        }
    ) """

