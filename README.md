# 🧪 Ansible Lab — laboratorio local de automatización

Laboratorio de aprendizaje de **Ansible** que funciona **100% en local**: el único "servidor" gestionado es la propia máquina (`localhost` con `ansible_connection=local`). No necesita SSH, ni servidores remotos, ni permisos de administrador — todo ocurre dentro del directorio del proyecto.

Forma parte de mi formación en automatización/DevOps con perfil de administración de sistemas (ASIR).

## 🎯 Qué demuestra

| Playbook | Conceptos |
|---|---|
| `playbooks/01_ping.yml` | Inventario, módulo `ping`, **facts** y `debug` |
| `playbooks/02_informe_sistema.yml` | **Templates Jinja2** — genera un informe Markdown del sistema (SO, hardware, discos) rellenando `templates/informe.md.j2` con los facts reales |
| `playbooks/03_desplegar_app_simulada.yml` | Un "despliegue" en miniatura: **loop**, **template con variables**, **lineinfile**/**blockinfile** idempotentes con marcador, **register**/**changed_when** y **handlers con notify** (el "servicio" solo se "reinicia" si la configuración cambió) |

## 📁 Estructura

```
ansible-lab/
├── ansible.cfg                          # configuración (inventario por defecto, formato de salida)
├── inventario.ini                       # inventario: localhost con conexión local
├── playbooks/
│   ├── 01_ping.yml
│   ├── 02_informe_sistema.yml
│   └── 03_desplegar_app_simulada.yml
├── templates/
│   ├── informe.md.j2                    # plantilla del informe del sistema
│   └── app.conf.j2                      # plantilla de configuración de la app simulada
├── informes/                            # (generado) informes de salida
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

## 📝 Notas

- Sintaxis moderna de facts (`ansible_facts['distribution']` en lugar de `ansible_distribution`), compatible con ansible-core ≥ 2.21.
- Los patrones del playbook 3 (marcadores `blockinfile`, handlers, variables sobreescribibles) son los mismos que se usan en entornos reales de producción, solo que aquí el "servicio" es simulado.
