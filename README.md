# 🧪 Ansible Lab — laboratorio local de automatización

[![CI](https://github.com/DannyRuizB/ansible-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/DannyRuizB/ansible-lab/actions/workflows/ci.yml)
![Ansible](https://img.shields.io/badge/ansible--core-2.21-black?logo=ansible)
![Lint](https://img.shields.io/badge/ansible--lint-perfil%20production-brightgreen)
![License](https://img.shields.io/badge/licencia-MIT-blue)

Laboratorio de aprendizaje de **Ansible** que funciona **100% en local**, en dos niveles:

- **Playbooks 1-6, 8-12 y 15-18**: el "servidor" gestionado es la propia máquina (`localhost` con `ansible_connection=local`). Sin SSH, sin servidores remotos, sin permisos de administrador — todo ocurre dentro del directorio del proyecto.
- **Playbooks 7, 13 y 14 (opcionales)**: una "flota" de 3 contenedores Docker locales gestionados **por SSH real**, para practicar inventarios multi-host, estrategias de ejecución y delegación. Requiere Docker, pero sigue siendo local: los contenedores solo escuchan en `127.0.0.1`.

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
| `playbooks/08_colecciones_galaxy.yml` | **Colecciones de Galaxy** — `requirements.yml` con versión + `ansible-galaxy collection install`, **FQCN**, el módulo `community.general.ini_file`, y `lookup('password')` que genera una credencial una sola vez (con `no_log` y modo 0600) y la verifica releyendo el INI |
| `playbooks/09_ensayo_check_diff.yml` | **Modo check y diff** — el "ensayo general" (`--check --diff`) y su letra pequeña: `ansible_check_mode`, `check_mode: false` (lecturas que deben ejecutarse hasta en el ensayo), `check_mode: true` (acciones que NUNCA se aplican) y **la trampa clásica**: una verificación forzada que depende de algo que el ensayo no creó — el mismo patrón que rompía el `--check` de un repo real de hardening |
| `playbooks/10_facts_personalizados.yml` | **Facts personalizados (facts.d)** — los dos sabores: fichero `.fact` **estático** (INI → `ansible_local.despliegue.app.version`, la "memoria" que un despliegue deja escrita en el servidor) y `.fact` **ejecutable** (script bash que imprime JSON y se ejecuta en cada gather). Incluye la letra pequeña: `fact_path` para no necesitar `/etc/ansible/facts.d` (root) y el clásico "¿por qué `ansible_local` está vacío?" — sin re-recolectar (`setup`) después de instalarlos, no existen |
| `playbooks/11_esperas_y_reintentos.yml` | **Esperas y reintentos** — la mitad del trabajo real de automatización: **async + poll: 0** (dispara y sigue: la tarea lenta corre en background y el playbook no se bloquea), **async_status** con **retries/until** (el bucle de espera con timeout real = retries × delay), **wait_for** con `search_regex` (esperar a un fichero/puerto/cadena) y **delegate_to** (la comprobación corre donde tú digas, no en el host del play). Incluye la trampa cazada al verificar: en una tarea async, `changed_when` fijo pisa el skip de `creates:` — idempotencia con guard explícito stat + when |
| `playbooks/12_import_vs_include.yml` | **import_tasks vs include_tasks** — estático contra dinámico, la fuente clásica de sustos al trocear playbooks: import se resuelve al **parsear** (su `when` se COPIA a cada tarea importada, sin loop, sin variables en el nombre), include al **ejecutar** (fichero elegido por variable — `entorno_{{ entorno }}.yml` —, `loop` con `loop_var` propio, when evaluado una vez). Con las tres vías demostradas sobre `playbooks/tasks/` y verificación con `assert` |
| `playbooks/13_estrategias_ejecucion.yml` | **Estrategias de ejecución** (sobre la flota) — **linear** (barrera por tarea: el host lento marca el paso de todos), **free** (cada host a su ritmo: los rápidos no esperan) y **throttle** (embudo por TAREA — de N en N aunque la play sea free; `serial` trocea la PLAY, visto en el 7). Demostrado con sellos de tiempo y `assert`: la barrera de linear se cumple, en free un web termina todo antes de que db1 acabe su primera tarea, y en el embudo nadie entra hasta que sale el anterior. Incluye la trampa de medición cazada al escribirlo: con free, un `set_fact` posterior mide cuándo el scheduler procesó el resultado (llegan a rachas), no cuándo corrió la tarea — los sellos van dentro del comando, con el reloj remoto |
| `playbooks/14_delegacion_y_run_once.yml` | **Delegación y run_once** (sobre la flota) — quién ejecuta y de quién son los datos: **delegate_to** (la tarea corre en otro nodo, el `register` es del que delega), **delegate_facts** con su trampa demostrada (un `setup` delegado SIN ella machaca los facts propios: web1 pasa a creerse db1) y **run_once** con la letra pequeña de `serial`: es una vez por play... pero una vez POR TANDA si hay serial (3 tandas = 3 "anuncios"; demostrado contando ejecuciones en ficheros del controlador). El "una vez de verdad" bajo serial: `when: inventory_hostname == groups['flota'][0]` |
| `playbooks/15_plantillas_jinja_avanzadas.yml` | **Jinja avanzado** — la mitad de Ansible es Jinja: **filtros encadenados** (`selectattr`/`rejectattr`/`groupby`/`items2dict` — transformar listas de dicts sin bucles de tareas), **la trampa de `default()`** (una cadena vacía ES un valor y no se rellena; lo falsy necesita `default(x, true)`), **macros** (la fila de la tabla se define una vez), **control de espacios** (`#jinja2: trim_blocks/lstrip_blocks` + el guion de `{{ ... -}}` — sin ellos las tablas Markdown salen con huecos) y **`lookup('template')`** (el mismo render del módulo, a una variable — verificado byte a byte contra el fichero escrito). Todo con `assert` |
| `playbooks/16_handlers_a_fondo.yml` | **Handlers a fondo** — la letra pequeña de `notify`: **dedupe** (N notify = 1 ejecución), **orden de definición** (corren en el orden del fichero, no del notify — demostrado notificando al revés), **`listen`** (varios handlers suscritos a un tema: la tarea no sabe cuántos escuchan), **`meta: flush_handlers`** (ejecutarlos A MITAD de play — el smoke test tras el reinicio, en la misma play) y **`force_handlers`** con un fallo de verdad: el auxiliar `16_demo_fallo_handlers.yml` cambia config, notifica y revienta — sin `--force-handlers` el reinicio muere con la play (config aplicada a medias), con él corre igualmente. Todo verificado con `assert` |
| `playbooks/17_errores_a_fondo.yml` | **Errores a fondo** — la letra pequeña de los fallos: **rescue con contexto** (`ansible_failed_task`/`ansible_failed_result`: anotar el parte, REPARAR la causa y reintentar, con `always` dejando su sello), **rescue vs `ignore_errors`** (la manta tapa pero la tarea queda roja y su register dice failed; el rescue caza hasta una **variable sin definir**), **`failed_when` fino** (grep rc=1 = dato, no error; y la CLI mentirosa que imprime ERROR con rc 0 — fallar por CONTENIDO), **fallos en un loop** (un ítem caído NO corta el loop: el recuento por ítem vive en `register.results`) y **el rescate del rescate** (si el rescue también revienta, el `always` corre igualmente y el error re-emerge al block exterior). Todo verificado con `assert` |
| `playbooks/18_vault_a_fondo.yml` | **Vault a fondo** — la letra pequeña del cifrado (el 6 es el caso base): **vault-ids múltiples** (dev y prod con contraseñas distintas cargados juntos: `--vault-id dev@f1 --vault-id prod@f2`), **la trampa de las etiquetas** (por defecto NO se comprueban — Ansible prueba todas las llaves contra cada vault y con las etiquetas intercambiadas abre igual; `ANSIBLE_VAULT_ID_MATCH=True` las convierte en cerradura, demostrado con la misma orden fallando), **`encrypt_string`** (YAML en claro con un valor `!vault` dentro — el diff de git sigue legible), **`rekey`** (rotar la llave sin descifrar a disco: la vieja deja de abrir, la nueva sí) y **qué hay en disco** (header `1.2;AES256;dev` — la etiqueta viaja en claro, otra razón por la que no es secreto). Demos anidadas vía `18_demo_vault_ids.yml`, todo con `assert` |

## 📁 Estructura

```
ansible-lab/
├── ansible.cfg                          # configuración (inventario por defecto, roles_path...)
├── inventario.ini                       # inventario: localhost con conexión local
├── .ansible-lint                        # configuración del linter (perfil, excepciones)
├── .github/workflows/ci.yml             # CI: lint + ejecución real de los playbooks
├── requirements.yml                     # colecciones de Galaxy que usa el lab
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
│   ├── 07_flota_multihost.yml
│   ├── 08_colecciones_galaxy.yml
│   ├── 09_ensayo_check_diff.yml
│   ├── 10_facts_personalizados.yml
│   ├── 11_esperas_y_reintentos.yml
│   ├── 12_import_vs_include.yml
│   ├── 13_estrategias_ejecucion.yml
│   ├── 14_delegacion_y_run_once.yml
│   ├── 15_plantillas_jinja_avanzadas.yml
│   ├── 16_handlers_a_fondo.yml
│   ├── 16_demo_fallo_handlers.yml       # auxiliar del 16: fallo a propósito
│   ├── 17_errores_a_fondo.yml
│   ├── 18_vault_a_fondo.yml
│   ├── 18_demo_vault_ids.yml            # auxiliar del 18: consumo anidado de vaults
│   └── tasks/                           # ficheros de tareas del playbook 12
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

# 8. Colecciones de Galaxy (instalar las colecciones primero)
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/08_colecciones_galaxy.yml
```

## 🚢 Flota multi-host (playbooks 7, 13 y 14)

Los únicos playbooks que salen de `localhost`: gestionan **3 "servidores" con SSH de verdad** — contenedores Docker locales (`web1`, `web2`, `db1`) que escuchan solo en `127.0.0.1`. Requiere Docker (en WSL: `sudo apt-get install -y docker.io && sudo usermod -aG docker $USER`, y reabrir la terminal).

```bash
./flota.sh up          # clave SSH del lab + imagen + 3 contenedores
./flota.sh esperar     # espera a que el sshd de los 3 nodos esté listo
ansible -i inventario_flota.ini flota -m ping
ansible-playbook -i inventario_flota.ini playbooks/07_flota_multihost.yml
ansible-playbook -i inventario_flota.ini playbooks/13_estrategias_ejecucion.yml
ansible-playbook -i inventario_flota.ini playbooks/14_delegacion_y_run_once.yml
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
4. Verifica la **idempotencia**: la segunda pasada del playbook 3 debe terminar con `changed=0` o el pipeline falla. Y verifica el **contrato del modo check** con el playbook 9: el ensayo `--check` sobre un entorno limpio no puede morir ni tocar el disco, y tras la ejecución real la única "novedad" permitida es su limpieza ensayada (que nunca borra nada).
5. Publica los informes generados como artefacto descargable, incluida una **captura PNG del panel** hecha con el Chrome headless del runner.
6. **Despliega el panel HTML (y su captura) en GitHub Pages** → [demo en vivo](https://dannyruizb.github.io/ansible-lab/).

> La contraseña del vault (`laboratorio-demo`) está documentada porque los "secretos" son de mentira — el objetivo es demostrar la mecánica. En un entorno real la contraseña iría en un gestor de credenciales o en un secreto del CI, nunca en el README.

## 📝 Notas

- Sintaxis moderna de facts (`ansible_facts['distribution']` en lugar de `ansible_distribution`), compatible con ansible-core ≥ 2.21.
- El intérprete de Python está fijado en `ansible.cfg` (`interpreter_python = /usr/bin/python3`): sin avisos de *interpreter discovery* y sin sorpresas si un nodo trae varios Python.
- Los patrones del playbook 3 (marcadores `blockinfile`, handlers, variables sobreescribibles) son los mismos que se usan en entornos reales de producción, solo que aquí el "servicio" es simulado.
- El playbook 5 se puede "endurecer" para verlo fallar: `ansible-playbook playbooks/05_auditoria_salud.yml -e "umbral_disco_pct=1"`.
