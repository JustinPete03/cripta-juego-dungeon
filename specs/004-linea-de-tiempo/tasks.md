# Tareas: Línea de Tiempo y Puntos de Control

**Feature**: `004-linea-de-tiempo`
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

---

## Fase 1: Estructura de Línea de Tiempo y Checkpoints

- [x] T001 [FR-029, FR-036] Implementar `model/LineaTiempo.py` con almacenamiento de puntos de control cada $K$ acciones y lista de acciones del jugador.
- [x] T002 [FR-029, FR-036] Integrar `LineaTiempo` en `model/Juego.py` (`Modelo`), inicializando el punto de control inicial en `iniciarPartida()` y registrando puntos de control cada $K$ acciones.
- [x] T003 [FR-034] Implementar `recortar()` en `LineaTiempo` e invocarlo en `_retroceder()` de `model/Juego.py` al usar un pergamino de retroceso.

---

## Fase 2: Consultas Históricas y Reconstrucción de Estados

- [x] T004 [FR-030, FR-031, FR-037] Implementar la re-simulación hacia adelante en `model/LineaTiempo.py` para reconstruir el estado en el instante $t$ o acción $\#k$ aplicando a lo sumo $K$ acciones.
- [x] T005 [FR-030, FR-031, FR-032, FR-033] Implementar `consultarHistoriaTiempo(t)` y `consultarHistoriaAccion(k)` en `model/Juego.py` con formateo del resumen y validación de consultas futuras.
- [x] T006 [FR-030, FR-031, FR-033] Integrar los comandos interactivos `historia <t>` e `historia #k` en `controller/ControladorJuego.py` y actualizar el texto de ayuda.

---

## Fase 3: Persistencia y Replay no Interactivo

- [x] T007 [FR-035] Implementar bandera `--hasta <t>` en `main.py` y actualizar `reproducir()` en `controller/ControladorJuego.py` para emitir el resumen sin instanciar la vista.
- [x] T008 [FR-036] Implementar bandera `--checkpoint-cada K` en `main.py` (con $K=20$ por defecto).
- [x] T009 [FR-038] Actualizar `adapters/guardadoPartida.py` con `VERSION_FORMATO = 3`, sección `"linea_tiempo"` y detección y rechazo de archivos versión 2 de la primera parte.

---

## Fase 4: Pruebas, Benchmarks y Documentación

- [x] T010 [FR-029 a FR-038] Escribir suite de pruebas de aceptación en `tests/test_linea_tiempo.py` cubriendo todos los escenarios del Apéndice B.
- [x] T011 [PR-007, PR-008] Implementar `bench/BenchLineaTiempo.py`: medición de memoria y tiempo para varios valores de $K$ (e.g. 5, 20, 50, $\infty$) y verificación de consulta en partida de 5 000 acciones en $< 50$ ms. Integrar en `main.py --bench`.
- [x] T012 Actualizar `DECISIONES.md` (secciones 5.5 y 5.6) y `PROMPTS_LLM.md`.

---

## Fase 5: Refinamientos, Mediciones y Telemetría Pendientes (Jorge)

- [x] T013 [FR-034] [US2] [L-01] Corregir el comentario del método `recortar()` en `model/LineaTiempo.py` para documentar que el costo real es proporcional a la cantidad de acciones descartadas ($O(\Delta)$ con $\Delta \le 5$).
- [x] T014 [FR-029, FR-036] [US4] [L-02] Optimizar `registrarPuntoControl` en `model/LineaTiempo.py` para comparar únicamente con el último punto `self._puntosControl[-1]` aprovechando el invariante de orden creciente, sin recorrer toda la lista.
- [x] T015 [FR-032] [US1] Reescribir la prueba de red y caché en `tests/test_linea_tiempo.py` usando un contador real de solicitudes (envolviendo métodos de acceso a datos del proveedor) y con la caché real, comprobando que falle si se fuerza una solicitud a propósito dentro de una consulta de historia.
- [ ] T016 [PR-007, FR-030, FR-031] [US1] [L-03] Medir la consulta de historia en `bench/BenchLineaTiempo.py` con la cripta más grande disponible y 5 000 acciones, y decidir con esos datos entre reutilizar el esqueleto ya construido o reconstruir hacia atrás con inversas (solo medir y decidir, sin implementar opción).
- [x] T017 [PR-007] [US1] [L-04] Actualizar `bench/BenchLineaTiempo.py` para utilizar el peor caso por consulta (tiempo máximo observado) al verificar el cumplimiento del límite constitucional de 50 ms.
- [ ] T018 [FR-034, PR-008] [US2] [J-02] Repetir las mediciones de retroceso con decenas de cazadores activos en `bench/BenchLineaTiempo.py` y registrar la comparativa contra la Parte I en `DECISIONES.md` (Nota: Requiere datos de medición del módulo de cazadores de Keilor; no modifica archivos de otros integrantes).
- [ ] T019 [PR-007, FR-030, FR-037] [US1] Implementar en `model/LineaTiempo.py` la opción elegida en T016 y comprobar que el peor caso de historia queda por debajo de 50 ms (si la medición demuestra que no hace falta cambiar nada, cerrar con ese dato; depende de T016).
- [x] T020 [FR-031] [US1] Probar en `tests/test_linea_tiempo.py` que historia #k con k igual a las acciones realizadas más 1 muestra el estado actual antes de la decisión pendiente (los casos k=0 y k excesivo ya tienen pruebas).
- [x] T021 [FR-033] [US1] Probar en `tests/test_linea_tiempo.py` que historia rechaza t menor que 0 con mensaje de error, que rechaza k negativo y que t igual a 0 sí es válido (el caso k=0 ya está probado).
- [x] T022 [FR-029, FR-036] [US4] Agregar prueba en `tests/test_linea_tiempo.py` de los invariantes de los puntos de control: orden creciente de acciones y de reloj, y el punto de control 0 siempre presente desde `iniciarPartida()`.
- [x] T023 [FR-029, FR-036] [US4] [L-05] Reemplazar primero todos los accesos por corchetes (cp["snapshot"], cp["numAccion"], item["accion"], item["reloj"], p["numAccion"] y similares) por acceso a atributos en `model/LineaTiempo.py` y `tests/test_linea_tiempo.py`; después, quitar `__getitem__` y `__setitem__` de `PuntoControl` y `RegistroAccion`, asegurando que pasen todas las pruebas y actualizando `plan.md` solo si los menciona.
