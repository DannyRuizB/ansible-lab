#!/usr/bin/python
# =============================================================================
# lab_sello — módulo a medida escrito para el playbook 25.
#
# Un módulo es la extensión MÁS fundamental de Ansible, y el contrapunto del
# action plugin (playbook 24): un action corre en el CONTROLADOR y orquesta;
# un módulo corre ENTERO EN EL TARGET — Ansible copia este fichero .py al
# nodo, lo ejecuta allí con el Python del nodo, y recoge su JSON de salida.
# Ve el sistema de fichero del nodo, no el del controlador.
#
# lab_sello asegura que un fichero de "sello" tenga un contenido dado. Enseña
# el contrato de un módulo bien hecho:
#
#   - AnsibleModule con argument_spec (tipos, required) — Ansible valida los
#     argumentos por ti y rechaza los desconocidos (de ahí el _VALID_ARGS
#     gratis que ya vimos en el action).
#   - supports_check_mode=True + comprobar module.check_mode: en --check NO
#     se toca el disco, pero se reporta el changed que HABRÍA ocurrido.
#   - changed HONESTO: se lee el estado actual, se compara, y solo se
#     escribe (y changed=True) si de verdad difiere — la idempotencia no es
#     un extra, es el contrato.
#   - exit_json / fail_json como únicas salidas (nunca print ni sys.exit).
# =============================================================================
from __future__ import annotations

import os

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type="str", required=True),
            content=dict(type="str", required=True),
            mode=dict(type="str", default="0644"),
        ),
        supports_check_mode=True,
    )
    path = module.params["path"]
    content = module.params["content"]
    mode = module.params["mode"]

    # Read current state on the TARGET's filesystem.
    current = None
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                current = fh.read()
        except OSError as e:
            module.fail_json(msg=f"could not read {path!r}: {e}")

    changed = current != content
    result = dict(changed=changed, path=path)

    # --check: report what would change, touch nothing.
    if module.check_mode or not changed:
        module.exit_json(**result)

    try:
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.chmod(path, int(mode, 8))
    except (OSError, ValueError) as e:
        module.fail_json(msg=f"could not write {path!r}: {e}", **result)

    module.exit_json(**result)


if __name__ == "__main__":
    run_module()
