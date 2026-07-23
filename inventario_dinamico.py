#!/usr/bin/env python3
# =============================================================================
# Inventario DINÁMICO de la flota (playbook 20).
#
# Mismo contenido que inventario_flota.ini, pero descubierto en vivo: en vez
# de puertos apuntados a mano, este script pregunta a Docker qué contenedores
# de la flota están corriendo y construye el inventario con lo que encuentra.
# Si mañana flota.sh levanta web3 en el 2204, aparece solo — nadie edita INIs.
#
# El CONTRATO de un script de inventario (lo que Ansible espera de él):
#
#   ./inventario_dinamico.py --list
#       JSON con los grupos ({"web": {"hosts": [...]}, ...}) y, opcionalmente,
#       una clave "_meta" con {"hostvars": {host: {...}}}. La _meta importa:
#       si falta, Ansible ejecuta el script UNA VEZ MÁS POR HOST (--host web1,
#       --host web2...) para pedir sus variables — con _meta, una sola llamada.
#
#   ./inventario_dinamico.py --host <nombre>
#       Variables de ese host. Con _meta en --list Ansible no lo llama nunca,
#       pero el contrato lo exige (inventarios antiguos viven de él).
#
# Se usa como cualquier inventario:  -i inventario_dinamico.py  (el fichero es
# ejecutable; Ansible lo detecta y lo ejecuta en lugar de parsearlo).
#
#   ansible-inventory -i inventario_dinamico.py --graph
#   ansible-playbook  -i inventario_dinamico.py playbooks/20_inventario_dinamico.yml
# =============================================================================
import json
import re
import subprocess
import sys

# Los contenedores de flota.sh se llaman ansible-lab-<nodo> y publican su SSH
# en 127.0.0.1:<puerto>->22/tcp. El nodo se agrupa por su prefijo alfabético
# (web1, web2 -> web; db1 -> db), la misma convención del INI estático.
PREFIJO = "ansible-lab-"
PUERTO_SSH = re.compile(r"127\.0\.0\.1:(\d+)->22/tcp")

# Las mismas variables de conexión que [flota:vars] en inventario_flota.ini.
# inventory_dir también existe para un script: es la carpeta que lo contiene,
# así que las rutas relativas al repo funcionan igual que con el INI.
VARS_FLOTA = {
    "ansible_host": "127.0.0.1",
    "ansible_user": "ansible",
    "ansible_ssh_private_key_file": "{{ inventory_dir }}/.ssh_lab/id_lab",
    "ansible_ssh_common_args": (
        "-o StrictHostKeyChecking=accept-new "
        "-o UserKnownHostsFile={{ inventory_dir }}/.ssh_lab/known_hosts"
    ),
}


def descubrir_flota():
    """Devuelve {nodo: puerto} con los contenedores de la flota vivos."""
    try:
        salida = subprocess.run(
            ["docker", "ps", "--filter", f"name={PREFIJO}",
             "--format", "{{.Names}}\t{{.Ports}}"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        # Un error de la fuente (docker no instalado, demonio caído) debe ser
        # RUIDOSO: un inventario vacío por accidente haría "no hosts matched"
        # y escondería el problema real. Flota parada != docker roto: si el
        # demonio responde y no hay contenedores, eso sí es inventario vacío.
        print(f"inventario_dinamico: no puedo preguntar a docker: {exc}",
              file=sys.stderr)
        sys.exit(1)

    nodos = {}
    for linea in salida.splitlines():
        nombre, _, puertos = linea.partition("\t")
        if not nombre.startswith(PREFIJO):
            continue  # el filtro de docker es por subcadena; esto es exacto
        encontrado = PUERTO_SSH.search(puertos)
        if not encontrado:
            continue  # sin SSH publicado no es un nodo gestionable
        nodos[nombre[len(PREFIJO):]] = int(encontrado.group(1))
    return nodos


def inventario(nodos):
    """Monta el JSON del contrato --list a partir de {nodo: puerto}."""
    grupos = {}
    hostvars = {}
    for nodo, puerto in sorted(nodos.items()):
        letras = re.match(r"[a-z]+", nodo)
        grupo = letras.group(0) if letras else "otros"
        grupos.setdefault(grupo, []).append(nodo)
        hostvars[nodo] = {"ansible_port": puerto}

    resultado = {"_meta": {"hostvars": hostvars}}
    for grupo, hosts in grupos.items():
        resultado[grupo] = {"hosts": hosts}
    # El grupo paraguas lleva las variables de conexión compartidas, igual
    # que [flota:children] + [flota:vars] en el INI.
    resultado["flota"] = {"children": sorted(grupos), "vars": VARS_FLOTA}
    return resultado


def main():
    argumentos = sys.argv[1:]
    if argumentos[:1] == ["--list"]:
        print(json.dumps(inventario(descubrir_flota()), indent=2))
    elif argumentos[:1] == ["--host"] and len(argumentos) == 2:
        # Con _meta en --list, Ansible nunca llega aquí; se implementa por
        # cumplir el contrato. Host desconocido = sin variables = {}.
        nodos = descubrir_flota()
        variables = {}
        if argumentos[1] in nodos:
            variables = {"ansible_port": nodos[argumentos[1]]}
        print(json.dumps(variables, indent=2))
    else:
        print("uso: inventario_dinamico.py --list | --host <nombre>",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
