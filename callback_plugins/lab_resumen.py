# =============================================================================
# lab_resumen — callback plugin de AGREGACIÓN escrito para el playbook 22.
#
# Un callback NO es una tarea: es código que Ansible invoca en cada evento
# de la ejecución (empieza una tarea, un host devuelve resultado, acaba el
# playbook...). Hay dos familias:
#
#   - stdout ..... SUSTITUYE la salida por pantalla (default, yaml, oneline).
#                  Solo puede haber UNO activo.
#   - aggregate .. corre AL LADO del stdout, tantos como quieras. Para
#                  métricas, notificaciones, logs... Este es de esa familia.
#
# La letra pequeña que enseña este plugin:
#
#   - CALLBACK_NEEDS_ENABLED = True: estar en callback_plugins/ solo hace
#     al plugin VISIBLE. Hasta que no se activa (callbacks_enabled en
#     ansible.cfg o ANSIBLE_CALLBACKS_ENABLED en el entorno) Ansible lo
#     ignora EN SILENCIO — ni error, ni aviso. El playbook 22 demuestra
#     las dos caras con la misma orden.
#
#   - Las opciones NO se leen a mano de os.environ: se DECLARAN en el
#     DOCUMENTATION (env + ini + default) y se piden con get_option().
#     Ansible resuelve la precedencia igual que en cualquier plugin oficial.
#
#   - La duración por tarea se mide entre v2_playbook_on_task_start y la
#     llegada del resultado de cada host (los eventos v2_runner_on_*).
# =============================================================================
from __future__ import annotations

DOCUMENTATION = """
    name: lab_resumen
    type: aggregate
    short_description: Resumen JSON de duracion y estado por tarea
    description:
      - Callback de agregacion del laboratorio (playbook 22). Anota cada
        resultado (tarea, host, estado, duracion) y al terminar el playbook
        escribe un resumen JSON ordenado de mas lenta a mas rapida.
    requirements:
      - Activarlo con ANSIBLE_CALLBACKS_ENABLED=lab_resumen (o en
        callbacks_enabled de ansible.cfg). En el path no hace nada.
    options:
      ruta_resumen:
        description: Fichero JSON donde escribir el resumen al acabar.
        default: /tmp/ansible-lab-22/resumen.json
        env:
          - name: ANSIBLE_LAB_RESUMEN
        ini:
          - section: callback_lab_resumen
            key: ruta_resumen
"""

import json
import os
import time

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "lab_resumen"
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super().__init__()
        # Marca de inicio por tarea (uuid): la duración de un resultado es
        # "ahora - inicio de SU tarea". monotonic() no retrocede si el reloj
        # del sistema se ajusta a mitad de ejecución.
        self._inicio_tarea = {}
        self._registros = []

    # --- eventos ------------------------------------------------------------

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._inicio_tarea[task._uuid] = time.monotonic()

    def _anotar(self, result, estado):
        inicio = self._inicio_tarea.get(result._task._uuid)
        duracion = round(time.monotonic() - inicio, 3) if inicio is not None else None
        self._registros.append(
            {
                "tarea": result._task.get_name(),
                "host": result._host.get_name(),
                "estado": estado,
                "duracion_s": duracion,
            }
        )

    def v2_runner_on_ok(self, result):
        self._anotar(result, "changed" if result.is_changed() else "ok")

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._anotar(result, "failed_ignorado" if ignore_errors else "failed")

    def v2_runner_on_skipped(self, result):
        self._anotar(result, "skipped")

    def v2_runner_on_unreachable(self, result):
        self._anotar(result, "unreachable")

    # --- cierre: escribir el resumen -----------------------------------------

    def v2_playbook_on_stats(self, stats):
        ruta = self.get_option("ruta_resumen")
        filas = sorted(
            self._registros,
            key=lambda r: (r["duracion_s"] is None, -(r["duracion_s"] or 0)),
        )
        resumen = {
            "total_registros": len(filas),
            "mas_lenta": filas[0] if filas else None,
            "registros": filas,
        }
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(resumen, fh, ensure_ascii=False, indent=2)
        self._display.display(
            f"[lab_resumen] {len(filas)} registros escritos en {ruta}"
        )
