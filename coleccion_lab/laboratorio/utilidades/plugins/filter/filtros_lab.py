# filtros_lab — filtro empaquetado en la colección laboratorio.utilidades.
# Mismo contrato que filter_plugins/lab_filters.py (playbook 19), pero al
# vivir en una colección SOLO se alcanza por FQCN:
#   {{ 'hola' | laboratorio.utilidades.etiqueta_lab }}
# La palabra clave `collections:` de un play NO ayuda aquí: solo acorta
# módulos y actions — los filtros y tests siempre exigen el nombre completo
# (el playbook 32 lo demuestra provocando el fallo).
from __future__ import annotations


def etiqueta_lab(texto, etiqueta="laboratorio"):
    """Antepone la etiqueta al texto: 'hola' -> '[laboratorio] hola'."""
    return "[%s] %s" % (etiqueta, texto)


class FilterModule(object):
    def filters(self):
        return {"etiqueta_lab": etiqueta_lab}
