# Tareas: Rutas ponderadas e invalidación de rutas

**Feature**: `005-rutas-e-invalidacion`
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)
**Responsable**: Keilor Baltodano (salvo donde se indica)

Convenciones:
- `[x]` hecha, `[ ]` pendiente.
- Entre corchetes, los requisitos que atiende.
- **Depende de** indica qué tareas deben estar terminadas antes.
- Cada tarea termina con `pytest` completo en verde.

---

## Fase 1: Línea base de mediciones

- [x] **T001** [PR-011, PR-012, PR-013] Reescribir `bench/BenchCazador.py`: cuadrículas sintéticas deterministas por semilla; cálculo individual correcto (distancia + primer salto) verificado contra el compartido antes de medir; rango pequeño frente a grande con 100, 1024 y 5041 salas; modelo real con todos los cazadores activados y contadores de decisiones y búsquedas; escenarios de puertas A, B y C; ciclo de eventos con 30 y 60 cazadores, con mediana, p95 y peor caso. (Corrige K-01 y K-02.)
- [x] **T002** [PR-009, PR-010] Guardar la salida del bench con el código actual en `mediciones-antes.txt`, como línea base para DECISIONES 5.1 y 5.2. **Depende de** T001.

## Fase 2: Contrato con el motor (archivos de Justin; implementado por Keilor para revisión de Justin)

- [x] **T003** [FR-041] *(revisión de Justin)* `Puerta` guarda `salaA`, `salaB` y `costo` al unificarse en `Juego._construirSalas`. Prueba: para cada puerta, sus dos salas tienen una salida que la usa, con ese costo.
- [x] **T004** [PR-010] *(revisión de Justin)* `Sala` guarda `indice` (su posición en el índice ordenado) al terminar `_construirSalas`. Prueba: `salas.enPosicion(s.indice) is s` para toda sala.

## Fase 3: Núcleo de búsqueda (`model/Dijkstra.py`)

- [x] **T005** [PR-010] `EspacioBusqueda` con arreglos de distancia, sello y sala, creados una vez por su dueño; `calcularDistancias(..., espacio)` los usa; `de(sala)` devuelve `None` si el sello no es el de la búsqueda o si supera la cota, y lanza error si las distancias quedaron obsoletas. Sin espacio se usa `Tabla`. **Depende de** T004.
- [x] **T006** [FR-043, PR-010] `calcularDistancias(origen, puedeUsar, cota=None, espacio=None)`: Dijkstra con `MinHeapDijkstra` y eliminación perezosa; recorre con `salida.destino`; se detiene al extraer una distancia mayor que la cota. **Depende de**: nada; usa `Distancias` con `Tabla` y T005 la optimiza después.
- [x] **T007** [FR-042, FR-044] `elegirPrimerPaso(sala, distancias, puedeUsar)`: vecina de menor id que cumple `costo + dist(v) = d`; hacia ella, la salida más barata, y si empatan, la primera en orden N, S, E, O (spec Q4). **Depende de** T006.
- [x] **T008** [FR-042, FR-043] Pruebas del núcleo en `tests/test_rutas_invalidacion.py`: grafo con pesos; cuadrícula con todas las rutas de igual costo (US-1 escenario 10); dos salidas hacia la misma vecina (Q4); corte por cota sin cambiar decisiones dentro de ella. **Depende de** T007.

## Fase 4: Cazador con cota (`model/Cazador.py`)

- [x] **T009** [FR-042] `elegirPasoCazador` usa `elegirPrimerPaso`; las reglas de atacar y esperar de 001 no cambian. Avisar a Justin. **Depende de** T007.
- [x] **T010** [FR-043, PR-010] La búsqueda del cazador se acota al mayor rango entre los cazadores activos y vivos. **Depende de** T009.
- [x] **T011** [FR-039] Pruebas: rango exactamente igual al costo (US-1 escenario 11); las pruebas existentes de `test_terreno_cazador.py` siguen pasando sin cambios. **Depende de** T010.

## Fase 5: Componente de rutas e invalidación fina (`model/RutasCazador.py`)

