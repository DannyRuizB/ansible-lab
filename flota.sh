#!/usr/bin/env bash
# =============================================================================
# Gestión de la "flota" del laboratorio: 3 contenedores Docker con SSH que
# hacen de servidores gestionados por Ansible (playbook 7).
#
#   ./flota.sh up      -> genera clave SSH del lab, construye la imagen y
#                         levanta web1 (puerto 2201), web2 (2202) y db1 (2203)
#   ./flota.sh down    -> para y elimina los contenedores
#   ./flota.sh estado  -> muestra el estado de la flota
#
# Todo es LOCAL: los contenedores son procesos de tu máquina y los puertos
# solo escuchan en 127.0.0.1. Al hacer "down" no queda nada corriendo.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

IMAGEN="ansible-lab-nodo"
NODOS="web1:2201 web2:2202 db1:2203"
CLAVE=".ssh_lab/id_lab"

caso="${1:-estado}"

case "$caso" in
  up)
    # 1. Clave SSH exclusiva del laboratorio (ignorada por git)
    if [ ! -f "$CLAVE" ]; then
      mkdir -p .ssh_lab
      ssh-keygen -t ed25519 -f "$CLAVE" -N "" -C "ansible-lab" >/dev/null
      echo "Clave del laboratorio creada en $CLAVE"
    fi

    # 2. Imagen con la clave pública autorizada
    docker build --build-arg PUBKEY="$(cat "$CLAVE.pub")" -t "$IMAGEN" multihost/

    # 3. Un contenedor por nodo, cada uno con su puerto SSH en localhost
    for nodo in $NODOS; do
      nombre="${nodo%%:*}"
      puerto="${nodo##*:}"
      if [ "$(docker ps -aq -f "name=^ansible-lab-$nombre$")" ]; then
        docker rm -f "ansible-lab-$nombre" >/dev/null
      fi
      docker run -d --name "ansible-lab-$nombre" --hostname "$nombre" \
        -p "127.0.0.1:$puerto:22" "$IMAGEN" >/dev/null
      echo "Nodo $nombre arriba (ssh en 127.0.0.1:$puerto)"
    done

    # 4. known_hosts limpio en cada arranque (los host keys cambian al recrear)
    rm -f .ssh_lab/known_hosts
    echo
    echo "Flota lista. Prueba:  ansible -i inventario_flota.ini flota -m ping"
    ;;

  down)
    for nodo in $NODOS; do
      nombre="${nodo%%:*}"
      docker rm -f "ansible-lab-$nombre" >/dev/null 2>&1 && echo "Nodo $nombre eliminado" || true
    done
    ;;

  estado)
    docker ps -a --filter "name=ansible-lab-" \
      --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;

  *)
    echo "Uso: $0 {up|down|estado}" >&2
    exit 1
    ;;
esac
