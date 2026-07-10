# 🧪 Ansible Lab — laboratorio local de automatización

[![CI](https://github.com/DannyRuizB/ansible-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/DannyRuizB/ansible-lab/actions/workflows/ci.yml)
![Ansible](https://img.shields.io/badge/ansible--core-2.21-black?logo=ansible)
![Lint](https://img.shields.io/badge/ansible--lint-perfil%20production-brightgreen)
![License](https://img.shields.io/badge/licencia-MIT-blue)

Laboratorio de aprendizaje de **Ansible** que funciona **100% en local**, en dos niveles:

- **Playbooks 1-6**: el "servidor" gestionado es la propia máquina (`localhost` con `ansible_connection=local`). Sin SSH, sin servidores remotos, sin permisos de administrador — todo ocurre dentro del directorio del proyecto.
- **Playbook 7 (opcional)**: una "flota" de 3 contenedores Docker locales gestionados **por SSH real**, para practicar inventarios multi-host. Requiere Docker, pero sigue siendo local: los contenedores solo escuchan en `127.0.0.1`.

Forma parte de mi formación en automatización/DevOps con perfil de administración de sistemas (ASIR).

**🔴 Demo en vivo:** [dannyruizb.github.io/ansible-lab](https://dannyruizb.github.io/ansible-lab/) — el panel HTML que genera el playbook 4, ejecutado por el CI sobre el runner de GitHub y publicado automáticamente en cada push.

[![Captura del panel generado por el rol informe_web](https://dannyruizb.github.io/ansible-lab/captura-panel.png)](https://dannyruizb.github.io/ansible-lab/)

## 🎯 Qué demuestra

| Playbook | Conceptos |
|---|---|
| `playbooks/01_ping.yml` | Inventario, módulo `ping`, **facts** y `debug` |
| `playbooks/02_informe_sistema.yml` | **Templates Jinja2** — genera un informe Markdown del sistema (SO, hardware, discos) rellenando `templates/informe.md.j2` con los facts reales |
| `playbooks/03_desplegar_app_simulada.yml` | Un "despliegue" en miniatura: **loop**, **template con variables**, **lineinfile**/**blockinfile** idempotentes con marcador, **register**/**changed_when**, **handlers con notify** y **tags** para ejecutar solo una parte |
| `playbooks/04_panel_web_con_rol.yml` | **Roles** — la estructura estándar de Ansible (`tasks/`, `templates/`, `defaults/`, `meta/`): el rol `informe_web` genera un panel HTML con tarjetas y barras de ocupación de disco |
| `playbooks/05_auditoria_salud.yml` | Auditoría de **solo lectura** (como los `status.yml` de producción): **assert** con umbrales configurables, **block/rescue/always** (el try/catch de Ansible), **when**, **stat**, `set_fact` y filtros Jinja |
| `playbooks/06_secretos_vault.yml` | **ansible-vault** — `vars/secretos.yml` vive cifrado en el repo, se descifra en ejecución (`vars_files`) y se aplica con **no_log** para que los valores nunca salgan por pantalla ni logs |
| `playbooks/07_flota_multihost.yml` | **Multi-host por SSH real** — 3 contenedores Docker locales como nodos gestionados: inventario con grupos `[web]`/`[db]`, **group_vars**, paralelismo, resumen con `run_once` + `hostvars` y **rolling update** (`serial: 1` + `max_fail_percentage`) |

## 📁 Estructura

```
ansible-lab/
├── ansible.cfg                          # configuración (inventario por defecto, roles_path...)
├── inventario.ini                       # inventario: localhost con conexión local
├── .ansible-lint                        # configuración del linter (perfil, excepciones)
├── .github/workflows/ci.yml             # CI: lint + ejecución real de los playbooks
├── inventario_flota.ini                 # inventario multi-host (grupos web/db)
├── flota.sh                             # levantar/apagar los 3 nodos Docker
├── multihost/Dockerfile                 # imagen de nodo: Debian + sshd + python3
├── group_vars/
│   ├── web.yml                          # variables del grupo [web]
│   └── db.yml                           # variables del grupo [db]
├── playbooks/
│   ├── 01_ping.yml
│   ├── 02_informe_sistema.yml
│   ├── 03_desplegar_app_simulada.yml
│   ├── 04_panel_web_con_rol.yml
│   ├── 05_auditoria_salud.yml
│   ├── 06_secretos_vault.yml
│   └── 07_flota_multihost.yml
├── vars/
│   └── secretos.yml                     # secretos CIFRADOS con ansible-vault
├── roles/
│   └── informe_web/                     # rol: panel HTML del sistema
│       ├── tasks/main.yml
│       ├── templates/panel.html.j2
│       ├── defaults/main.yml
│       └── meta/main.yml
├── templates/
│   ├── informe.md.j2                    # plantilla del informe del sistema
│   └── app.conf.j2                      # plantilla de configuración de la app simulada
├── informes/                            # (generado) informes y panel de salida
└── entorno-prueba/                      # (generado) la "aplicación" desplegada
```

Los directorios `informes/` y `entorno-prueba/` los crean los playbooks y no se versionan.

## 🚀 Uso

Requisitos: Linux (o WSL) con Ansible instalado (`pip install --user ansible`). Para el playbook 7, además Docker (ver su sección).

```bash
git clone git@github.com:DannyRuizB/ansible-lab.git
cd ansible-lab

# 1. Primer contacto: conectividad y facts
ansible-playbook playbooks/01_ping.yml

# 2. Informe del sistema (queda en informes/informe_<hostname>.md)
ansible-playbook playbooks/02_informe_sistema.yml

# 3. Despliegue simulado
ansible-playbook playbooks/03_desplegar_app_simulada.yml

# 4. Panel HTML del sistema (rol) — queda en informes/panel_<hostname>.html
ansible-playbook playbooks/04_panel_web_con_rol.yml

# 5. Auditoría de salud (solo lectura, nunca cambia nada)
ansible-playbook playbooks/05_auditoria_salud.yml

# 6. Secretos con ansible-vault (contraseña de la demo: laboratorio-demo)
ansible-playbook playbooks/06_secretos_vault.yml --ask-vault-pass

# Ver o editar el fichero cifrado
ansible-vault view vars/secretos.yml --ask-vault-pass
```

## 🚢 Flota multi-host (playbook 7)

El único playbook que sale de `localhost`: gestiona **3 "servidores" con SSH de verdad** — contenedores Docker locales (`web1`, `web2`, `db1`) que escuchan solo en `127.0.0.1`. Requiere Docker (en WSL: `sudo apt-get install -y docker.io && sudo usermod -aG docker $USER`, y reabrir la terminal).

```bash
./flota.sh up          # clave SSH del lab + imagen + 3 contenedores
./flota.sh esperar     # espera a que el sshd de los 3 nodos esté listo
ansible -i inventario_flota.ini flota -m ping
ansible-playbook -i inventario_flota.ini playbooks/07_flota_multihost.yml
./flota.sh down        # apagar y eliminar la flota (no queda nada corriendo)
```

Cada nodo recibe la configuración de **su grupo** (`group_vars/web.yml` y `group_vars/db.yml`): los `web` despliegan `miapp-web:8080` y el `db`, `miapp-db:5432`. El CI levanta esta misma flota en cada push y verifica la idempotencia en los 3 nodos.

### Cosas que probar

```bash
# Idempotencia: la segunda ejecución no cambia nada (changed=0)
ansible-playbook playbooks/03_desplegar_app_simulada.yml
ansible-playbook playbooks/03_desplegar_app_simulada.yml

# Modo simulación: qué cambiaría, sin tocar nada (como -WhatIf en PowerShell)
ansible-playbook playbooks/03_desplegar_app_simulada.yml --check --diff

# Sobreescribir variables desde la línea de comandos
ansible-playbook playbooks/03_desplegar_app_simulada.yml -e "app_puerto=9090 app_entorno=pre"

# Comandos ad-hoc contra el inventario
ansible laboratorio -m ping
ansible laboratorio -m setup -a "filter=*mem*"

# Tags: ejecutar solo una parte del playbook 3
ansible-playbook playbooks/03_desplegar_app_simulada.yml --list-tags
ansible-playbook playbooks/03_desplegar_app_simulada.yml --tags config
ansible-playbook playbooks/03_desplegar_app_simulada.yml --skip-tags verificacion

# Ver a la auditoría suspender CON elegancia (block/rescue/always)
ansible-playbook playbooks/05_auditoria_salud.yml -e "umbral_disco_pct=1"

# Ver el handler en acción: edita a mano entorno-prueba/miapp/config/miapp.conf
# y vuelve a ejecutar el playbook 3 → lo restaura y "reinicia" el servicio
```

### Para empezar de cero

```bash
rm -rf entorno-prueba informes
```

## ✅ Integración continua

En cada push, GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)):

1. Pasa **ansible-lint** (el proyecto cumple el perfil `production`).
2. Comprueba la **sintaxis** de todos los playbooks.
3. **Ejecuta los playbooks de verdad** en el runner (al ser un laboratorio contra `localhost`, el CI es también el entorno de pruebas) y **levanta la flota Docker** para probar el multi-host por SSH.
4. Verifica la **idempotencia**: la segunda pasada del playbook 3 debe terminar con `changed=0` o el pipeline falla.
5. Publica los informes generados como artefacto descargable, incluida una **captura PNG del panel** hecha con el Chrome headless del runner.
6. **Despliega el panel HTML (y su captura) en GitHub Pages** → [demo en vivo](https://dannyruizb.github.io/ansible-lab/).

> La contraseña del vault (`laboratorio-demo`) está documentada porque los "secretos" son de mentira — el objetivo es demostrar la mecánica. En un entorno real la contraseña iría en un gestor de credenciales o en un secreto del CI, nunca en el README.

## 📝 Notas

- Sintaxis moderna de facts (`ansible_facts['distribution']` en lugar de `ansible_distribution`), compatible con ansible-core ≥ 2.21.
- El intérprete de Python está fijado en `ansible.cfg` (`interpreter_python = /usr/bin/python3`): sin avisos de *interpreter discovery* y sin sorpresas si un nodo trae varios Python.
- Los patrones del playbook 3 (marcadores `blockinfile`, handlers, variables sobreescribibles) son los mismos que se usan en entornos reales de producción, solo que aquí el "servicio" es simulado.
- El playbook 5 se puede "endurecer" para verlo fallar: `ansible-playbook playbooks/05_auditoria_salud.yml -e "umbral_disco_pct=1"`.
