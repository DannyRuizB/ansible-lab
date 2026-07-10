#!/usr/bin/env bash
# =============================================================================
# Gestión de la "flota" del laboratorio: 3 contenedores Docker con SSH que
# hacen de servidores gestionados por Ansible (playbook 7).
#
#   ./flota.sh up      -> genera clave SSH del lab, construye la imagen y
#                         levanta web1 (puerto 2201), web2 (2202) y db1 (2203)
#   ./flota.sh esperar -> espera a que el SSH de los 3 nodos responda
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

# Comprobación previa: docker instalado Y con permiso para usarlo. Sin esto,
# el error de docker sale a mitad de "up" y es mucho menos claro.
if ! command -v docker >/dev/null; then
  echo "ERROR: docker no está instalado (en Ubuntu/WSL: sudo apt install docker.io)" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: no puedo hablar con el demonio de Docker." >&2
  echo "  - ¿Está arrancado?  sudo service docker start" >&2
  echo "  - ¿Tienes permiso?  sudo usermod -aG docker \$USER  (y abre una sesión nueva)" >&2
  exit 1
fi

case "$caso" in
  up)
    # 1. Clave SSH exclusiva del laboratorio (ignorada por git)
    if [ ! -f "$CLAVE" ]; then
      mkdir -p .ssh_lab
      chmod 700 .ssh_lab
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
    echo "Flota levantada. Espera al SSH con:  ./flota.sh esperar"
    echo "Y luego prueba:  ansible -i inventario_flota.ini flota -m ping"
    ;;

  esperar)
    # Los contenedores tardan 1-2 s en tener el sshd listo. Reintenta la
    # conexión a cada nodo hasta 30 s antes de darlo por perdido.
    for nodo in $NODOS; do
      nombre="${nodo%%:*}"
      puerto="${nodo##*:}"
      for i in $(seq 1 15); do
        if ssh -i "$CLAVE" -p "$puerto" \
            -o StrictHostKeyChecking=accept-new \
            -o UserKnownHostsFile=.ssh_lab/known_hosts \
            -o ConnectTimeout=2 ansible@127.0.0.1 true 2>/dev/null; then
          echo "Nodo $nombre (puerto $puerto): SSH OK"
          break
        fi
        if [ "$i" = 15 ]; then
          echo "ERROR: el SSH de $nombre (puerto $puerto) no responde tras 30 s" >&2
          exit 1
        fi
        sleep 2
      done
    done
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
    echo "Uso: $0 {up|esperar|down|estado}" >&2
    exit 1
    ;;
esac
