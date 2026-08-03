# Changelog — laboratorio.utilidades

Toda colección publicable lleva changelog: la versión de `galaxy.yml` sola no
dice QUÉ cambió, y quien la instala compara versiones para decidir si le
merece la pena. `ansible-lint` lo exige (`galaxy[no-changelog]`) y por eso
existe este fichero — la propia regla es parte de la lección del playbook 32.

## 1.0.0

- Primera versión: módulo `lab_eco` (eco etiquetado, check-mode safe) y filtro
  `etiqueta_lab` (antepone una etiqueta configurable).
