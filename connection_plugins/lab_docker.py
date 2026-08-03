# =============================================================================
# lab_docker — connection plugin a medida escrito para el playbook 31.
#
# La octava extensión del tour (filtros 19, callbacks 22, lookups 23, action
# 24, módulos 25, vars 26, tests 30): un connection plugin es EL TRANSPORTE.
# Todo lo que Ansible hace en un nodo pasa por exactamente TRES métodos:
#
#   exec_command(cmd) .... ejecutar una orden en el nodo
#   put_file(a, b) ....... subir un fichero (así viajan los MÓDULOS: Ansible
#                          copia el .py al tmp remoto y lo ejecuta con exec)
#   fetch_file(a, b) ..... bajar un fichero (fetch, slurp de vuelta...)
#
# Quien implemente esos tres tiene un transporte completo: ssh, paramiko,
# winrm, community.docker.docker... y este. lab_docker habla con los
# contenedores de la flota por `docker exec` / `docker cp`: MISMOS nodos que
# el inventario SSH del playbook 7, cero puertos, cero claves, cero usuario.
#
# La lección incómoda que el playbook demuestra: entrar por la puerta del
# daemon te hace ROOT en el contenedor sin presentar credencial alguna — el
# mismo motivo por el que montar docker.sock en un contenedor es root del
# host regalado. Poder administrar sin SSH es comodísimo; quién puede hablar
# con el daemon es EXACTAMENTE la superficie que estás regalando a cambio.
# =============================================================================
from __future__ import annotations

DOCUMENTATION = """
    name: lab_docker
    short_description: Transporte docker exec/cp para la flota del laboratorio
    description:
      - Ejecuta las tareas dentro de un contenedor Docker local usando
        C(docker exec) y mueve ficheros con C(docker cp). Sin SSH, sin
        puertos, sin claves; la autenticacion es poder hablar con el daemon.
    author: laboratorio
    options:
      remote_addr:
        description: Nombre (o id) del contenedor gestionado.
        default: inventory_hostname
        vars:
          - name: inventory_hostname
          - name: ansible_host
          - name: ansible_lab_docker_container
"""

import subprocess

from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

display = Display()


class Connection(ConnectionBase):
    """Transporte minimo: tres metodos y ya eres un plugin de conexion."""

    transport = "lab_docker"
    # Sin pipelining: cada modulo viaja como fichero via put_file, que es
    # justo lo que el playbook quiere ensenar (el camino comodo existe, pero
    # esconde la mecanica).
    has_pipelining = False

    def _contenedor(self):
        return self.get_option("remote_addr")

    def _connect(self):
        # "Conectar" aqui es solo comprobar que el contenedor existe y corre:
        # docker exec no mantiene sesion (cada orden es un proceso nuevo),
        # asi que no hay socket que abrir ni que cachear.
        if self._connected:
            return self
        nombre = self._contenedor()
        probe = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", nombre],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode != 0 or probe.stdout.strip() != "true":
            raise AnsibleConnectionFailure(
                f"el contenedor '{nombre}' no existe o no esta corriendo "
                f"(¿./flota.sh up?): {probe.stderr.strip()}"
            )
        display.vvv(f"CONEXION lab_docker establecida (docker exec)", host=nombre)
        self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super().exec_command(cmd, in_data=in_data, sudoable=sudoable)
        nombre = self._contenedor()
        # -i mantiene stdin abierto para los modulos que lo usan; el shell
        # es el contrato de exec_command (cmd llega como UNA cadena shell).
        args = ["docker", "exec", "-i", nombre, "/bin/sh", "-c", cmd]
        display.vvv(f"EXEC {cmd}", host=nombre)
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(in_data)
        return proc.returncode, stdout, stderr

    def put_file(self, in_path, out_path):
        super().put_file(in_path, out_path)
        nombre = self._contenedor()
        display.vvv(f"PUT {in_path} -> {out_path}", host=nombre)
        cp = subprocess.run(
            ["docker", "cp", in_path, f"{nombre}:{out_path}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if cp.returncode != 0:
            raise AnsibleError(f"docker cp fallo subiendo {in_path}: {cp.stderr.strip()}")

    def fetch_file(self, in_path, out_path):
        super().fetch_file(in_path, out_path)
        nombre = self._contenedor()
        display.vvv(f"FETCH {in_path} -> {out_path}", host=nombre)
        cp = subprocess.run(
            ["docker", "cp", f"{nombre}:{in_path}", out_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if cp.returncode != 0:
            raise AnsibleError(f"docker cp fallo bajando {in_path}: {cp.stderr.strip()}")

    def close(self):
        # Nada que cerrar: no hay sesion persistente que soltar.
        self._connected = False
