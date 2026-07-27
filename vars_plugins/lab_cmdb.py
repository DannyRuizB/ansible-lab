# Vars plugin a medida (playbook 26): inyecta variables desde una mini-CMDB
# YAML (vars/cmdb_lab.yml) por host y por grupo, en el momento de cargar el
# inventario — la sexta y última pieza del tour de extensiones (filtros 19,
# callback 22, lookup 23, action 24, módulo 25).
#
# Qué lo hace distinto de host_vars/group_vars: la FUENTE puede ser cualquier
# cosa que sepa leer Python (aquí un YAML, en producción una API de CMDB, una
# base de datos, un export). Ansible pregunta por cada host y cada grupo, y
# este plugin contesta con lo que la CMDB sepa de esa entidad.
#
# Las dos trampas que el playbook 26 demuestra:
#   1. REQUIRES_ENABLED = True: como el callback lab_resumen, que Ansible VEA
#      el plugin no basta — sin listarlo en vars_plugins_enabled no corre.
#   2. vars_plugins_enabled SUSTITUYE el default (host_group_vars): si se
#      pone solo "lab_cmdb", los group_vars/host_vars de TODO el proyecto
#      dejan de cargarse en silencio. La lista correcta lleva ambos.

from __future__ import annotations

DOCUMENTATION = """
    name: lab_cmdb
    short_description: variables por host/grupo desde la mini-CMDB del laboratorio
    description:
      - Lee vars/cmdb_lab.yml (relativo a la raíz del proyecto) y devuelve
        el bloque nodos.<nombre> para cada host y grupos.<nombre> para cada
        grupo del inventario. Entidades que la CMDB no conoce reciben {}.
      - Declara REQUIRES_ENABLED, así que solo corre si aparece en
        vars_plugins_enabled (la trampa que enseña el playbook 26).
    options:
      stage:
        ini:
          - key: stage
            section: vars_lab_cmdb
        env:
          - name: ANSIBLE_VARS_LAB_CMDB_STAGE
    extends_documentation_fragment:
      - vars_plugin_staging
"""

import os

from ansible.errors import AnsibleParserError
from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible.plugins.vars import BaseVarsPlugin

CMDB_FILE = os.path.join(os.path.dirname(__file__), "..", "vars", "cmdb_lab.yml")


class VarsModule(BaseVarsPlugin):

    # Sin esto el plugin correría solo por estar en vars_plugins/. Con esto,
    # hace falta el opt-in explícito en vars_plugins_enabled — el mismo
    # patrón "visible no es activo" del callback del playbook 22.
    REQUIRES_ENABLED = True

    def get_vars(self, loader, path, entities, cache=True):
        super(VarsModule, self).get_vars(loader, path, entities)

        if not isinstance(entities, list):
            entities = [entities]

        cmdb_path = os.path.realpath(CMDB_FILE)
        if not os.path.exists(cmdb_path):
            raise AnsibleParserError(f"lab_cmdb: no existe la CMDB en {cmdb_path}")
        # load_from_file cachea por fichero: aunque Ansible pregunte una vez
        # por cada host y cada grupo, el YAML se parsea una sola vez.
        cmdb = loader.load_from_file(cmdb_path, cache="all") or {}

        datos = {}
        for entity in entities:
            if isinstance(entity, Host):
                datos.update(cmdb.get("nodos", {}).get(entity.name, {}) or {})
            elif isinstance(entity, Group):
                datos.update(cmdb.get("grupos", {}).get(entity.name, {}) or {})
        return datos
