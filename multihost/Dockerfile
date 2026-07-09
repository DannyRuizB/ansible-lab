# =============================================================================
# Imagen de un "servidor" del laboratorio: Debian mínimo con servidor SSH
# y Python 3 (lo único que necesita Ansible en el nodo gestionado).
#
# La clave pública se inyecta en el build (la genera flota.sh):
#   docker build --build-arg PUBKEY="$(cat .ssh_lab/id_lab.pub)" -t ansible-lab-nodo multihost/
# =============================================================================
FROM debian:13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-server python3 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/sshd

# Usuario con el que se conectará Ansible (sin contraseña: solo clave SSH)
ARG PUBKEY
RUN useradd -m -s /bin/bash ansible \
    && mkdir -p /home/ansible/.ssh \
    && echo "$PUBKEY" > /home/ansible/.ssh/authorized_keys \
    && chown -R ansible:ansible /home/ansible/.ssh \
    && chmod 700 /home/ansible/.ssh \
    && chmod 600 /home/ansible/.ssh/authorized_keys

EXPOSE 22

# sshd en primer plano (-D) con logs a stderr (-e): es el proceso del contenedor
CMD ["/usr/sbin/sshd", "-D", "-e"]
