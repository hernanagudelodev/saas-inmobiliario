from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.template import Context, Template, engines
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from core_inmobiliario.models import Propiedad, PropiedadCliente
from inventarioapp.models import FormularioCaptacion
from .models import ContratoMandato, PlantillaContrato, ContratoArrendamiento, VigenciaContrato
from usuarios.mixins import TenantRequiredMixin
from .forms import ContratoMandatoForm, PlantillaContratoForm,ContratoArrendamientoForm, SubirArrendamientoFirmadoForm, SubirMandatoFirmadoForm,RegistrarContratoExistenteForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.core.files.base import ContentFile

from django.views.decorators.clickjacking import xframe_options_sameorigin

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
    
#--- Vistas para Contrato de Mandato ---

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
        # CORRECCIÓN: Ahora pasamos 'propietario' también en el POST
        form = ContratoMandatoForm(request.POST, inmobiliaria=inmobiliaria, propietario=propietario)
        if form.is_valid():
            contrato = form.save(commit=False)
            contrato.propiedad = propiedad
            contrato.propietario = propietario
            contrato.inmobiliaria = inmobiliaria
            contrato.save()
            
            messages.success(request, "Borrador del Contrato de Mandato creado exitosamente.")
            return redirect('gestion_arriendos:detalle_contrato_mandato', pk=contrato.pk)
    else:
        # CORRECCIÓN: Pasamos 'propietario' al constructor y eliminamos la línea manual
        form = ContratoMandatoForm(inmobiliaria=inmobiliaria, propietario=propietario)

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
        # La vista ahora es mucho más simple, solo añade la sección para el menú
        context = super().get_context_data(**kwargs)
        context['section'] = 'arriendos'
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
        'cuerpo_renderizado': clausulas_renderizadas,
        'titulo_contrato': plantilla_obj.titulo
    }
    texto_renderizado = render_to_string('gestion_arriendos/base_contrato_pdf.html', contexto_final)
    
    contrato.texto_final_renderizado = texto_renderizado
    contrato.estado = 'FINALIZADO'
    contrato.save()

    messages.success(request, "El contrato ha sido finalizado y está listo para ser firmado.")
    return redirect('gestion_arriendos:detalle_contrato_mandato', pk=contrato.id)

@xframe_options_sameorigin # Este decorador permite que la vista se muestre en un iframe
@login_required
def descargar_borrador_contrato_mandato(request, contrato_id):
    """
    Genera y sirve un PDF del borrador del contrato con una marca de agua.
    """
    contrato = get_object_or_404(ContratoMandato, id=contrato_id, inmobiliaria=request.user.profile.inmobiliaria)

    # Solo generamos el borrador si el contrato está en ese estado
    if contrato.estado != 'BORRADOR':
        messages.error(request, "Este contrato ya no es un borrador y no se puede descargar de esta forma.")
        return redirect('gestion_arriendos:detalle_contrato_mandato', pk=contrato.id)

    # Reutilizamos la misma lógica de renderizado que en la vista de detalle
    plantilla_obj = contrato.plantilla_usada
    template_string = "{% load letras_numeros %}" + plantilla_obj.cuerpo_texto
    
    contexto_render = {
        "propietario": contrato.propietario,
        "propiedad": contrato.propiedad,
        "inmobiliaria": contrato.inmobiliaria,
        "contrato": contrato
    }
    
    template = engines['django'].from_string(template_string)
    clausulas_renderizadas = template.render(contexto_render)

    # Renderizamos la plantilla maestra, pasando la variable para la marca de agua
    contexto_final = {
        'inmobiliaria': contrato.inmobiliaria,
        'cuerpo_renderizado': clausulas_renderizadas,
        'titulo_contrato': plantilla_obj.titulo, 
        'es_borrador': True  # <-- ¡La clave para la marca de agua!
    }
    html_string = render_to_string('gestion_arriendos/base_contrato_pdf.html', contexto_final)

    # Creamos el PDF en memoria
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    # Creamos la respuesta HTTP para servir el archivo
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Borrador_Contrato_{contrato.id}.pdf"'
    
    return response

