#!/usr/bin/python
# lab_eco — módulo mínimo empaquetado en la colección laboratorio.utilidades.
# Mismo esqueleto que library/lab_sello.py (playbook 25), pero viviendo en
# plugins/modules/ de una colección: su nombre completo es
# laboratorio.utilidades.lab_eco y NO existe fuera de ella.
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: lab_eco
short_description: Devuelve el mensaje etiquetado por la colección
description:
  - Módulo de demostración del playbook 32. Devuelve el mensaje recibido
    con la etiqueta de la colección delante, sin tocar el sistema.
options:
  msg:
    description: Mensaje a devolver etiquetado.
    required: true
    type: str
author:
  - Danny Ruiz (laboratorio local)
"""

EXAMPLES = """
- name: Eco etiquetado
  laboratorio.utilidades.lab_eco:
    msg: hola
"""

RETURN = """
eco:
  description: El mensaje con la etiqueta de la colección delante.
  type: str
  returned: always
"""


def main():
    module = AnsibleModule(
        argument_spec={"msg": {"type": "str", "required": True}},
        supports_check_mode=True,
    )
    module.exit_json(changed=False, eco="[laboratorio.utilidades] " + module.params["msg"])


if __name__ == "__main__":
    main()
