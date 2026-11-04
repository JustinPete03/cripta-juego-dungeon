# Tareas: Verificación de Resolubilidad

**Feature**: `003-resolubilidad`
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

---

## Fase 1: Adaptadores de Red y Cliente para Llaves

- [x] T001 [FR-021] Añadir `obtenerLlaves(idCripta)` a la interfaz `ClienteCripta` en `adapters/clienteCripta.py`.
- [x] T002 [FR-021] Implementar `obtenerLlaves` en `adapters/clienteHttp.py` (`GET /criptas/{id}/llaves`).
- [x] T003 [FR-021] Implementar `obtenerLlaves` en `adapters/clienteOffline.py` leyendo archivo de disco o infiriendo desde el contenido.

---

## Fase 2: Algoritmo de Verificación y Detección de Ciclos

- [x] T004 [FR-022, FR-023, FR-024] Implementar `verificarResolubilidad` en `model/Resolubilidad.py` con recorrido incremental $O(V + E + K)$ y orden determinista de llaves.
- [x] T005 [FR-025] Implementar detección de ciclos de dependencia de llaves e identificación de frontera bloqueada con ubicación de llaves.
- [x] T006 [FR-022, FR-024, FR-025] Escribir pruebas unitarias del algoritmo de resolubilidad y detección de ciclos en `tests/test_resolubilidad.py`.

---

## Fase 3: Integración CLI y Flujo de Partida

- [x] T007 [FR-026] Añadir bandera `--verificar <idCripta>` en `main.py` para ejecutar solo la verificación sin interfaz interactiva.
- [x] T008 [FR-027] Añadir bandera `--forzar` en `main.py` y comprobación al inicio de partida normal.
- [x] T009 [FR-026, FR-027] Escribir pruebas de aceptación de las banderas CLI y control de inicio de partida.

---

## Fase 4: Benchmarks y Documentación

- [x] T010 [PR-005, PR-006] Implementar `bench/BenchResolubilidad.py`: recorrido incremental vs repetido ingenuo, y verificar tiempo < 200 ms.
- [x] T011 Actualizar `DECISIONES.md` (sección 5.4) y `PROMPTS_LLM.md`.
