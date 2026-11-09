# Plan de implementación: Rutas ponderadas e invalidación de rutas

**Rama**: `005-rutas-e-invalidacion` | **Fecha**: 2026-11-08 | **Spec**: [spec.md](spec.md)
**Responsable**: Keilor Baltodano
**Coordinación**: Justin (motor y entidades), Jurnier («ir a»)

---

## Resumen

Hoy el cazador usa un Dijkstra propio desde la sala del jugador que recorre **toda** la cripta, con una bandera que se invalida ante **cualquier** cambio de puertas. El código de «ir a» tiene una segunda copia de la búsqueda. Los benchmarks no miden lo que dicen: el cálculo «individual» usa distancias desde el cazador, y el ciclo de 20 ms no ejecuta ningún turno de cazador.

Este plan:

1. Unifica la búsqueda en un **núcleo único** que usan el cazador e «ir a».
2. La **acota** al mayor rango activo (PR-010).
3. Reemplaza la bandera por un **componente de rutas** con invalidación fina demostrable (FR-041).
4. Rehace el **bench** y agrega una **prueba oráculo** (FR-039, PR-011 a PR-013).

---

## Verificación de la constitución

| Principio | Estado | Cómo se cumple |
|---|---|---|
| I. Estructuras propias | PASA | Montículo binario propio; distancias en un arreglo propio sobre `list` (o `Tabla` si el bench no justifica el cambio). Sin `heapq`, `dict`, `set` ni bibliotecas de grafos. |
| II. Determinismo | PASA | Desempate por menor id de vecina y orden de direcciones N, S, E, O; las criptas del bench se generan con `random.Random(semilla)`. |
| III. MVC | PASA | Todo vive en `model/`; el bench no instancia la vista. |
| IV. Sin datos de una cripta | PASA | Rangos y costos se leen de fichas y esqueleto. |
| VI. Rendimiento con `--bench` | PASA | Cada decisión de este plan tiene su medición (sección «Mediciones planificadas»). |
| VII. Spec antes que código | PASA | `spec.md` confirmado en el commit `spec(005)` antes de cualquier cambio de código. |

---

## Decisiones de diseño

### D1. Algoritmo: Dijkstra con montículo binario propio y eliminación perezosa

Los costos no son uniformes (§3.1), así que contar salas no sirve.

| Alternativa | Complejidad | Decisión |
|---|---|---|
| BFS (contar salas) | O(V + E) | Descartada: ignora el costo (falla el caso «menos salas pero mayor costo»). |
| BFS sobre aristas unitarias (partir cada salida en `costo` pasos) | O(suma de costos) | Descartada: con costos de 250 o más multiplica el trabajo. |
| Bellman-Ford | O(V · E) | Descartada: innecesaria con costos positivos. |
| Dijkstra con montículo y **disminuir clave** (mapa de posiciones) | O((V + E) log V) | Descartada: mismo orden que la eliminación perezosa, pero exige mantener un mapa de posiciones en cada intercambio del montículo. |
| **Dijkstra con montículo y eliminación perezosa** | O((V + E) log E), con E ≤ 4V | **Elegida**: reutiliza el `MinHeapDijkstra` existente; las entradas obsoletas se descartan al extraerlas. |

El montículo guarda pares (distancia, id). Al empatar en distancia, sale primero el menor id, pero el desempate de la regla **no** depende de eso (ver D4).

### D2. Dirección y alcance: una búsqueda compartida desde el jugador, acotada al mayor rango activo

- **Desde el jugador.** Todos los cazadores persiguen la misma sala. Como cada salida comparte puerta y costo con su inversa (§3.1), la distancia del jugador a una sala es igual a la distancia de esa sala al jugador. Una sola búsqueda da `dist(v, jugador)` para **todas** las salas, que es justo lo que pide la regla de §3.2.
- **Acotada.** La búsqueda se detiene al extraer una distancia mayor que la **cota** = mayor rango entre los cazadores activos y vivos (spec Q2). El costo queda proporcional a la región dentro de la cota (PR-010) y no al tamaño de la cripta.
- **Por qué la cota no cambia decisiones.** Si `d(u) ≤ rango ≤ cota`, u y toda vecina v con `costo(u, v) + dist(v) = d(u)` tienen distancia `≤ cota`, así que se extrajeron antes del corte y su valor es definitivo. Todo valor guardado mayor que la cota se trata como **desconocido (infinito)**: puede ser provisional por la eliminación perezosa.
- **Alternativa: una búsqueda por cazador** (desde su sala, con la etiqueta (distancia, primer salto) para respetar el desempate). Se implementa **solo en el bench** como comparación (PR-012). Con N cazadores cuesta N búsquedas por ciclo, frente a una sola compartida.

### D3. Distancias: arreglo indexado por sala con «sello» de búsqueda

Hoy las distancias se guardan en `Tabla`, que calcula `str(clave)` y djb2 en cada consulta. Además, cada extracción hace `salasIndice.buscar(id)`, una búsqueda binaria.

