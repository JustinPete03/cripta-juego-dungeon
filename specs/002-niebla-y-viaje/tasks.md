# Tareas: Niebla de Guerra y Viaje Automático («ir a»)

**Feature**: `002-niebla-y-viaje`  
**Spec**: [spec.md](spec.md)  
**Plan**: [plan.md](plan.md)

---

## Fase 1: Estructura de Datos `MapaConocido`

- [x] T001 [FR-011, FR-012] Implementar `MapaConocido` en `model/MapaConocido.py` con estados `ESTADO_EXPLORADA`, `ESTADO_AVISTADA` y `ESTADO_DESCONOCIDA` sobre `Tabla` propia.
- [x] T002 [FR-013] Registrar el último estado observado de cada puerta desde sus salas contiguas. Distinguir entre abierta, cerrada y sin observar mediante `estadoPuertaRecordada(uId, vId)`.
- [x] T003 [FR-015] Conectar registro de inversas en `Diario` para reversibilidad completa sin copias de estado.
- [x] T004 [FR-011, FR-012, FR-013, FR-015] Escribir pruebas de estados del mapa, memoria de puertas y reversibilidad en `tests/test_niebla_viaje.py`.

---

## Fase 2: Integración en el Modelo y Mecánica de la Antorcha

- [x] T005 [FR-012] Inicializar `MapaConocido` en `Modelo._prepararEstado` e iniciar sala inicial como explorada en t=0.
- [x] T006 [FR-013] Actualizar observación de puertas al moverse (`_aplicarMover`) o abrir puertas (`_aplicarAbrir`). Al entrar, `explorarSala(destino)` registra las puertas de la sala del jugador.
- [x] T007 [FR-014] Revelar las vecinas con `marcarExplorada()` cuando la antorcha está encendida. Registrar la revelación para el retroceso y dejar intacta la memoria de puertas ajenas a la sala del jugador.
- [x] T008 [FR-014, FR-015] Probar que la antorcha revela B al entrar en A, observa A–B y deja B–C sin observar. Verificar la reversión de la exploración con el pergamino.

---

## Fase 3: Cálculo de Rutas sobre Mapa Conocido

- [x] T009 [FR-017] Usar `calcularDistancias` y `elegirPrimerPaso` en `elegirPasoViajeAutomatico(salaActual, salaDestino, salasIndice, mapaConocido)`. Filtrar por salas exploradas y puertas recordadas abiertas. Desempatar por menor ID de vecina (K-05).
- [x] T010 [FR-016, FR-017] Probar que «ir a» descarta una puerta sin observar aunque esté abierta. Verificar el costo mínimo y el desempate en `tests/test_rutas_invalidacion.py`.

---

## Fase 4: Comando `ir a <sala>` y Comando `mapa`

- [x] T011 [FR-016, FR-018, FR-019] Validar y ejecutar los pasos de «ir a» en `Modelo.validarViaje` y `Modelo.pasoViaje`. Registrar el daño durante el paso y delegar al controlador la repetición de pasos, la bitácora y la presentación del motivo de detención.
- [x] T012 [FR-020] Mostrar las salas exploradas, las avistadas y el estado recordado de cada puerta. Mostrar «sin observar» cuando corresponda.
- [x] T013 [FR-016, FR-018, FR-019] Probar el rechazo de destinos no explorados, el recálculo por puertas cerradas, la detención al encontrar enemigos y la detención por daño aunque se recupere vida en el mismo paso. Verificar que iniciar desde una sala con enemigos no cambia la posición ni el reloj. Las suites `tests/test_niebla_viaje.py` y `tests/test_rutas_invalidacion.py` pasaron juntas: 40 pruebas en 2.28 s.

---

## Fase 5: Benchmarks y Documentación

- [x] T014 [PR-003, PR-004] Medir consultas al mapa conocido, explorar cinco salas nuevas por repetición y medir el cálculo de un paso de «ir a» sobre el mapa conocido completo de la cripta de referencia. `cripta-06` (300 salas): promedio de 1.098 ms y peor tiempo de 2.115 ms frente al límite de 5 ms.
- [x] T015 Actualizar `DECISIONES.md` (sección 5.3) y `PROMPTS_LLM.md`.