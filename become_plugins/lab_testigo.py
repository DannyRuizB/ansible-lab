# Become plugin a medida (playbook 54): la undécima extensión — LA IDENTIDAD.
#
# Un become plugin no "cambia de usuario": construye la línea de comandos que
# lo hace. Ansible le pasa el comando que quiere ejecutar (`cmd`) y el plugin
# devuelve OTRO comando que lo envuelve: `sudo -u ana ...`, `su ana -c ...`,
# `doas -u ana ...`. Este no escala de verdad (el laboratorio corre sin
# permisos de administrador): envuelve el comando con `env LAB_TESTIGO_USER=<
# usuario>` para que el módulo vea A QUIÉN se le pidió ser. Todo lo demás es
# exactamente lo que hace sudo:
#
#   - la marca de éxito: `echo BECOME-SUCCESS-<id>` delante del comando real;
#     el connection plugin espera a verla antes de dar el become por bueno;
#   - la clave: si hay `lab_testigo_clave_fichero`, el envoltorio imprime un
#     prompt, lee una línea y la compara con ese fichero. Ansible ve el prompt
#     y escribe `ansible_become_password` por la entrada estándar — nunca en
#     la línea de comandos (el playbook 54 lo comprueba con -vvv);
#   - `fail`: el texto que el envoltorio imprime cuando la clave no cuadra.
#
# Ejemplo:
#   - ansible.builtin.command: printenv LAB_TESTIGO_USER
#     become: true
#     become_method: lab_testigo
#     become_user: ana            # -> stdout "ana"
from __future__ import annotations

DOCUMENTATION = """
name: lab_testigo
short_description: Become de laboratorio que envuelve el comando sin cambiar de usuario
description:
  - Envuelve el comando con C(env LAB_TESTIGO_USER=<become_user>) y la marca de
    éxito de Ansible. Opcionalmente pide una clave por prompt y la compara con un
    fichero, como haría sudo.
author: Danny Ruiz Boluda
options:
  become_user:
    description: Usuario al que se "escala" (solo se anota en LAB_TESTIGO_USER).
    default: root
    ini:
      - section: privilege_escalation
        key: become_user
    vars:
      - name: ansible_become_user
      - name: ansible_lab_testigo_user
    env:
      - name: ANSIBLE_BECOME_USER
    keyword:
      - name: become_user
  become_pass:
    description: Clave que Ansible escribe cuando ve el prompt.
    required: false
    vars:
      - name: ansible_become_password
      - name: ansible_become_pass
    env:
      - name: ANSIBLE_BECOME_PASS
  clave_fichero:
    description: Fichero con la clave esperada. Sin él, no se pide clave.
    required: false
    vars:
      - name: lab_testigo_clave_fichero
"""

import shlex

from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'lab_testigo'

    # Lo que imprime el envoltorio cuando la clave no cuadra.
    fail = ('lab_testigo: clave incorrecta',)

    def build_become_command(self, cmd, shell):
        # La base fija self._id y self.success (BECOME-SUCCESS-<id>).
        super(BecomeModule, self).build_become_command(cmd, shell)
        if not cmd:
            return cmd

        user = self.get_option('become_user') or 'root'
        envuelto = 'env LAB_TESTIGO_USER=%s %s -c %s' % (
            shlex.quote(user),
            shell.executable or '/bin/sh',
            self._build_success_command(cmd, shell, noexe=True),
        )

        fichero = self.get_option('clave_fichero')
        if not fichero:
            return envuelto

        # Prompt único por ejecución (como el `[sudo via ansible, key=...]` de
        # sudo): así Ansible no lo confunde con la salida de nadie más.
        self.prompt = '[lab_testigo %s] clave: ' % self._id
        guardia = "printf '%%s' %s; IFS= read -r c; [ \"$c\" = \"$(cat %s)\" ] || { echo %s; exit 1; }; exec %s" % (
            shlex.quote(self.prompt), shlex.quote(fichero), shlex.quote(self.fail[0]), envuelto)
        return '/bin/sh -c %s' % shlex.quote(guardia)