- [x] **T012** [FR-039, FR-040] `RutasCazador.distanciasPara(salaJugador, rangoNecesario, cotaActual)`: recalcula si no hay cálculo válido, si cambió la sala del jugador o si `rangoNecesario` supera la cota usada; contador `recalculos`. **Depende de** T006, T010.
- [x] **T013** [FR-041] `puertaCambio(puerta, seAbrio)` con las reglas de cierre (¿está en algún camino mínimo?) y de apertura (¿aparece un camino más corto?); distancia desconocida o mayor que la cota = infinito. **Depende de** T003, T012.
- [x] **T014** [FR-040] `invalidar()`; llamarlo en `Juego._retroceder` y `Juego.restaurarEstado`. **Depende de** T012.
- [x] **T015** [FR-039] *(revisión de Justin)* Conectar en `Juego`: reemplazar `_rutasCazadorValidas` y `_distanciasCazador` por `RutasCazador`; `puertaCambio` en `_aplicarAbrir` y `_manejarCierrePuerta`. **Depende de** T013, T014.
- [x] **T016** [FR-039, FR-040, FR-041] Pruebas de US-1, escenarios 1 a 9: puerta de la ruta que se cierra entre turnos (por la agenda, no a mano); puerta lejana; atajo; apertura sin efecto; jugador que se mueve; pergamino; otros eventos; carga de partida; cazador de rango mayor activado. **Depende de** T015.
- [x] **T017** [FR-039, FR-040, FR-041] Prueba oráculo (US-1 escenario 12): cientos de turnos con semilla y puertas que cambian al azar; en cada decisión, «con caché» = «desde cero sin cota». **Depende de** T015.

## Fase 6: «ir a» sobre el núcleo (con Jurnier)

- [x] **T018** [FR-044] `elegirPasoViajeAutomatico` usa `calcularDistancias` desde el destino con el `puedeUsar` del conocimiento del jugador y `elegirPrimerPaso`; misma firma pública. **Depende de** T007.
- [x] **T019** [FR-044] Pruebas de US-3 (escenarios 1 y 2); las pruebas de `test_niebla_viaje.py` siguen pasando. **Depende de** T018.
- [x] **T020** [FR-044] `dijkstraDesde` y `dijkstraSubgrafoConocido` siguen existiendo porque las usan pruebas de 001 y 002, pero como envoltorios del núcleo: ya no hay una segunda implementación del algoritmo (plan D6). **Depende de** T015, T018.

## Fase 7: Mediciones finales

- [x] **T021** [PR-012] En `BenchCazador`, agregar la estrategia «invalidación fina» a la sección 3 y adaptar `_cambiarPuerta` y `_Contador` a `RutasCazador`. **Depende de** T015.
- [x] **T022** [PR-010] Sección nueva: `Tabla` frente a arreglo con sellos sobre el mismo escenario de la sección 2 (plan D3). Si el arreglo no mejora de forma medible, volver a `Tabla` y documentarlo. **Depende de** T006.
- [ ] **T023** [PR-009, PR-010, PR-012] Medir en Windows (Python del `.venv`, sin otros programas abiertos) la versión de antes (commit `8c80884`) y la final; guardar `mediciones-antes.txt` y `mediciones-despues.txt`. El entorno Linux de la máquina dio resultados demasiado variables entre corridas. **Depende de** T021, T022.

## Fase 8: Documentación

- [x] **T024** [FR-043] Prueba de simetría sobre las criptas de demostración: toda salida tiene su inversa con la misma puerta y el mismo costo (supuesto de la spec). Encontró conexiones con direcciones no opuestas que no compartían puerta; corregido en `_construirSalas` (plan D7).
- [ ] **T025** Reescribir DECISIONES 5.1 y 5.2 con los números de `mediciones-antes.txt` y `mediciones-despues.txt`; indicar qué cambió respecto al plan original de 001 y qué medición lo motivó; incluir la demostración de las reglas de D5. **Depende de** T023.
- [x] **T026** Si la implementación se apartó del plan, corregir primero `plan.md` y `tasks.md` (commit aparte) y luego DECISIONES.
