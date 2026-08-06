# =============================================================================
# Inventory plugin a medida (playbook 33): la flota, descubierta POR PLUGIN.
#
# El script del 20 y este plugin contestan a la misma pregunta (¿qué nodos
# tiene la flota?) por dos puertas distintas:
#
#   script (playbook 20)                plugin (playbook 33)
#   ─────────────────────────────       ─────────────────────────────────────
#   ejecutable, CUALQUIER lenguaje      Python dentro del proceso de Ansible
#   contrato: JSON por stdout           API: self.inventory.add_host/add_group
#   se activa por ser ejecutable        'auto' lee la clave plugin: del YAML
#   acepta lo que le echen              verify_file() puede RECHAZAR el fichero
#   opciones: argv/env artesanal        DOCUMENTATION + get_option(), como el
#                                       callback (22) y el lookup (23)
#
# Así están hechos los inventarios de verdad: amazon.aws.aws_ec2,
# community.docker.docker_containers o el constructed del playbook 21 son
# exactamente esta clase con más opciones.
# =============================================================================
from __future__ import annotations

DOCUMENTATION = """
    name: lab_flota
    short_description: Descubre la flota Docker del laboratorio (web*/db*)
    description:
      - Pregunta al daemon de Docker por los contenedores C(ansible-lab-*)
        vivos con SSH publicado y construye los grupos web/db y el paraguas
        flota — el mismo inventario que el script del playbook 20, por la
        puerta del plugin.
      - Solo acepta ficheros de configuración cuyo nombre termine en
        C(flota_plugin.yml) — la mitad verify_file de la lección.
    options:
      plugin:
        description: Nombre que activa este plugin (la clave que lee 'auto').
        required: true
        choices: ['lab_flota']
      prefijo_contenedor:
        description: Prefijo de los contenedores de la flota en Docker.
        type: str
        default: ansible-lab-
"""

EXAMPLES = """
# inventario_flota_plugin.yml — el YAML es CONFIGURACIÓN, no inventario
plugin: lab_flota
prefijo_contenedor: ansible-lab-
"""

import os
import re
import subprocess

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin

PUERTO_SSH = re.compile(r"127\.0\.0\.1:(\d+)->22/tcp")


class InventoryModule(BaseInventoryPlugin):

    NAME = "lab_flota"

    def verify_file(self, path):
        # La palabra del plugin ANTES de parsear nada: si esto devuelve False,
        # 'auto' descarta la fuente ("could not be verified") y Ansible sigue
        # con un WARNING y rc 0 — la misma letra pequeña que enseñó el 21.
        # Un script no puede negarse a un fichero; un plugin declara qué
        # acepta (aws_ec2 hace exactamente esto: exige *.aws_ec2.yml).
        return super().verify_file(path) and path.endswith(
            ("flota_plugin.yml", "flota_plugin.yaml")
        )

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path, cache)
        # Lee el YAML, lo valida contra DOCUMENTATION (plugin: obligatoria y
        # con choices; opciones desconocidas = error) y deja get_option()
        # cargado — la diferencia con el os.environ.get() artesanal de un
        # script es la misma que enseñaron el callback (22) y el lookup (23).
        self._read_config_data(path)
        prefijo = self.get_option("prefijo_contenedor")

        # Las mismas variables de conexión que [flota:vars] en el INI — con
        # una diferencia CAZADA al probar: el INI y el script escriben
        # "{{ inventory_dir }}" y Ansible lo rellena al usarlo, pero los
        # hosts que añade un plugin NO traen ese magic var (el ssh acababa
        # intentando resolver el literal "inventory_dir" como hostname). Un
        # plugin tampoco lo necesita: parse() recibe la ruta de su fichero
        # de configuración y deja las rutas ya RESUELTAS.
        basedir = os.path.dirname(os.path.abspath(path))
        vars_flota = {
            "ansible_host": "127.0.0.1",
            "ansible_user": "ansible",
            "ansible_ssh_private_key_file": os.path.join(basedir, ".ssh_lab", "id_lab"),
            "ansible_ssh_common_args": (
                "-o StrictHostKeyChecking=accept-new "
                "-o UserKnownHostsFile="
                + os.path.join(basedir, ".ssh_lab", "known_hosts")
            ),
        }

        # El paraguas existe aunque la flota esté parada: flota vacía es un
        # DATO (cero nodos), no un error — la fuente rota sí es error (abajo).
        self.inventory.add_group("flota")
        for variable, valor in vars_flota.items():
            self.inventory.set_variable("flota", variable, valor)

        for nodo, puerto in sorted(self._descubrir_flota(prefijo).items()):
            letras = re.match(r"[a-z]+", nodo)
            grupo = letras.group(0) if letras else "otros"
            # La API hace el trabajo que en el script era imprimir JSON: cada
            # add_* deja el inventario en memoria ya montado, sin contrato
            # --list/_meta/--host que cumplir ni proceso extra que lanzar.
            self.inventory.add_group(grupo)
            self.inventory.add_child("flota", grupo)
            self.inventory.add_host(nodo, group=grupo)
            self.inventory.set_variable(nodo, "ansible_port", puerto)

    def _descubrir_flota(self, prefijo):
        """Devuelve {nodo: puerto} con los contenedores de la flota vivos."""
        try:
            salida = subprocess.run(
                ["docker", "ps", "--filter", f"name={prefijo}",
                 "--format", "{{.Names}}\t{{.Ports}}"],
                capture_output=True, text=True, check=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            # Igual de RUIDOSO que el script del 20: docker caído debe parar
            # la ejecución, no colarse como inventario vacío que esconda el
            # problema tras un "no hosts matched".
            raise AnsibleParserError(
                f"lab_flota: no puedo preguntar a docker: {exc}"
            ) from exc

        nodos = {}
        for linea in salida.splitlines():
            nombre, _, puertos = linea.partition("\t")
            if not nombre.startswith(prefijo):
                continue  # el filtro de docker es por subcadena; esto es exacto
            encontrado = PUERTO_SSH.search(puertos)
            if not encontrado:
                continue  # sin SSH publicado no es un nodo gestionable
            nodos[nombre[len(prefijo):]] = int(encontrado.group(1))
        return nodos
