# =============================================================================
# lab_fichero — lookup plugin a medida escrito para el playbook 23.
#
# Un lookup es la tercera extensión clásica tras los filtros (playbook 19) y
# los callbacks (22). Devuelve DATOS para usar en una tarea —
# `{{ lookup('lab_fichero', 'ruta.txt') }}` — y su rasgo definitorio, el que
# muerde en producción, es que corre SIEMPRE EN EL CONTROLADOR:
#
#   - Aunque el play esté delegado a un nodo remoto por SSH, el fichero se
#     lee en la máquina que lanza ansible, NO en el nodo. Es como Ansible
#     distribuye plantillas y secretos que solo viven en el controlador. El
#     playbook 23 lo demuestra: lee un fichero que SOLO existe aquí y lo
#     aterriza en tres contenedores que nunca lo tuvieron.
#
#   - Devuelve una LISTA (el contrato del lookup); el motor la aplana con el
#     resultado. Con `wantlist=True` el llamante recibe la lista entera.
#
#   - Las opciones se DECLARAN en el DOCUMENTATION y se leen con get_option()
#     tras self.set_options() — igual que en filtros/callbacks, la precedencia
#     (env, ini, vars, kwargs de la llamada) la resuelve Ansible.
#
#   - Los errores son AnsibleError: un fichero que falta debe PARAR el play,
#     no colarse como cadena vacía y romper algo tres tareas más abajo.
# =============================================================================
from __future__ import annotations

DOCUMENTATION = """
    name: lab_fichero
    author: laboratorio
    short_description: Lee lineas de un fichero DEL CONTROLADOR
    description:
      - Devuelve las lineas de cada fichero indicado en I(_terms), leidas en
        el controlador. Por defecto salta lineas en blanco y comentarios.
    options:
      _terms:
        description: Rutas de fichero a leer (en el controlador).
        required: true
        type: list
        elements: str
      skip_comments:
        description: Si saltar lineas de comentario y en blanco.
        type: bool
        default: true
        ini:
          - section: lookup_lab_fichero
            key: skip_comments
        env:
          - name: ANSIBLE_LAB_FICHERO_SKIP_COMMENTS
      comment_char:
        description: Caracter que abre un comentario de linea.
        type: str
        default: '#'
"""

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        # set_options + get_option: nunca leer os.environ ni kwargs a mano.
        self.set_options(var_options=variables, direct=kwargs)
        skip_comments = self.get_option("skip_comments")
        comment_char = self.get_option("comment_char")

        result = []
        for term in terms:
            path = os.path.expanduser(str(term))
            if not os.path.exists(path):
                # Ruidoso a propósito: parar el play, no devolver "" y que el
                # fallo aparezca disfrazado tres tareas mas abajo.
                raise AnsibleError(f"lab_fichero: no existe el fichero {path!r} en el controlador")
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    lines = fh.read().splitlines()
            except OSError as e:
                raise AnsibleError(f"lab_fichero: no se pudo leer {path!r}: {e}")

            for line in lines:
                if skip_comments:
                    stripped = line.strip()
                    if not stripped or stripped.startswith(comment_char):
                        continue
                result.append(line)
        return result
