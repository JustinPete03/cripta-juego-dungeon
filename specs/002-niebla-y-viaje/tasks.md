# Tareas: Niebla de Guerra y Viaje Automático («ir a»)

**Feature**: `002-niebla-y-viaje`
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

---

## Fase 1: Estructura de Datos `MapaConocido`

- [x] T001 [FR-011, FR-012] Implementar `MapaConocido` en `model/MapaConocido.py` con estados `EXPLORADA`, `AVISTADA`, `DESCONOCIDA` sobre `Tabla` propia.
- [x] T002 [FR-013] Implementar memoria de puertas con actualización por observación directa en salas contiguas.
- [x] T003 [FR-015] Conectar registro de inversas en `Diario` para reversibilidad completa sin copias de estado.
- [x] T004 [FR-011, FR-013, FR-015] Escribir pruebas unitarias de `MapaConocido` y reversibilidad.

---

## Fase 2: Integración en el Modelo y Mecánica de la Antorcha

- [x] T005 [FR-012] Inicializar `MapaConocido` en `Modelo._prepararEstado` e iniciar sala inicial como explorada en t=0.
- [x] T006 [FR-013] Actualizar observación de puertas al moverse (`_aplicarMover`) o abrir puertas (`_aplicarAbrir`).
- [x] T007 [FR-014] Implementar efecto de la antorcha: al entrar a una sala con antorcha encendida, explorar vecinas de forma reversible sin activar enemigos/trampas.
- [x] T008 [FR-014, FR-015] Escribir pruebas de antorcha y reversión con pergamino de retroceso.

---

## Fase 3: Cálculo de Rutas sobre Mapa Conocido

- [x] T009 [FR-017] Implementar `dijkstraSubgrafoConocido(salaOrigen, salaDestino, salasIndice, mapaConocido)` en `model/Dijkstra.py` con desempate determinista por menor ID de vecina.
- [x] T010 [FR-016, FR-017] Escribir pruebas unitarias de ruta sobre subgrafo conocido y manejo de puertas recordadas.

---

## Fase 4: Comando `ir a <sala>` y Comando `mapa`

- [x] T011 [FR-016, FR-018, FR-019] Implementar ejecución de `ir a <sala>` en `controller/ControladorJuego.py` con parada ante enemigos, daño o puertas cerradas.
- [x] T012 [FR-020] Implementar comando `mapa` en `view/Consola.py` y `controller/ControladorJuego.py`.
- [x] T013 [FR-016, FR-018, FR-019] Escribir pruebas de aceptación completas para `ir a` (todos los casos del Apéndice B).

---

## Fase 5: Benchmarks y Documentación

- [x] T014 [PR-003, PR-004] Crear `bench/BenchNiebla.py` midiendo costo de consulta a mapa conocido y cálculo de paso de «ir a» (< 5 ms).
- [x] T015 Actualizar `DECISIONES.md` (sección 5.3) y `PROMPTS_LLM.md`.