- **Decisión**: cada `Sala` recibe un `indice` fijo (su posición en el índice ordenado) al construir la cripta. Las distancias se guardan en una `list` del tamaño de la cripta, creada una sola vez, junto a una lista de **sellos**: la distancia de una sala solo vale si su sello coincide con el número de la búsqueda actual. Así no hay que reinicializar el arreglo en cada búsqueda, y el costo sigue siendo proporcional a las salas examinadas (PR-010).
- La búsqueda recorre usando `salida.destino` (una referencia directa), sin buscar por id.
- **Alternativa**: mantener `Tabla`. Se mide en el bench (K-06). **Si el arreglo no mejora de forma medible, se mantiene `Tabla`** y se documenta.

### D4. Desempate: un solo auxiliar para el cazador y para «ir a»

`elegirPrimerPaso(sala, distancias, puedeUsar)`:

1. `d = dist(sala)`; si es desconocida, no hay ruta.
2. Entre las salidas de la sala que `puedeUsar` acepta, las candidatas son las que cumplen `costo + dist(destino) = d`.
3. Se elige la **vecina de menor id**. Si hay varias salidas hacia esa vecina, la de menor costo, y si empatan, la primera en orden N, S, E, O (spec Q4). `Sala.salidas` ya está en ese orden.

El resultado depende solo de las distancias y de las salidas actuales, no del orden de exploración (FR-042).

### D5. Componente de rutas del cazador con invalidación fina

Nuevo módulo `model/RutasCazador.py`, dueño de la caché que hoy son la bandera `_rutasCazadorValidas` y `_distanciasCazador` de `Juego`.

**Estado guardado**: las distancias, la sala del jugador usada, la cota usada y si el cálculo es válido.

**`distanciasPara(salaJugador, rangoNecesario)`** recalcula si:
- no hay un cálculo válido; o
- la sala del jugador cambió (se compara en cada consulta, así que movimientos, pergamino y carga quedan cubiertos sin depender de enganches); o
- `rangoNecesario` supera la cota usada (se activó un cazador de rango mayor; FR-040, escenario 9).

**`puertaCambio(puerta, seAbrio)`**, llamada desde `Juego` cuando una puerta cambia. Con u y v, las salas de la puerta, y c, su costo (una distancia desconocida o mayor que la cota cuenta como ∞):
- **Cierre**: si **no** se cumple `dist(u) + c = dist(v)` ni `dist(v) + c = dist(u)`, la salida no está en ningún camino mínimo y la tabla sigue válida. Si se cumple alguna, se invalida.
- **Apertura**: si **no** se cumple `dist(u) + c < dist(v)` ni `dist(v) + c < dist(u)`, no aparece ningún camino más corto y la tabla sigue válida. Si se cumple alguna, se invalida.

**`invalidar()`**: se llama en `_retroceder` (el pergamino revierte puertas sin pasar por `puertaCambio`) y en `restaurarEstado` (defensivo).

**Por qué basta con saber si la tabla cambió.** La decisión del cazador = f(tabla de distancias, salidas actuales de su sala), y las salidas actuales se leen en vivo en cada decisión (D4). Si la tabla no cambia, la decisión es la misma que la de un cálculo desde cero (FR-039, FR-041). La demostración completa de las dos reglas va en DECISIONES 5.2.

**Eventos que no invalidan**, porque la tabla depende solo de (sala del jugador, puertas, costos): movimientos y muertes de otros actores, cambios de velocidad, daño y efectos (FR-040, escenario 7).

**Alternativas** (medidas en el bench, PR-012): recalcular siempre; bandera gruesa (invalidar ante cualquier puerta, como hoy); invalidación fina (elegida).

### D6. «ir a» usa el mismo núcleo, sin caché

- `elegirPasoViajeAutomatico` llama al núcleo **desde el destino** sobre el conocimiento del jugador: `puedeUsar` = «el destino de la salida está explorado y la puerta se recuerda abierta», y sin cota. Luego aplica el mismo `elegirPrimerPaso` (FR-044).
- Sin caché: el conocimiento cambia en casi cada paso (exploración y memoria de puertas) y §3.4 exige recalcular antes de cada paso. El límite de 5 ms se verifica en el bench de Jurnier.
- La regla `puedeUsar` la define Jurnier (incluida la corrección N-02 de puertas sin observar); este plan solo fija la interfaz.

---

## Interfaces compartidas (contrato)

```text
model/Dijkstra.py
  calcularDistancias(origen, cantidadSalas, puedeUsar, cota=None) -> Distancias
      origen: Sala; puedeUsar(salaActual, salida) -> bool; cota: int o None
  Distancias.de(sala) -> int o None          # None = desconocida o mayor que la cota
  Distancias.salasExaminadas -> int          # para medir PR-010
  elegirPrimerPaso(sala, distancias, puedeUsar) -> Salida o None

model/RutasCazador.py
  RutasCazador(cantidadSalas)
  distanciasPara(salaJugador, rangoNecesario, rangoMaximoActivo) -> Distancias
  puertaCambio(puerta, seAbrio)
  invalidar()
  recalculos -> int                          # contador para el bench
```

