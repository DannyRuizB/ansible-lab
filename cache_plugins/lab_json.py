# =============================================================================
# lab_json — cache plugin a medida (playbook 35). La DÉCIMA extensión del tour.
#
# El playbook 29 USA el jsonfile de serie para cachear facts entre procesos.
# Este implementa el BACKEND: un cache plugin decide DÓNDE y CÓMO se guardan
# los facts en disco. Es un plugin de fichero, así que hereda de
# BaseFileCacheModule (un fichero por host bajo fact_caching_connection) y solo
# tiene que decir cómo se serializa un valor — _dump al escribir, _load al
# leer. Todo lo demás (claves, caducidad con fact_caching_timeout, contains,
# flush) lo pone la base.
#
# La gracia que lo hace VISIBLE frente al jsonfile: envuelve los facts en un
# sobre con marca propia (_lab_cache) y los escribe INDENTADOS. El jsonfile de
# serie escribe el dict pelado en una línea; nuestro fichero se reconoce a
# ojo, y el playbook 35 comprueba en disco que la marca está — la prueba de
# que corrió NUESTRO plugin, no el de serie.
# =============================================================================
from __future__ import annotations

DOCUMENTATION = """
    name: lab_json
    short_description: Cache de facts en JSON indentado con sobre propio (lab).
    description:
        - Guarda los facts de cada host en un fichero JSON, uno por host, bajo
          la ruta de C(fact_caching_connection).
        - Envuelve el valor en un sobre C(_lab_cache) e indenta el JSON, para
          que el artefacto en disco se distinga del plugin C(jsonfile) de serie.
    author: laboratorio-ansible (@DannyRuizB)
    version_added: "0.35"
    options:
      _uri:
        required: True
        description:
          - Directorio donde el plugin escribe los ficheros JSON por host.
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
        type: path
      _prefix:
        description: Prefijo opcional para los ficheros JSON.
        env:
          - name: ANSIBLE_CACHE_PLUGIN_PREFIX
        ini:
          - key: fact_caching_prefix
            section: defaults
      _timeout:
        default: 86400
        description: Caducidad de la cache, en segundos.
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
          - key: fact_caching_timeout
            section: defaults
        type: integer
"""

import json
import pathlib

from ansible.plugins.cache import BaseFileCacheModule

# Marca del sobre: si un fichero de cache la lleva, lo escribió ESTE plugin.
CACHE_MARKER = "_lab_cache"


class CacheModule(BaseFileCacheModule):
    """Cache de facts en JSON indentado, con sobre reconocible."""

    def _dump(self, value, filepath):
        envelope = {
            CACHE_MARKER: 1,
            "stored_by": "lab_json",
            "facts": value,
        }
        # indent=2 a propósito: el jsonfile de serie escribe una sola línea;
        # este se lee de un vistazo y se distingue en el assert del playbook.
        pathlib.Path(filepath).write_text(json.dumps(envelope, indent=2, sort_keys=True))

    def _load(self, filepath):
        data = json.loads(pathlib.Path(filepath).read_text())
        # Retrocompatible con un fichero pelado (jsonfile) por si se comparte
        # el directorio: si no hay sobre, se devuelve tal cual.
        if isinstance(data, dict) and CACHE_MARKER in data:
            return data["facts"]
        return data
