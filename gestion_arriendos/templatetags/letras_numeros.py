import locale
from django import template
from num2words import num2words

register = template.Library()

@register.filter(name='a_letras')
def a_letras(numero):
    """
    Convierte un número (incluyendo tipo Decimal de Django) a letras en español.
    """
    if numero is None:
        return ""
    
    try:
        # Nos aseguramos de convertir el número a un entero simple antes de pasarlo a num2words
        valor_entero = int(numero)
        return num2words(valor_entero, lang='es').title()
    except (ValueError, TypeError):
        # Si algo falla, devolvemos el número original para no perder la información
        return numero

@register.inclusion_tag('gestion_arriendos/tags/lista_codeudores.html')
def lista_codeudores(contrato):
    """
    Este tag renderiza la lista de codeudores de un contrato.
    """
    # Obtenemos la lista de codeudores del contrato
    codeudores = contrato.codeudores.all()
    # Le pasamos la lista a la plantilla 'lista_codeudores.html'
    return {'codeudores': codeudores}

@register.filter(name='duracion_en_meses')
def duracion_en_meses(contrato):
    """
    Calcula la duración en meses de la primera vigencia de un contrato.
    """
    # Buscamos la primera (la más reciente) vigencia del contrato
    primera_vigencia = contrato.vigencias.first()
    
    if not primera_vigencia:
        return "N/A" # O 0, o lo que prefieras si no hay vigencia

    fecha_inicio = primera_vigencia.fecha_inicio
    fecha_fin = primera_vigencia.fecha_fin

    # Cálculo para obtener la diferencia en meses
    meses = (fecha_fin.year - fecha_inicio.year) * 12 + (fecha_fin.month - fecha_inicio.month)
    
    # Generalmente se le suma 1 para ser inclusivo, ej: Enero a Diciembre son 12 meses, no 11.
    # Ajusta según tu lógica de negocio.
    if fecha_fin.day >= fecha_inicio.day:
        meses += 1
        
    return meses

# --- FUNCIÓN PARA LAS FIRMAS DE CODEUDORES ---
@register.inclusion_tag('gestion_arriendos/tags/firmas_codeudores.html')
def firmas_codeudores(contrato):
    """
    Este tag renderiza los bloques de firma para todos los codeudores de un contrato.
    """
    codeudores = contrato.codeudores.all()
    return {'codeudores': codeudores}
# --------------------------------------------------


@register.filter(name='formato_moneda')
def formato_moneda(valor):
    """
    Formatea un número como moneda colombiana (ej: $ 1.800.000,00).
    """
    try:
        # Intentamos establecer la configuración regional para Colombia
        locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')
    except locale.Error:
        try:
            # Un formato alternativo que a veces funciona en Windows
            locale.setlocale(locale.LC_ALL, 'es-CO')
        except locale.Error:
            # Si todo falla, usamos un formato manual simple
            return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Usamos la librería 'locale' para dar el formato correcto con separadores de miles
    return locale.currency(valor, grouping=True, symbol='$')