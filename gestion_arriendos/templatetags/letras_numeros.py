# gestion_arriendos/templatetags/letras_numeros.py

from django import template
from num2words import num2words

register = template.Library()

@register.filter(name='a_letras')
def a_letras(numero):
    """
    Convierte un número a su representación en letras en español.
    """
    if numero is None:
        return ""
    try:
        # Usamos lang='es' para español.
        return num2words(numero, lang='es')
    except Exception:
        return numero