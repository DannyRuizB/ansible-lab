# 🧪 Ansible Lab — laboratorio local de automatización

[![CI](https://github.com/DannyRuizB/ansible-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/DannyRuizB/ansible-lab/actions/workflows/ci.yml)
![Ansible](https://img.shields.io/badge/ansible--core-2.21-black?logo=ansible)
![Lint](https://img.shields.io/badge/ansible--lint-perfil%20production-brightgreen)
![License](https://img.shields.io/badge/licencia-MIT-blue)

Laboratorio de aprendizaje de **Ansible** que funciona **100% en local**, en dos niveles:

- **Playbooks 1-6, 8-12, 15-19, 22, 25-26, 28-30, 32 y 34-38**: el "servidor" gestionado es la propia máquina (`localhost` con `ansible_connection=local`). Sin SSH, sin servidores remotos, sin permisos de administrador — todo ocurre dentro del directorio del proyecto.
- **Playbooks 7, 13, 14, 20, 21, 23, 24, 27, 31 y 33 (opcionales)**: una "flota" de 3 contenedores Docker locales gestionados **por SSH real** (y en el 31, por un **connection plugin propio sobre `docker exec`**), para practicar inventarios multi-host, estrategias de ejecución, delegación, inventario dinámico, inventario por capas, lookups, action, connection e inventory plugins a medida, y la precedencia de variables. Requiere Docker, pero sigue siendo local: los contenedores solo escuchan en `127.0.0.1`.

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
| `playbooks/19_filtros_a_medida.yml` | **Filtros Jinja a medida (Python)** — cuando ninguno de los ~50 filtros nativos (playbook 15) encaja, se escribe uno en Python en vez de contorsionar un one-liner. Un `filter_plugins/lab_filters.py` con una clase `FilterModule` cuyo `filters()` devuelve `{nombre: función}`; Ansible lo autodescubre por la ruta `filter_plugins` de `ansible.cfg` y desde ahí se usan como los built-in. Tres filtros propios — **`to_snake`** (CamelCase/kebab/espacios → snake_case), **`redact_secrets`** (enmascara dejando N chars, nunca filtra un secreto más corto que el prefijo) y **`human_bytes`** (1536 → `1.5 KiB`) — verificados con `assert`, encadenados con los nativos (`map('to_snake') | sort`) y usados dentro de una plantilla. No toca disco: idempotente por construcción |
| `playbooks/20_inventario_dinamico.yml` | **Inventario dinámico** (sobre la flota) — el INI estático miente en cuanto la realidad cambia; un inventario dinámico pregunta a la **fuente de verdad** al ejecutar (aquí Docker; en producción AWS/Proxmox/NetBox). `inventario_dinamico.py` descubre los contenedores vivos y emite el **contrato**: `--list` con grupos + `_meta.hostvars` (la letra pequeña: sin `_meta`, Ansible ejecuta el script una vez más POR HOST) y `--host` por compatibilidad. Los errores de la fuente son **ruidosos** (docker caído = exit 1, no un inventario vacío que esconda el problema); flota parada sí es inventario vacío (dato, no error). Verificación doble: el contrato validado desde fuera (localhost) y **conexión SSH real** a lo descubierto, con `hostname` confirmando que cada puerto lleva al nodo que el inventario dice |
| `playbooks/21_inventario_por_capas.yml` | **Inventario por capas: el plugin `constructed`** (sobre la flota) — una capa que se apila detrás de cualquier fuente (`-i fuente -i capa`, el orden importa) y deriva grupos y variables con Jinja, sin código: **`compose`** (`ssh_endpoint`, `nodo_numero`), **`groups`** condicionales (paridad) y **`keyed_groups`** (`rol_web`/`rol_db` derivados del nombre — lo que el script del 20 agrupa a mano, con cero código). Lo carga el plugin `auto` por la clave `plugin:`, sin tocar config. **La trampa es doble**: con `strict: false` (el default) un error de plantilla se traga EN SILENCIO (el grupo no aparece); con `strict: true` la capa falla… pero `ansible-inventory` sigue con **rc 0** — una fuente que no parsea se descarta con un warning, y solo `ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED` convierte el aviso en parada. Demostrado con la misma capa rota por los tres caminos, y rematado conectando **por SSH a un grupo que solo existe en la capa** (`rol_web`) |
| `playbooks/22_callback_a_medida.yml` | **Callback plugin a medida** — la otra extensión clásica tras los filtros del 19: código Python que Ansible invoca en **cada evento** de la ejecución (así se construyen `profile_tasks`, ara o un notificador de despliegues). `callback_plugins/lab_resumen.py` es un callback **aggregate** (corre AL LADO de la salida normal; un stdout la sustituiría) que anota tarea/host/estado/duración y escribe un resumen JSON al acabar. **La trampa que demuestra**: con `CALLBACK_NEEDS_ENABLED`, estar en `callback_plugins/` solo lo hace **visible** — sin activarlo (`ANSIBLE_CALLBACKS_ENABLED=lab_resumen`) Ansible lo ignora EN SILENCIO; la misma orden anidada corre sin y con la variable, con assert de "no existe" y de contenido (los cuatro desenlaces ok/changed/skipped/failed-ignorado clasificados, y el `sleep 1` encabezando las duraciones). Opciones **como Dios manda**: declaradas en `DOCUMENTATION` (env+ini+default) y leídas con `get_option()`, no un `os.environ.get()` artesanal |
| `playbooks/23_lookup_a_medida.yml` | **Lookup plugin a medida** (sobre la flota) — cierra la trilogía de extensiones Python tras los filtros (19) y el callback (22). Un lookup APORTA datos a una tarea (`{{ lookup('lab_fichero', ruta) }}`) y su rasgo definitorio es que corre **en el controlador**: `lookup_plugins/lab_fichero.py` lee un fichero y devuelve sus líneas (salta comentarios por defecto, opción `skip_comments` vía `DOCUMENTATION` + `get_option()`). **La trampa que demuestra**: el play lee un fichero que **solo existe en el controlador** y lo aterriza en los tres nodos de la flota que nunca lo tuvieron (`stat` remoto: no existe; la variable del lookup: llena) — así distribuye Ansible plantillas y secretos que solo viven aquí. Devuelve una **lista** (`wantlist=True` para recibirla entera), y un fichero ausente **para el play** (`AnsibleError`), no se cuela como cadena vacía. Trampa de escritura cazada: `join('\n')` deja la cadena literal `\n` (Jinja no procesa el escape) — un `{% for %}` en bloque literal YAML da los saltos de verdad |
| `playbooks/24_action_a_medida.yml` | **Action plugin a medida** (sobre la flota) — la cuarta extensión Python, tras filtros (19), callbacks (22) y lookups (23). Un action plugin tiene DOS mitades: corre **en el controlador** (ve ficheros locales, el hostname del control, variables) y desde ahí **orquesta un módulo en el target** — un módulo normal corre entero en el nodo y jamás ve el controlador; así están hechos `template`, `copy`, `fetch`. `action_plugins/lab_marca.py` construye en el controlador el contenido de una marca (hostname del control + del nodo) y **delega la escritura al action `copy`** (que convierte `content` en fichero temporal y lo transfiere — un `_execute_module` del *módulo* copy no puede). **La trampa que demuestra**: los tres nodos acaban con el MISMO hostname de controlador en su marca (dato que ninguno podía conocer), es idempotente (2ª pasada `changed=0`), y un argumento no soportado se rechaza **en el controlador** (`_VALID_ARGS`) antes de tocar el nodo |
| `playbooks/25_modulo_a_medida.yml` | **Módulo a medida** — la extensión más fundamental, y el contrapunto del action plugin (24): un action corre en el **controlador** y orquesta; un módulo corre **entero en el target** (Ansible copia `library/lab_sello.py` al nodo y lo ejecuta con su Python). `lab_sello` asegura que un fichero de sello tenga un contenido dado, y enseña el contrato de un módulo bien hecho: `AnsibleModule` con `argument_spec` (tipos, `required`), `supports_check_mode=True` (en `--check` reporta el cambio que haría sin tocar el disco), un `changed` **honesto** (lee, compara, solo escribe si difiere) y salidas solo por `exit_json`/`fail_json`. **Demuestra**: 1ª aplicación cambia, 2ª con el mismo contenido no (idempotencia); en `check_mode: true` con contenido nuevo dice `changed=true` pero un `slurp` confirma que el disco no se tocó |
| `playbooks/26_vars_a_medida.yml` | **Vars plugin a medida** — la sexta pieza del tour de extensiones (filtros 19, callback 22, lookup 23, action 24, módulo 25): `vars_plugins/lab_cmdb.py` corre en el **controlador al cargar el inventario** y contesta, por cada host y cada grupo, con variables desde una mini-CMDB YAML (`vars/cmdb_lab.yml`) — la fuente podría ser una API o una BD, Ansible solo ve variables de inventario. Dos trampas demostradas: `REQUIRES_ENABLED` (verlo en `vars_plugins/` no basta, hay que listarlo en `vars_plugins_enabled` — el hermano `26_demo_sin_habilitar.yml` corre en CI con la lista sin `lab_cmdb` y confirma que la CMDB no llega), y que **esa lista SUSTITUYE el default**: sin `host_group_vars` delante, los `group_vars/` de todo el proyecto dejan de cargarse en silencio (lo vigila el testigo `cmdb_grupo_testigo`). **Demuestra**: variables sin `vars_files` ni `set_fact`, precedencia host > grupo, y el testigo vivo |
| `playbooks/27_precedencia_variables.yml` | **Precedencia de variables a fondo** (sobre la flota) — la pregunta que más discusiones genera en un proyecto real: *"¿por qué esta variable vale ESO aquí?"*. De los 22 niveles documentados, demuestra con asserts los que muerden: **la escalera** (defaults del rol `prec_demo` < `group_vars/all` < `group_vars/web` < `host_vars/web1` — cada nodo de la flota ve el peldaño que le toca), que las **vars del play pisan TODO el inventario** (hasta el host_vars, lo más específico), block < tarea (cuanto más cerca, más manda), los **empates entre grupos hermanos** (mismo nivel = funde en orden ALFABÉTICO y el último pisa; el desempate explícito es `ansible_group_priority` — a más prioridad, más tarde funde = gana), que **los diccionarios se REEMPLAZAN, no se fusionan** (`hash_behaviour=replace`: redefinir `prec_app_conf` con solo `puerto` hace desaparecer `debug` en los web; el arreglo explícito es `combine`) y la trampa final: **`set_fact` gana al play pero NADA gana a un `-e`** — el `set_fact` termina en "ok" sin avisar y el extra var sigue mandando, en TODAS las plays del run (por eso un `-e` olvidado en una plantilla de AWX/Semaphore contamina todo lo que lanza). El `-e prec_ganador=extra` de la orden es parte de la lección |
| `playbooks/28_tags_a_fondo.yml` | **Tags y `--skip-tags` a fondo** — las tags viven en el YAML pero **la selección es de la orden**, así que la lección ejecuta `28_demo_tags.yml` una vez por escena (nueve órdenes anidadas) y comprueba con asserts **exactamente** qué tareas dejaron marca. Demuestra: que `--tags X` apaga todo lo no etiquetado (la sorpresa habitual), la **herencia de tags de un block**, que `always` corre con cualquier selección (y `--skip-tags always` es la única forma de quitarlo), el patrón **`never` + `debug`** para tareas de diagnóstico que solo corren pedidas a propósito, los selectores especiales (`--tags untagged`) y `--list-tags` como catálogo sin ejecutar nada. **La trampa gorda**: la tag de un `import_tasks` (estático) SE COPIA a cada tarea importada; la de un `include_tasks` (dinámico) se queda en la sentencia — con `--tags incluido` el include carga el fichero y **ninguna tarea interior corre**. El arreglo: `apply: {tags: [...]}` en el include (o pasarse a `import_tasks`) |
| `playbooks/29_cache_de_facts.yml` | **Caché de facts: gathering smart, jsonfile y caducidad** — recoger facts es lo más caro de casi cualquier play, y la caché los guarda **entre ejecuciones**: como la gracia está justo ahí, la lección ejecuta `29_demo_cache.yml` en órdenes anidadas con la política por variables de entorno (`ANSIBLE_GATHERING`, `ANSIBLE_CACHE_PLUGIN…`, sin tocar el `ansible.cfg` del repo) y comprueba con asserts las cuatro caras: sin backend cada pasada lanza su setup y el `cacheable: true` no cachea nada (el plugin de serie es `memory`); con **jsonfile + smart** la 2ª pasada trae la hora **congelada** de la 1ª (la prueba de que no hubo setup) y el **sello cacheable cruza de proceso**; con `fact_caching_timeout` corto la caducidad re-recoge **y se lleva también los sellos**; y al final se abre el fichero: un JSON **en claro** con toda la vida del host (el formato exacto es de cada versión de core — la 2.21 prefija `s1_` y envuelve en `__payload__` — así que el assert mira el texto, no la estructura). Moraleja doble: lo bueno y lo peligroso de la caché son la misma cosa — TODOS los facts pasan a tener la edad de la caché, y el fichero cuenta tu host en claro a quien pueda leerlo |
| `playbooks/30_tests_a_medida.yml` | **Tests de Jinja a medida: el séptimo tipo de extensión** — el tour (19, 22, 23, 24, 25, 26) se dio por cerrado con seis piezas… y había un colado: los tests también se extienden. El contrato es la diferencia: un filtro TRANSFORMA, un test CLASIFICA (contesta sí o no) — se usa con `is` / `is not` y es lo que **esperan `select` / `reject` / `selectattr` / `rejectattr`**. `test_plugins/lab_tests.py` (clase `TestModule`, método `tests()`, autodescubierto por la ruta `test_plugins` añadida a `ansible.cfg`) trae tres del gremio: **`es_ipv4_privada`** (RFC 1918 estricto — el `is_private` de Python también dice sí a loopback y link-local, que no es lo mismo), **`es_puerto_privilegiado`** (< 1024) y **`es_mac_valida`** (6 octetos, separador COHERENTE: la MAC con `:` y `-` mezclados cae por el backreference). Con ellos la revisión de seguridad se escribe tal cual se piensa: `rejectattr('ip', 'es_ipv4_privada') \| selectattr('puerto', 'es_puerto_privilegiado')`. **La trampa que demuestra**: filtros y tests viven en NAMESPACES SEPARADOS — `select('to_snake')` (el filtro del 19) y `'x' \| es_ipv4_privada` se provocan DE VERDAD y revientan los dos, cazados con asserts. Y el contrato del buen test: **bool de verdad y nunca una excepción** (a "¿esta cosa rara es una IP?" se contesta `False`; `int(True) == 1` haría de `True` un puerto privilegiado — excluido a propósito). No toca disco: idempotente por construcción |
| `playbooks/31_connection_a_medida.yml` | **Connection plugin a medida: la octava extensión — EL TRANSPORTE** (sobre la flota). Todo lo que Ansible hace en un nodo pasa por TRES métodos del connection plugin: `exec_command` (ejecutar), `put_file` (subir — **así viajan los MÓDULOS**: el .py va al tmp remoto y se ejecuta) y `fetch_file` (bajar); quien implemente esos tres tiene un transporte completo (ssh, winrm, `community.docker.docker`… y el nuestro). `connection_plugins/lab_docker.py` habla con **la misma flota del 7** por `docker exec`/`docker cp`: compara los inventarios — `inventario_flota.ini` lleva puerto+clave+usuario, `inventario_flota_docker.ini` **no lleva nada**, porque la "credencial" es poder hablar con el daemon. **LA LECCIÓN INCÓMODA**: por esa puerta eres **root sin presentar credencial alguna** (por SSH la flota te hace usuario raso) — el mismo motivo por el que montar `docker.sock` en un contenedor es root regalado. **LA TRAMPA, provocada de verdad**: `become` aquí SOBRA (ya eres root) y además MUERDE (la imagen no trae sudo) — al cambiar de transporte, revisa tus suposiciones de become. Ida y vuelta byte a byte por put/fetch, `changed=0` en la 2ª pasada |
| `playbooks/32_coleccion_propia.yml` | **Colección propia: `galaxy.yml`, build, install y FQCN**. Las 8 extensiones del tour viven sueltas en carpetas `*_plugins/` — se comparten con UN proyecto; una **colección** las empaqueta con nombre y versión para compartirlas con cualquiera (es lo que hay en Galaxy y lo que instala el `requirements.yml` del 8). Aquí se hace el viaje entero **en local**: fuente (`coleccion_lab/laboratorio/utilidades`, con un módulo `lab_eco` y un filtro `etiqueta_lab`) → `ansible-galaxy collection build` (tarball versionado; `galaxy.yml` define el FQCN) → `install -p` (despliegue como **snapshot**: `MANIFEST.json` con hash de cada fichero, así que editar la fuente después NO cambia lo instalado) → consumo por `laboratorio.utilidades.lab_eco`. **LA TRAMPA GORDA, provocada de verdad**: instalar **no basta** — con `ANSIBLE_COLLECTIONS_PATH` apuntando a otro sitio, el mismo playbook falla con "couldn't resolve module"; el clásico *"la instalé y no la ve"* es casi siempre una ruta, no un bug. **Y la letra pequeña**: la palabra clave `collections:` acorta **módulos** (y actions y roles), pero **NO filtros ni tests** — el auxiliar lo fija haciendo reventar `| etiqueta_lab` a secas con `collections:` puesto |
| `playbooks/33_inventory_plugin_a_medida.yml` | **Inventory plugin a medida: la novena extensión — LA FUENTE** (sobre la flota). El arco de tres playbooks se cierra: el 20 descubrió la flota con un **script** (ejecutable + contrato JSON), el 21 apiló el plugin `constructed` de serie, y este escribe el plugin **de verdad** — la misma clase de la que están hechos `aws_ec2` o `community.docker.docker_containers`. `inventory_plugins/lab_flota.py` pregunta a Docker y monta el inventario con la **API** (`add_group`/`add_host`/`set_variable`, sin contrato `--list`/`_meta` que cumplir), se activa por la clave `plugin:` de un YAML de configuración (el despachador que lee `auto`) y declara opciones en `DOCUMENTATION` + `get_option()`. **LA TRAMPA DOBLE, provocada de verdad**: `verify_file` es un portero — el MISMO contenido con un nombre que el plugin no acepta muere en *"could not be verified"*, y la fuente descartada es **WARNING + rc 0 + inventario vacío** (la letra pequeña del 21; por eso `aws_ec2` exige `*.aws_ec2.yml`); y SIN la clave `plugin:`, el YAML bien nombrado **ni siquiera avisa** — el plugin `yaml` se lo queda como inventario vacío legal y el *"Unable to parse"* nunca llega. **Lección extra cazada al probar**: los hosts de `add_host` no traen `inventory_dir` (el `{{ inventory_dir }}` heredado del INI llegaba LITERAL al ssh) — un plugin resuelve las rutas él mismo en `parse()`. Verificación doble como el 20: contrato por fuera (y **script vs plugin: la misma flota por las dos puertas**, pinneado con assert) y **SSH real** a lo descubierto |
| `playbooks/34_dependencias_de_roles.yml` | **Dependencias de roles (`meta/main.yml`) a fondo** — siete escenas, cinco roles de laboratorio cuyo único trabajo es dejar constancia de haberse ejecutado. Un rol declara de qué depende y Ansible lo ejecuta antes que a él: suena a `include_role` con otra sintaxis y no lo es. **La deduplicación es lo que muerde**: dos roles que declaran la misma dependencia la ejecutan **una sola vez** (lo que hace útil una dependencia compartida… y lo que sorprende cuando esperabas que se repitiera), pero la firma es **(rol + parámetros)** — las mismas dependencias con etiquetas distintas corren **dos veces sin `allow_duplicates`** —, y `allow_duplicates: true` (que se lee del meta al cargar, no se decide en runtime) las repite con parámetros idénticos. Por la puerta de `tasks`, `include_role`/`import_role` **no deduplican nunca**: cuatro invocaciones, cuatro ejecuciones. **LA TRAMPA GORDA, provocada de verdad**: un rol **listado explícitamente en la play puede NO ejecutarse** si esa misma firma ya corrió como dependencia transitiva de otro — y Ansible no avisa de nada. Y un contraste con el 28: el **tag del rol SÍ baja a sus dependencias** (el de un `include_tasks` no), comprobado con `--tags` en un auxiliar. **Lección de arnés**: la primera versión del testigo usaba `lineinfile` y mentía — es idempotente, así que contaba 1 donde el rol había corrido 2 veces; **un medidor idempotente no puede contar invocaciones** |
| `playbooks/35_cache_plugin_a_medida.yml` | **Cache plugin a medida: la décima extensión — EL BACKEND**. El playbook 29 *usa* el `jsonfile` de serie para cachear facts entre pasadas; este escribe el plugin que decide **dónde y cómo** se guardan. `cache_plugins/lab_json.py` hereda de `BaseFileCacheModule` (un fichero por host, caducidad con `fact_caching_timeout`, `contains`/`flush` — todo puesto por la base) y solo dice cómo se serializa un valor: `_dump` al escribir, `_load` al leer. **Lo que lo hace VISIBLE frente al de serie**: envuelve los facts en un sobre con marca propia (`_lab_cache` / `stored_by: lab_json`) e **indenta** el JSON, mientras el `jsonfile` escribe el dict pelado en una línea. Se demuestra con órdenes anidadas (como el 28 y el 29): una pasada planta un sello **cacheable** con `ANSIBLE_CACHE_PLUGIN=lab_json`, el playbook comprueba **en disco** que el fichero lleva la firma y es multilínea (prueba de que corrió el nuestro, no el de serie), y **otro proceso** con `gathering=smart` lo recupera de la caché — la persistencia entre procesos por nuestro backend. Los facts se serializan con el sobre `__payload__` de ansible-core 2.21, así que los asserts miran el **texto** del fichero, no una estructura parseada (la lección del 29). Cierra el tour de extensiones en diez piezas + la colección |
| `playbooks/36_ansible_pull.yml` | **ansible-pull: el modelo INVERTIDO**. Todo el laboratorio es push; aquí EL NODO tira de un repo git y se aplica su propio playbook (`cron` + `ansible-pull` = flotas que se configuran solas; por debajo es azúcar sobre el módulo `git` + `ansible-playbook -c local`). El repo "remoto" se fabrica en /tmp y se consume por `file://`. **Todo medido antes de escribirlo**: la convención de nombres (`{fqdn}.yml` → `{hostname}.yml` → `local.yml`) y que **el playbook con nombre de host GANA a `local.yml`** aunque ambos existan — un repo sirve config común y excepciones por máquina con la misma orden de cron; **LA TRAMPA de `--only-if-changed`**: sin commit nuevo no ejecuta nada **y aun así sale con rc 0** ("Repository has not changed, quitting") — una monitorización que lea rc 0 como "config aplicada" se engaña, el estado se mira en el nodo; con un commit nuevo (vacío vale: compara **SHAs**, no contenido) la misma orden vuelve a aplicar; y el repo sin ninguno de los tres nombres falla RUIDOSO ("Could not find a playbook to run.", rc ≠ 0), no como no-op silencioso |
| `playbooks/37_meta_a_fondo.yml` | **El módulo `meta:` a fondo — órdenes AL MOTOR, no a los nodos**. Cuatro verbos, cada uno con su escena y su `assert`, todos medidos contra ansible-core 2.21: **`flush_handlers`** (LA GORDA: un handler notificado **NO corre si la play aborta antes del final** — medio servicio reconfigurado y el `reload` que lo remataba nunca disparado; el playbook lanza DOS órdenes anidadas con el mismo playbook interior, con y sin flush, y demuestra que sin él la marca del handler no aparece y con él sí, aunque el paso siguiente falle), **`end_host`** (termina la play para ESE host y sigue con los demás, **limpio**: `ok`, no `failed`; honra el `when`; se comprueba desde la play siguiente porque tras él no corre nada más en la suya), **`end_play`** (cierra la play para TODOS los hosts — pero **la play SIGUIENTE sí arranca**: cierra una play, no el playbook) y **`clear_facts`** (borra los facts RECOGIDOS pero **NO los de `set_fact`**: son cosas distintas y el assert lo fija; `noop`, el quinto verbo, se nombra sin escena porque su lección es que no hace nada). Tres trampas cazadas al fabricar el playbook interior: el escalar literal de bloque de YAML **recorta la sangría** (una marca escrita al ras del bloque queda en columna 0), un `\n` dentro de un escalar plegado **no se desescapa** (solo lo hacen las comillas dobles; Jinja lo deja literal) y `ANSIBLE_VAULT_PASSWORD_FILE=""` **no desactiva nada**: Ansible resuelve la cadena vacía como el cwd y muere con "can not be a directory" — de ahí el fichero propio en ruta absoluta, como en el 36 |
| `playbooks/38_bucles_a_fondo.yml` | **Bucles a fondo: `loop_control`, la colisión de `item` y el aplanado**. Cinco escenas con `assert`, medidas contra ansible-core 2.21: **la colisión de `item`** (un `include_tasks` con `loop:` cuyo fichero incluido también hace `loop:` PISA la variable — el interior gana, el exterior desaparece y ansible avisa "The variable 'item' is already in use" y sigue; con `loop_control.loop_var: exterior` cada nivel tiene nombre y los valores se combinan: `['1','2','1','2']` frente a `['a-1','a-2','b-1','b-2']`), **`index_var` + `extended: true`** (índice base 0 y `ansible_loop` con `first/last/length/revindex/previtem/nextitem` — la coma-menos-en-el-último sin trucos de Jinja, que dentro de una tarea no existe), **`label`** (sin él la salida de cada vuelta lleva el item ENTERO, secretos incluidos — medido con una orden anidada buscando el secreto en la salida; con `label: "{{ item.nombre }}"` solo el nombre; ojo: `label` es cosmético, `no_log` es lo que protege), **`with_items` aplana un nivel y `loop` no** (`[[1,2],[3]]` → 3 vueltas frente a 2; la migración fiel es `loop: "{{ x | flatten(levels=1) }}"`) y **`pause`** (espera ENTRE vueltas, no antes de la primera: tres vueltas con `pause: 1` tardan ≥ 2 s, medido con marcas de tiempo dentro del playbook). Dos ficheros de tareas en `tasks/` (las dos variantes del include). |

```
ansible-lab/
├── ansible.cfg                          # configuración (inventario por defecto, roles_path...)
├── inventario.ini                       # inventario: localhost con conexión local
├── .ansible-lint                        # configuración del linter (perfil, excepciones)
├── .github/workflows/ci.yml             # CI: lint + ejecución real de los playbooks
├── requirements.yml                     # colecciones de Galaxy que usa el lab
├── inventario_flota.ini                 # inventario multi-host (grupos web/db)
├── inventario_dinamico.py               # inventario dinámico: descubre la flota en Docker (playbook 20)
├── inventario_construido.yml            # capa constructed: grupos/vars derivados (playbook 21)
├── inventario_flota_plugin.yml          # configuración del inventory plugin lab_flota (playbook 33)
├── flota.sh                             # levantar/apagar los 3 nodos Docker
├── multihost/Dockerfile                 # imagen de nodo: Debian + sshd + python3
├── group_vars/
│   ├── all.yml                          # el "suelo" del inventario (playbook 27)
│   ├── web.yml                          # variables del grupo [web]
│   └── db.yml                           # variables del grupo [db]
├── host_vars/
│   └── web1.yml                         # el nivel más específico del inventario (playbook 27)
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
│   ├── 19_filtros_a_medida.yml
│   ├── ...                              # 20-38: un playbook por lección (la tabla de arriba los lista todos)
│   └── tasks/                           # ficheros de tareas de los playbooks 12, 28 y 38
├── filter_plugins/
│   └── lab_filters.py                   # filtros Jinja a medida en Python (playbook 19)
├── callback_plugins/
│   └── lab_resumen.py                   # callback aggregate: resumen JSON por tarea (playbook 22)
├── lookup_plugins/
│   └── lab_fichero.py                   # lookup: lee del controlador (playbook 23)
├── action_plugins/
│   └── lab_marca.py                     # action: corre en el control, orquesta copy (playbook 24)
├── library/
│   └── lab_sello.py                     # módulo: corre en el target, check_mode (playbook 25)
├── vars_plugins/
│   └── lab_cmdb.py                      # vars plugin: la CMDB llega con el inventario (playbook 26)
├── test_plugins/
│   └── lab_tests.py                     # tests de Jinja a medida: clasificar, no transformar (playbook 30)
├── connection_plugins/
│   └── lab_docker.py                    # connection plugin: docker exec como transporte (playbook 31)
├── coleccion_lab/laboratorio/utilidades/ # colección propia: galaxy.yml + módulo + filtro (playbook 32)
├── inventory_plugins/
│   └── lab_flota.py                     # inventory plugin: la fuente como plugin, con verify_file (playbook 33)
├── cache_plugins/
│   └── lab_json.py                      # cache plugin: backend de facts en JSON con sobre propio (playbook 35)
├── vars/
│   ├── cmdb_lab.yml                     # mini-CMDB que lee lab_cmdb (playbook 26)
│   └── secretos.yml                     # secretos CIFRADOS con ansible-vault
├── roles/
│   ├── informe_web/                     # rol: panel HTML del sistema
│   │   ├── tasks/main.yml
│   │   ├── templates/panel.html.j2
│   │   ├── defaults/main.yml
│   │   └── meta/main.yml
│   └── dep_*/                           # cinco roles-testigo: dependencias de meta (playbook 34)
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
ansible-playbook -i inventario_dinamico.py playbooks/20_inventario_dinamico.yml
ansible-playbook -i inventario_dinamico.py -i inventario_construido.yml playbooks/21_inventario_por_capas.yml
ansible-playbook -i inventario_flota_plugin.yml playbooks/33_inventory_plugin_a_medida.yml
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