**Cambios que hace Justin (acordados), o Keilor con su aviso:**
- `Puerta` guarda `salaA`, `salaB` y `costo` al unificarse en `_construirSalas`.
- `Sala` guarda `indice`, su posición en el índice ordenado, al terminar `_construirSalas`.

---

## Módulos afectados

| Módulo | Dueño | Cambio |
|---|---|---|
| `model/Dijkstra.py` | Keilor | Núcleo único `calcularDistancias`, `Distancias` con sellos, `elegirPrimerPaso`. `dijkstraSubgrafoConocido` y `dijkstraDesde` pasan a ser envoltorios del núcleo y luego se eliminan. |
| `model/RutasCazador.py` (nuevo) | Keilor | Caché, cota e invalidación fina (D5). |
| `model/Cazador.py` | Keilor (avisando a Justin) | `elegirPasoCazador` usa `elegirPrimerPaso`; las reglas de atacar y esperar (001) no cambian. |
| `model/Juego.py` | Justin, coordinado | Reemplazar `_rutasCazadorValidas` y `_distanciasCazador` por `RutasCazador`; llamar a `puertaCambio` en `_aplicarAbrir` y `_manejarCierrePuerta`; `invalidar()` en `_retroceder` y `restaurarEstado`. |
| `model/Entidades.py` | Justin | `Puerta.salaA`, `salaB`, `costo`; `Sala.indice`. |
| `bench/BenchCazador.py` | Keilor | Reescritura completa (ver «Mediciones planificadas»). |
| `tests/test_rutas_invalidacion.py` (nuevo) | Keilor | Escenarios de US-1 a US-3 y prueba oráculo. |
| `controller/ControladorJuego.py` | Jurnier | Sin cambios de este plan: «ir a» mantiene la firma de `elegirPasoViajeAutomatico`. |

---

## Complejidad esperada

| Operación | Antes | Después |
|---|---|---|
| Búsqueda del cazador | O((V + E) log E) sobre **toda** la cripta, con consultas hash y `buscar` por id | O((Vr + Er) log Er), con **Vr** = salas dentro de la cota; acceso O(1) al arreglo |
| Decisión de un cazador con caché válida | O(salidas) + consultas hash | O(salidas) ≤ O(4) |
| Cierre o apertura de puerta | invalida todo | O(1) para decidir si invalida |
| Cálculos por ciclo con N cazadores y mapa estable | 1 (bandera) | 1 o 0 (con caché válida) |
| Memoria | Tabla de V entradas por búsqueda | 2 listas de V, creadas una vez |

---

## Mediciones planificadas (`--bench`, `bench/BenchCazador.py`)

Todas con criptas sintéticas deterministas por semilla. Se guardan los números **antes** (código actual) y **después** para DECISIONES.

1. **Uno frente a muchos / compartido frente a individual** (PR-012): 1, 10, 30 y 60 cazadores; el individual (D2, alternativa) se verifica **antes** de medir: misma decisión que el compartido para cada cazador (PR-013).
2. **Rango pequeño frente a grande** (PR-010): rangos 150 y 2000 en criptas de 100, 1000 y 5000 salas; se reportan el tiempo y `salasExaminadas`.
3. **Invalidación** (PR-012): escenario A, puertas estables; B, una puerta al azar cambia en cada ciclo; C, cambia una puerta que está en caminos mínimos. Se comparan recalcular siempre, bandera gruesa e invalidación fina; se reportan ms por ciclo y la cantidad de recálculos.
4. **Ciclo de eventos** (PR-009): modelo real con 30 y 60 cazadores activados en el bench; se reportan la mediana, el p95 y el peor caso, y el número de decisiones de cazador por ciclo. Si son 0, la medición falla (PR-013).
5. **Tabla frente a arreglo con sellos** (D3): el mismo escenario 2 con ambas estructuras.

---

## Pruebas planificadas

- Un caso por escenario de US-1, US-2 y US-3, citando sus FR y PR.
- **Prueba oráculo** (US-1, escenario 12): cientos de turnos con semilla, abriendo y cerrando puertas al azar; en cada decisión, «con caché» = «desde cero sin cota».
- **Simetría** (supuesto de la spec): en las criptas de demostración, toda salida tiene su inversa con la misma puerta y el mismo costo.
- Las pruebas existentes de `test_terreno_cazador.py` y `test_niebla_viaje.py` deben seguir pasando sin cambios.

---

## Riesgos

- **`Juego.py` y `Entidades.py` son de Justin.** Esos cambios se integran con un PR revisado por él y van primero, antes de conectar `RutasCazador`.
- **Pergamino.** El diario revierte las puertas sin avisar al componente de rutas; por eso `_retroceder` invalida todo (decisión conservadora y correcta).
- **«ir a» y N-02.** Si Jurnier cambia la memoria de puertas a tres estados, solo cambia su `puedeUsar`; el núcleo no se toca.
