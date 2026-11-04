# Tareas: Terreno y Cazador

**Feature**: `001-terreno-y-cazador`
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

---

## Fase 1: Modelo de datos (costo de salida y atributos del cazador)

- [x] T001 [FR-001] Agregar campo `costo` a `Salida` en `model/Entidades.py` (default 100).
- [x] T002 [FR-010] Agregar campo `rango` a `Enemigo` en `model/Entidades.py` (default 0).
- [x] T003 [FR-001] En `Juego._construirSalas`, leer `info.get("costo", 100)` y pasarlo a `Salida`.
- [x] T004 [FR-010] En `Juego._asegurarContenido`, leer `ficha.get("rango", 0)` y asignarlo al `Enemigo`.

---

## Fase 2: Costo de movimiento para todos los actores

- [x] T005 [FR-002] Modificar `_aplicarMover` para que la acción del jugador use el costo de la salida en lugar de `COSTOS[ACC_MOVER]`.
- [x] T006 [FR-004] Modificar `_moverEnemigo` y `_programarEnemigo` para que el enemigo use el costo de la salida atravesada.
- [x] T007 [FR-002, FR-004] Escribir pruebas de movimiento con costo variable: jugador, errante, rastreador.

---

## Fase 3: Dijkstra propio y montículo binario

- [x] T008 [FR-005] Implementar `MinHeapDijkstra` en `model/Dijkstra.py`: montículo binario de pares (distancia, id) con disminuirClave, usando `Tabla` propia para posiciones.
- [x] T009 [FR-005] Implementar `dijkstraInverso(indiceSalas, salaObjetivoId)`: Dijkstra inverso desde la sala del jugador, devuelve Tabla de distancias y Tabla de predecesores.
- [x] T010 [FR-005] Escribir pruebas unitarias del montículo y de Dijkstra sobre grafos sintéticos.

---

## Fase 4: Comportamiento del cazador

- [x] T011 [FR-005, FR-008] Implementar `elegirDestinoCazador(enemigo, distancias, indiceSalas)` en `model/Cazador.py`.
- [x] T012 [FR-005] Integrar en `Juego._enemigoSeComporta`: caso `"cazador"` que consulta distancias y llama a `elegirDestinoCazador`.
- [x] T013 [FR-007] Implementar invalidación: bandera `_rutasInvalidas` en el modelo, activada por apertura/cierre de puertas y movimiento del jugador.
- [x] T014 [FR-005, FR-006, FR-007] Escribir pruebas del cazador: ataca en misma sala, espera sin ruta, espera fuera de rango, sigue ruta mínima, desempate por menor id, puerta se cierra entre turnos.

---

## Fase 5: Vista y presentación

- [x] T015 [FR-009] Actualizar `view/presentacion.py` para incluir costos de salida en la instantánea.
- [x] T016 [FR-009] Actualizar `view/Consola.py` para mostrar costos de salida y etiquetar cazadores.

---

## Fase 6: Benchmarks

- [x] T017 [PR-001, PR-002] Crear `bench/BenchCazador.py`: Dijkstra compartido vs. individual, rango variable, invalidación vs. recálculo.
- [x] T018 [PR-001] Verificar ciclo de eventos < 20 ms con 30 cazadores activos.
