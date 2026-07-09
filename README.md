# 🧪 Ansible Lab — laboratorio local de automatización

[![CI](https://github.com/DannyRuizB/ansible-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/DannyRuizB/ansible-lab/actions/workflows/ci.yml)
![Ansible](https://img.shields.io/badge/ansible--core-2.21-black?logo=ansible)
![Lint](https://img.shields.io/badge/ansible--lint-perfil%20production-brightgreen)

Laboratorio de aprendizaje de **Ansible** que funciona **100% en local**: el único "servidor" gestionado es la propia máquina (`localhost` con `ansible_connection=local`). No necesita SSH, ni servidores remotos, ni permisos de administrador — todo ocurre dentro del directorio del proyecto.

Forma parte de mi formación en automatización/DevOps con perfil de administración de sistemas (ASIR).

## 🎯 Qué demuestra

| Playbook | Conceptos |
|---|---|
| `playbooks/01_ping.yml` | Inventario, módulo `ping`, **facts** y `debug` |
| `playbooks/02_informe_sistema.yml` | **Templates Jinja2** — genera un informe Markdown del sistema (SO, hardware, discos) rellenando `templates/informe.md.j2` con los facts reales |
| `playbooks/03_desplegar_app_simulada.yml` | Un "despliegue" en miniatura: **loop**, **template con variables**, **lineinfile**/**blockinfile** idempotentes con marcador, **register**/**changed_when** y **handlers con notify** (el "servicio" solo se "reinicia" si la configuración cambió) |
| `playbooks/04_panel_web_con_rol.yml` | **Roles** — la estructura estándar de Ansible (`tasks/`, `templates/`, `defaults/`, `meta/`): el rol `informe_web` genera un panel HTML con tarjetas y barras de ocupación de disco |
| `playbooks/05_auditoria_salud.yml` | Auditoría de **solo lectura** (como los `status.yml` de producción): **assert** con umbrales configurables, **when**, **stat**, `set_fact` y filtros Jinja (`selectattr`, `map`) |

## 📁 Estructura

```
ansible-lab/
├── ansible.cfg                          # configuración (inventario por defecto, roles_path...)
├── inventario.ini                       # inventario: localhost con conexión local
├── .ansible-lint                        # configuración del linter (perfil, excepciones)
├── .github/workflows/ci.yml             # CI: lint + ejecución real de los playbooks
├── playbooks/
│   ├── 01_ping.yml
│   ├── 02_informe_sistema.yml
│   ├── 03_desplegar_app_simulada.yml
│   ├── 04_panel_web_con_rol.yml
│   └── 05_auditoria_salud.yml
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

Requisitos: Linux (o WSL) con Ansible instalado (`pip install --user ansible`).

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
```

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
3. **Ejecuta los 5 playbooks de verdad** en el runner (al ser un laboratorio contra `localhost`, el CI es también el entorno de pruebas).
4. Verifica la **idempotencia**: la segunda pasada del playbook 3 debe terminar con `changed=0` o el pipeline falla.
5. Publica los informes generados como artefacto descargable.

## 📝 Notas

- Sintaxis moderna de facts (`ansible_facts['distribution']` en lugar de `ansible_distribution`), compatible con ansible-core ≥ 2.21.
- Los patrones del playbook 3 (marcadores `blockinfile`, handlers, variables sobreescribibles) son los mismos que se usan en entornos reales de producción, solo que aquí el "servicio" es simulado.
- El playbook 5 se puede "endurecer" para verlo fallar: `ansible-playbook playbooks/05_auditoria_salud.yml -e "umbral_disco_pct=1"`.