@login_required
def editar_contrato_mandato(request, pk):
    """
    Permite editar un Contrato de Mandato que está en estado Borrador.
    """
    mandato = get_object_or_404(ContratoMandato, pk=pk, inmobiliaria=request.user.profile.inmobiliaria)

    # Validación: Solo se puede editar si está en estado Borrador
    if mandato.estado != 'BORRADOR':
        messages.error(request, "Este contrato no se puede editar porque ya no está en estado 'Borrador'.")
        return redirect('gestion_arriendos:detalle_contrato_mandato', pk=mandato.pk)

    if request.method == 'POST':
        form = ContratoMandatoForm(request.POST, instance=mandato, inmobiliaria=mandato.inmobiliaria, propietario=mandato.propietario)
        if form.is_valid():
            form.save()
            messages.success(request, "El Contrato de Mandato ha sido actualizado exitosamente.")
            return redirect('gestion_arriendos:detalle_contrato_mandato', pk=mandato.pk)
    else:
        form = ContratoMandatoForm(instance=mandato, inmobiliaria=mandato.inmobiliaria, propietario=mandato.propietario)

    context = {
        'form': form,
        'propiedad': mandato.propiedad,
        'propietario': mandato.propietario,
        'modo_edicion': True, # Para cambiar el título y el botón en la plantilla
        'section': 'arriendos'
    }
    # Reutilizamos la plantilla de creación
    return render(request, 'gestion_arriendos/crear_contrato_mandato.html', context)

# --- VISTA DE ELIMINACIÓN PARA CONTRATO DE MANDATO ---


