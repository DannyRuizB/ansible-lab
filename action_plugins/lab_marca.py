# =============================================================================
# lab_marca — action plugin a medida escrito para el playbook 24.
#
# Un action plugin es la CUARTA extensión, tras filtros (19), callbacks (22)
# y lookups (23). Su rasgo definitorio es que tiene DOS mitades:
#
#   - Corre EN EL CONTROLADOR (como un lookup), así que ve el sistema de
#     control: ficheros locales, el hostname del controlador, variables...
#   - Y desde ahí ORQUESTA un módulo EN EL TARGET con self._execute_module().
#     Un módulo normal corre entero en el nodo remoto y jamás ve el
#     controlador; un action plugin es el pegamento entre ambos mundos.
#     Así están hechos `template`, `copy`, `assemble`, `fetch`.
#
# Este plugin construye en el controlador el contenido de una marca —
# combinando el hostname DEL CONTROLADOR con el del nodo destino — y delega
# la escritura al módulo `copy` en el target. El playbook 24 lo prueba sobre
# la flota: los tres nodos acaban con el MISMO hostname de controlador en su
# marca, algo que ninguno podría haber sabido por sí mismo.
#
# La letra pequeña:
#   - Los argumentos se leen de self._task.args, y se validan en el
#     controlador antes de tocar el nodo (fallar barato).
#   - result = super().run(...) arranca el contrato del action; se le hace
#     update() con lo que devuelva el módulo para que changed/failed fluyan.
#   - El contenido es ESTABLE (sin timestamp) para que copy sea idempotente:
#     changed en la 1ª pasada, changed=0 en la 2ª.
# =============================================================================
from __future__ import annotations

import socket

from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    # Argumentos aceptados por la tarea `lab_marca:`.
    _VALID_ARGS = frozenset(("dest", "note"))

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        task_vars = task_vars or {}

        # --- validación EN EL CONTROLADOR (antes de tocar el nodo) ---
        # _VALID_ARGS ya hace que super().run() (arriba) rechace CUALQUIER
        # argumento fuera de la lista, con "Invalid options for lab_marca:
        # ..." — y eso ocurre en el controlador, antes de abrir la conexión.
        # Aquí solo queda validar lo que esa lista no puede: que `dest` esté.
        args = self._task.args or {}
        dest = args.get("dest")
        if not dest:
            raise AnsibleActionFail("lab_marca: 'dest' es obligatorio")
        note = args.get("note", "")

        # --- trabajo EN EL CONTROLADOR: datos que el nodo no tiene ---
        controller = socket.gethostname()
        target = task_vars.get("inventory_hostname", "?")
        content = (
            f"controller={controller}\n"
            f"target={target}\n"
            f"note={note}\n"
        )

        # --- delegar la escritura al ACTION `copy` EN EL TARGET ---
        # No re-implementamos la copia: reutilizamos copy, que ya es
        # idempotente y respeta check mode. OJO: `content` NO lo maneja el
        # MÓDULO copy (esperaría `src`) — es el ACTION plugin de copy quien
        # convierte el contenido en un fichero temporal y lo transfiere. Por
        # eso delegamos en el action_loader, no en _execute_module. Un action
        # plugin envolviendo a otro: el patrón real de template/assemble.
        copy_task = self._task.copy()
        copy_task.args = {"dest": dest, "content": content, "mode": "0644"}
        copy_action = self._shared_loader_obj.action_loader.get(
            "ansible.legacy.copy",
            task=copy_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj,
        )
        result.update(copy_action.run(task_vars=task_vars))
        # Exponer también el dato del controlador para que el playbook pueda
        # asertarlo sin releer el fichero.
        result["controller"] = controller
        result["target"] = target
        return result
