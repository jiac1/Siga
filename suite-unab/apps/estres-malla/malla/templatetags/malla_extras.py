"""malla/templatetags/malla_extras.py

Filtro faltante en el repositorio original: dashboard.html usaba
`{{ ultimos|get_item:carrera.pk }}` para buscar en el diccionario
`ultimos` (armado en views.dashboard) por clave, pero el módulo de
templatetags que lo define nunca se subió al repo. Se agrega aquí
siguiendo el patrón estándar de Django para lookup de diccionario
por clave dentro de una plantilla.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if not dictionary:
        return None
    return dictionary.get(key)