@login_required
def eliminar_contrato_mandato(request, pk):
    """
    Muestra una confirmación y elimina un Contrato de Mandato en estado Borrador.
    """
    mandato = get_object_or_404(ContratoMandato, pk=pk, inmobiliaria=request.user.profile.inmobiliaria)
    propiedad_id = mandato.propiedad.id

    # La validación del estado "Borrador" la dejamos aquí para proteger el acceso
    if mandato.estado != 'BORRADOR':
        messages.error(request, "Este contrato no se puede eliminar porque ya no es un borrador.")
        return redirect('gestion_arriendos:detalle_contrato_mandato', pk=mandato.pk)

    if request.method == 'POST':
        # --- VALIDACIÓN MOVIDA AQUÍ ---
        # Ahora, solo validamos la dependencia ANTES de borrar, en el POST.
        if mandato.contratos_arrendamiento.exists():
            messages.error(
                request, 
                "No se puede eliminar este Contrato de Mandato porque ya tiene un Contrato de Arrendamiento asociado. "
                "Utilice la opción 'Eliminar Proceso en Borrador' desde el panel de la propiedad."
            )
            # Redirigimos de vuelta al detalle del mandato, donde se mostrará el error.
            return redirect('gestion_arriendos:detalle_contrato_mandato', pk=mandato.pk)
        # ------------------------------------

        mandato.delete()
        messages.success(request, "El borrador del contrato ha sido eliminado exitosamente.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad_id)

    context = {
        'contrato': mandato
    }
    # Si la petición es GET, ahora siempre se mostrará la página de confirmación
    return render(request, 'gestion_arriendos/confirmar_eliminar_contrato.html', context)

#--- Vista para eliminar todo el proceso en borrador (mandato + arrendamiento) ---

@login_required
def eliminar_proceso_borrador(request, propiedad_id):
    """
    Muestra una confirmación y elimina todos los contratos en estado 'Borrador'
    asociados a una propiedad.
    """
    propiedad = get_object_or_404(Propiedad, id=propiedad_id, inmobiliaria=request.user.profile.inmobiliaria)
    
    # Buscamos los contratos en borrador para mostrarlos en la confirmación
    mandato_borrador = ContratoMandato.objects.filter(propiedad=propiedad, estado='BORRADOR').first()
    arrendamiento_borrador = ContratoArrendamiento.objects.filter(propiedad=propiedad, estado='BORRADOR').first()

    # Si no hay nada que borrar, redirigimos con un mensaje.
    if not mandato_borrador and not arrendamiento_borrador:
        messages.warning(request, "No hay ningún proceso en borrador para eliminar.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)

    if request.method == 'POST':
        if mandato_borrador:
            mandato_borrador.delete()
        if arrendamiento_borrador:
            arrendamiento_borrador.delete()
        
        messages.success(request, "El proceso de arrendamiento en borrador ha sido eliminado exitosamente.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)

    context = {
        'propiedad': propiedad,
        'mandato': mandato_borrador,
        'arrendamiento': arrendamiento_borrador,
    }
    return render(request, 'gestion_arriendos/confirmar_eliminar_proceso.html', context)

# --- Vistas para Contrato de Arrendamiento ---


@login_required
def crear_contrato_arrendamiento(request, mandato_id):
    """
    Crea un Contrato de Arrendamiento y lo asocia a un Contrato de Mandato existente.
    """
    # Obtenemos el contexto necesario: el mandato, la propiedad y la inmobiliaria
    mandato = get_object_or_404(ContratoMandato, id=mandato_id, inmobiliaria=request.user.profile.inmobiliaria)
    propiedad = mandato.propiedad
    inmobiliaria = request.user.profile.inmobiliaria

    if request.method == 'POST':
        # Al instanciar el formulario, le pasamos los datos del POST y el contexto
        form = ContratoArrendamientoForm(request.POST, inmobiliaria=inmobiliaria, propiedad=propiedad)
        if form.is_valid():
            # Creamos el objeto en memoria sin guardarlo aún en la BD
            arrendamiento = form.save(commit=False)
            
            # Asignamos las relaciones que no vienen del formulario
            arrendamiento.contrato_mandato = mandato
            arrendamiento.propiedad = propiedad
            arrendamiento.inmobiliaria = inmobiliaria
            
            # Guardamos el objeto principal en la base de datos
            arrendamiento.save()
            
            # MUY IMPORTANTE: Guardamos las relaciones "Muchos a Muchos" (codeudores)
            form.save_m2m()

            # --- NUEVA LÓGICA PARA CREAR LA PRIMERA VIGENCIA ---
            VigenciaContrato.objects.create(
                contrato_arrendamiento=arrendamiento,
                tipo='INICIAL',
                fecha_inicio=form.cleaned_data['fecha_inicio'],
                fecha_fin=form.cleaned_data['fecha_fin'],
                valor_canon=form.cleaned_data['valor_canon']
            )
            # ----------------------------------------------------
            
            messages.success(request, "Contrato de Arrendamiento creado exitosamente en estado Borrador.")
            # Redirigimos de vuelta al panel de control de la propiedad
            return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
    else:
        # Si es una petición GET, creamos un formulario vacío, pasándole el contexto
        form = ContratoArrendamientoForm(inmobiliaria=inmobiliaria, propiedad=propiedad)

    context = {
        'form': form,
        'mandato': mandato,
        'propiedad': propiedad,
        'section': 'arriendos'
    }
    return render(request, 'gestion_arriendos/crear_contrato_arrendamiento.html', context)

# --- VISTA DE EDICIÓN PARA CONTRATO DE ARRENDAMIENTO ---

@login_required
def editar_contrato_arrendamiento(request, pk):
    """
    Permite editar un Contrato de Arrendamiento y su primera vigencia
    mientras está en estado Borrador.
    """
    arrendamiento = get_object_or_404(ContratoArrendamiento, pk=pk, inmobiliaria=request.user.profile.inmobiliaria)
    primera_vigencia = arrendamiento.vigencias.first()

    # Validación: Solo se puede editar si está en estado Borrador
    if arrendamiento.estado != 'BORRADOR':
        messages.error(request, "Este contrato no se puede editar porque ya no está en estado 'Borrador'.")
        return redirect('gestion_arriendos:detalle_contrato_arrendamiento', pk=arrendamiento.pk)

    if request.method == 'POST':
        form = ContratoArrendamientoForm(request.POST, instance=arrendamiento, inmobiliaria=arrendamiento.inmobiliaria, propiedad=arrendamiento.propiedad)
        if form.is_valid():
            # Guardamos los cambios del contrato y sus codeudores
            form.save() 
            
            # Actualizamos los datos de la primera vigencia
            if primera_vigencia:
                primera_vigencia.valor_canon = form.cleaned_data['valor_canon']
                primera_vigencia.fecha_inicio = form.cleaned_data['fecha_inicio']
                primera_vigencia.fecha_fin = form.cleaned_data['fecha_fin']
                primera_vigencia.save()

            messages.success(request, "El Contrato de Arrendamiento ha sido actualizado exitosamente.")
            return redirect('gestion_arriendos:detalle_contrato_arrendamiento', pk=arrendamiento.pk)
    else:
        # Pre-poblamos el formulario con los datos de la vigencia
        initial_data = {
            'valor_canon': primera_vigencia.valor_canon if primera_vigencia else None,
            'fecha_inicio': primera_vigencia.fecha_inicio if primera_vigencia else None,
            'fecha_fin': primera_vigencia.fecha_fin if primera_vigencia else None,
        }
        form = ContratoArrendamientoForm(instance=arrendamiento, initial=initial_data, inmobiliaria=arrendamiento.inmobiliaria, propiedad=arrendamiento.propiedad)

    context = {
        'form': form,
        'propiedad': arrendamiento.propiedad,
        'modo_edicion': True,
        'section': 'arriendos'
    }
    # Reutilizamos la plantilla de creación
    return render(request, 'gestion_arriendos/crear_contrato_arrendamiento.html', context)

# --- VISTA DE DETALLE PARA CONTRATO DE ARRENDAMIENTO ---

class DetalleContratoArrendamiento(LoginRequiredMixin, TenantRequiredMixin, DetailView):
    model = ContratoArrendamiento
    template_name = 'gestion_arriendos/detalle_contrato_arrendamiento.html'
    context_object_name = 'contrato'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'arriendos'
        return context

# --- VISTA DE DESCARGA PARA BORRADOR DE ARRENDAMIENTO ---
@xframe_options_sameorigin
@login_required
def descargar_borrador_contrato_arrendamiento(request, contrato_id):
    contrato = get_object_or_404(ContratoArrendamiento, id=contrato_id, inmobiliaria=request.user.profile.inmobiliaria)

    if contrato.estado != 'BORRADOR':
        messages.error(request, "Este contrato ya no es un borrador.")
        return redirect('gestion_arriendos:detalle_contrato_arrendamiento', pk=contrato.id)

    plantilla_obj = contrato.plantilla_usada
    template_string = "{% load letras_numeros %}" + plantilla_obj.cuerpo_texto
    
    contexto_render = {
        "propietario": contrato.contrato_mandato.propietario,
        "arrendatario": contrato.arrendatario,
        "propiedad": contrato.propiedad,
        "inmobiliaria": contrato.inmobiliaria,
        "contrato": contrato
    }
    
    template = engines['django'].from_string(template_string)
    clausulas_renderizadas = template.render(contexto_render)

    contexto_final = {
        'inmobiliaria': contrato.inmobiliaria,
        'cuerpo_renderizado': clausulas_renderizadas,
        'titulo_contrato': plantilla_obj.titulo,
        'es_borrador': True
    }
    html_string = render_to_string('gestion_arriendos/base_contrato_pdf.html', contexto_final)

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Borrador_Contrato_Arrendamiento_{contrato.id}.pdf"'
    
    return response

# --- VISTA DE ELIMINACIÓN PARA CONTRATO DE ARRENDAMIENTO ---

@login_required
def eliminar_contrato_arrendamiento(request, pk):
    """
    Muestra una confirmación y elimina un Contrato de Arrendamiento en estado Borrador.
    """
    arrendamiento = get_object_or_404(ContratoArrendamiento, pk=pk, inmobiliaria=request.user.profile.inmobiliaria)
    propiedad_id = arrendamiento.propiedad.id

    # Validación: Solo se puede eliminar si está en estado Borrador
    if arrendamiento.estado != 'BORRADOR':
        messages.error(request, "Este contrato no se puede eliminar porque ya no es un borrador.")
        return redirect('gestion_arriendos:detalle_contrato_arrendamiento', pk=arrendamiento.pk)

    if request.method == 'POST':
        arrendamiento.delete()
        messages.success(request, "El borrador del Contrato de Arrendamiento ha sido eliminado exitosamente.")
        # Redirigimos al panel de control de la propiedad
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad_id)

    context = {
        'contrato': arrendamiento
    }
    return render(request, 'gestion_arriendos/confirmar_eliminar_contrato_arrendamiento.html', context)

# --- NUEVA VISTA PARA LA LÓGICA DE "ENVIAR A FIRMAS" ---

@login_required
def enviar_ciclo_a_firmas(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, id=propiedad_id, inmobiliaria=request.user.profile.inmobiliaria)
    
    # Buscamos los contratos activos en estado borrador para esta propiedad
    mandato = ContratoMandato.objects.filter(propiedad=propiedad, estado='BORRADOR').first()
    arrendamiento = ContratoArrendamiento.objects.filter(propiedad=propiedad, estado='BORRADOR').first()

    if not mandato or not arrendamiento:
        messages.error(request, "Error: No se encontraron ambos contratos en estado 'Borrador' para esta propiedad.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)

    # --- Generar y guardar PDF del Contrato de Mandato (SIN marca de agua) ---
    plantilla_mandato = mandato.plantilla_usada
    template_string_mandato = "{% load letras_numeros %}" + plantilla_mandato.cuerpo_texto
    contexto_mandato = { "contrato": mandato, "propiedad": propiedad, "propietario": mandato.propietario, "inmobiliaria": mandato.inmobiliaria }
    template_m = engines['django'].from_string(template_string_mandato)
    clausulas_m = template_m.render(contexto_mandato)
    html_string_mandato = render_to_string('gestion_arriendos/base_contrato_pdf.html', {
        'cuerpo_renderizado': clausulas_m, 'titulo_contrato': plantilla_mandato.titulo, 'inmobiliaria': mandato.inmobiliaria
    })
    pdf_mandato = HTML(string=html_string_mandato, base_url=request.build_absolute_uri()).write_pdf()
    mandato.archivo_pdf_final.save(f"Contrato_Mandato_Final_{mandato.id}.pdf", ContentFile(pdf_mandato), save=False)
    mandato.estado = 'EN_FIRMAS'
    mandato.save()

    # --- Generar y guardar PDF del Contrato de Arrendamiento (SIN marca de agua) ---
    plantilla_arr = arrendamiento.plantilla_usada
    template_string_arr = "{% load letras_numeros %}" + plantilla_arr.cuerpo_texto
    contexto_arr = { "contrato": arrendamiento, "propiedad": propiedad, "arrendatario": arrendamiento.arrendatario, "inmobiliaria": arrendamiento.inmobiliaria }
    template_a = engines['django'].from_string(template_string_arr)
    clausulas_a = template_a.render(contexto_arr)
    html_string_arrendamiento = render_to_string('gestion_arriendos/base_contrato_pdf.html', {
        'cuerpo_renderizado': clausulas_a, 'titulo_contrato': plantilla_arr.titulo, 'inmobiliaria': arrendamiento.inmobiliaria
    })
    pdf_arrendamiento = HTML(string=html_string_arrendamiento, base_url=request.build_absolute_uri()).write_pdf()
    arrendamiento.archivo_pdf_final.save(f"Contrato_Arrendamiento_Final_{arrendamiento.id}.pdf", ContentFile(pdf_arrendamiento), save=False)
    arrendamiento.estado = 'EN_FIRMAS'
    arrendamiento.save()

    messages.success(request, "Los contratos han sido finalizados y enviados al proceso de firmas.")
    return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)


# --- VISTA PARA SUBIR EL CONTRATO DE MANDATO FIRMADO ---

@login_required
def subir_mandato_firmado(request, pk):
    mandato = get_object_or_404(ContratoMandato, pk=pk, inmobiliaria=request.user.profile.inmobiliaria)

    # Solo se puede subir un archivo si el contrato está en proceso de firmas
    if mandato.estado != 'EN_FIRMAS':
        messages.error(request, "Solo se puede subir un archivo a un contrato que está 'En Proceso de Firmas'.")
        return redirect('gestion_arriendos:detalle_contrato_mandato', pk=mandato.pk)

    if request.method == 'POST':
        # Usamos el nuevo formulario específico que creamos
        form = SubirMandatoFirmadoForm(request.POST, request.FILES, instance=mandato)
        if form.is_valid():
            mandato = form.save(commit=False)
            mandato.estado = 'VIGENTE' # ¡El estado final cambia a Vigente!
            mandato.save()
            messages.success(request, "El contrato firmado se ha subido y el estado se ha actualizado a 'Vigente'.")
            return redirect('gestion_arriendos:detalle_contrato_mandato', pk=mandato.pk)
    else:
        # Si no es POST, no hacemos nada y redirigimos
        return redirect('gestion_arriendos:detalle_contrato_mandato', pk=mandato.pk)

@login_required
def subir_arrendamiento_firmado(request, pk):
    arrendamiento = get_object_or_404(ContratoArrendamiento, pk=pk, inmobiliaria=request.user.profile.inmobiliaria)

    # Solo se puede subir un archivo si el contrato está en proceso de firmas
    if arrendamiento.estado != 'EN_FIRMAS':
        messages.error(request, "Solo se puede subir un archivo a un contrato que está 'En Proceso de Firmas'.")
        return redirect('gestion_arriendos:detalle_contrato_arrendamiento', pk=arrendamiento.pk)

    if request.method == 'POST':
        # Usamos el formulario específico para el Contrato de Arrendamiento
        form = SubirArrendamientoFirmadoForm(request.POST, request.FILES, instance=arrendamiento)
        if form.is_valid():
            arrendamiento = form.save(commit=False)
            arrendamiento.estado = 'VIGENTE' # Cambiamos el estado a Vigente
            arrendamiento.save()
            messages.success(request, "El contrato firmado se ha subido y el estado se ha actualizado a 'Vigente'.")
            return redirect('gestion_arriendos:detalle_contrato_arrendamiento', pk=arrendamiento.pk)
    else:
        # Si no es POST, no hacemos nada y redirigimos
        return redirect('gestion_arriendos:detalle_contrato_arrendamiento', pk=arrendamiento.pk)


@login_required
def registrar_contrato_existente(request, propiedad_id):
    """
    Vista para registrar un contrato existente (migrado) directamente como VIGENTE.
    """
    inmobiliaria = request.user.profile.inmobiliaria
    propiedad = get_object_or_404(Propiedad, id=propiedad_id, inmobiliaria=inmobiliaria)

    # Verificar que la propiedad no tenga ya contratos vigentes (opcional pero recomendado)
    if ContratoMandato.objects.filter(propiedad=propiedad, estado='VIGENTE').exists():
        messages.error(request, "Esta propiedad ya tiene un contrato de mandato vigente.")
        return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)

    if request.method == 'POST':
        form = RegistrarContratoExistenteForm(request.POST, request.FILES, 
                                              propiedad=propiedad, 
                                              inmobiliaria=inmobiliaria)
        if form.is_valid():
            data = form.cleaned_data
            
            # 1. Crear Contrato de Mandato
            mandato = ContratoMandato.objects.create(
                propiedad=propiedad,
                propietario=data['propietario'],
                inmobiliaria=inmobiliaria,
                estado='VIGENTE',
                es_contrato_migrado=True,
                porcentaje_comision=data['porcentaje_comision'],
                cuenta_bancaria_pago=data['cuenta_bancaria_pago'],
                # --- USAR DATOS DEL FORMULARIO ---
                periodicidad=data['periodicidad'],
                uso_inmueble=data['uso_inmueble'],
                # ---------------------------------
            )
            
            # 2. Crear Contrato de Arrendamiento
            arrendamiento = ContratoArrendamiento.objects.create(
                contrato_mandato=mandato,
                propiedad=propiedad,
                arrendatario=data['arrendatario'],
                inmobiliaria=inmobiliaria,
                estado='VIGENTE',
                es_contrato_migrado=True,
                # --- USAR DATOS DEL FORMULARIO ---
                periodicidad=data['periodicidad'], # Asumimos la misma para ambos
                uso_inmueble=data['uso_inmueble'],
                # ---------------------------------
            )
            # Añadir codeudores si existen
            if data['codeudores']:
                arrendamiento.codeudores.set(data['codeudores'])

            # 3. Crear la primera Vigencia
            VigenciaContrato.objects.create(
                contrato_arrendamiento=arrendamiento,
                tipo='INICIAL',
                fecha_inicio=data['fecha_inicio_vigencia'],
                fecha_fin=data['fecha_fin_vigencia'],
                valor_canon=data['valor_canon']
            )

            # 4. Guardar PDF firmado si se subió
            if data['archivo_pdf_firmado']:
                mandato.archivo_pdf_firmado = data['archivo_pdf_firmado']
                arrendamiento.archivo_pdf_firmado = data['archivo_pdf_firmado']
                mandato.save()
                arrendamiento.save()

            messages.success(request, "Contrato existente registrado (migrado) exitosamente.")
            return redirect('core_inmobiliario:detalle_propiedad', id=propiedad.id)
    else:
        # Petición GET: mostrar formulario vacío
        form = RegistrarContratoExistenteForm(propiedad=propiedad, inmobiliaria=inmobiliaria)

    context = {
        'form': form,
        'propiedad': propiedad,
        'section': 'arriendos'
    }
    return render(request, 'gestion_arriendos/registrar_contrato_existente.html', context)

# --- Plantillas contratos ---

class ListaPlantillas(LoginRequiredMixin, TenantRequiredMixin, ListView):
    model = PlantillaContrato
    template_name = 'gestion_arriendos/lista_plantillas.html'
    context_object_name = 'plantillas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'arriendos'
        return context


# --- Crear plantilla de contrato.
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
                {'variable': '{{ contrato|duracion_en_meses }}', 'descripcion': 'Calcula y muestra la duración del contrato en meses.'},
            ],
            'Propietario': [
                {'variable': '{{ propietario.nombre }}', 'descripcion': 'Nombre completo del propietario.'},
                {'variable': '{{ propietario.identificacion }}', 'descripcion': 'Documento de identidad del propietario.'},
                {'variable': '{{ propietario.telefono }}', 'descripcion': 'Teléfono del propietario.'},
                {'variable': '{{ propietario.email }}', 'descripcion': 'Email del propietario.'},
            ],
            'Arrendatario': [
                {'variable': '{{ arrendatario.nombre }}', 'descripcion': 'Nombre completo del arrendatario.'},
                {'variable': '{{ arrendatario.identificacion }}', 'descripcion': 'Documento de identidad del arrendatario.'},
                {'variable': '{{ arrendatario.telefono }}', 'descripcion': 'Teléfono del arrendatario.'},
                {'variable': '{{ arrendatario.email }}', 'descripcion': 'Email del arrendatario.'},
            ],
            'Codeudor': [
                # La descripción ahora muestra la etiqueta simplificada
                {'variable': '{% lista_codeudores contrato %}', 'descripcion': 'Inserta la lista completa y formateada de todos los codeudores.'},
                {'variable': '{% firmas_codeudores contrato %}', 'descripcion': 'Inserta los bloques de firma para todos los codeudores.'}
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
                {'variable': '{{ inmobiliaria.forma_recaudo }}', 'descripcion': 'Forma de recaudo de la inmobiliaria.'},
            ]
        }
        # ----------------------
        
        return context

