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
