from django.shortcuts import render
from django.shortcuts import render,get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import *
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .forms import *
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from usuarios.mixins import TenantRequiredMixin
from inventarioapp.models import *




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

class DetalleCliente(TenantRequiredMixin, ClienteBaseView, DetailView):
    model = Cliente
    fields = '__all__'
    success_url = reverse_lazy('core_inmobiliario:lista_clientes')
    template_name = "core_inmobiliario/clientes/detalle_cliente.html"

    

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
        form.instance.inmobiliaria = request.user.profile.inmobiliaria
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
    return render(request, 'core_inmobiliario/propiedades/form_propiedad.html', {
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

@login_required
def agregar_relacion_propiedad(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    if request.method == 'POST':
        form = AgregarPropiedadClienteForm(request.POST, propiedad=propiedad)
        if form.is_valid():
            relacion = form.save(commit=False)
            relacion.propiedad = propiedad
            relacion.save()
            messages.success(request, "Relación agregada correctamente.")
            return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
    else:
        form = AgregarPropiedadClienteForm(propiedad=propiedad)
    return render(request, 'core_inmobiliario/propiedades/agregar_relacion.html', {
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
        'core_inmobiliario/propiedades/detalle_propiedad_completo.html',
        {
            'propiedad': propiedad,
            'captaciones': captaciones,
            'entregas': entregas,
            'puede_entregar': puede_entregar,
            'section': 'propiedades',
        }
    )

