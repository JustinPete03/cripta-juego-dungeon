# Plan de Implementación: Terreno y Cazador

**Rama**: `001-terreno-y-cazador` | **Fecha**: 2026-11-01 | **Spec**: [spec.md](spec.md)

---

## Resumen

Extender el modelo existente para que las salidas tengan costo variable y agregar el comportamiento `cazador`, un enemigo que calcula la ruta de costo mínimo hacia el jugador usando Dijkstra propio con montículo binario propio, limitado por rango.

---

## Verificación de la Constitución

1. **Estructuras propias**: PASA. Dijkstra se implementa con montículo binario propio (reutilizando el esquema de `Agenda.py`). Las distancias se almacenan en `Tabla` propia. Sin `heapq`, `dict`, `set`.
2. **Determinismo**: PASA. El desempate por menor id de sala garantiza resultado único.
3. **Separación MVC**: PASA. La búsqueda de ruta vive en `model/`. La vista solo muestra costos.
4. **Sin datos concretos**: PASA. El rango y costo se leen de las fichas/esqueleto.

---

## Cambios al modelo de datos

### `Salida` (model/Entidades.py)
- Nuevo campo: `costo` (int, default 100).

### `Enemigo` (model/Entidades.py)
- Nuevo campo: `rango` (int, default 0). Solo relevante cuando `comportamiento == "cazador"`.

---

## Estructura de la solución de rutas

### Algoritmo: Dijkstra con montículo binario propio

**Justificación**: Los costos no son uniformes, así que BFS no sirve. Dijkstra con montículo binario tiene complejidad O((V + E) log V) y se detiene tempranamente cuando la distancia extraída supera el rango del cazador.

**Alternativa rechazada**: BFS ponderado (descomponer aristas en unitarias): memoria y tiempo proporcionales a la suma de costos, no al número de salidas. Prohibitivo para costos altos (250+).

**Alternativa rechazada**: Bellman-Ford: O(V × E), innecesariamente lento para pesos positivos.

### Decisión: cálculo compartido vs. individual (§5.1)

Todos los cazadores persiguen al mismo jugador. En lugar de un Dijkstra por cazador, se ejecuta **un solo Dijkstra inverso desde la sala del jugador** que propaga distancias hacia todas las salas. Cada cazador consulta su distancia en O(1).

- **Cálculo compartido**: 1 Dijkstra por ciclo, O((V + E) log V). Cada cazador consulta O(1).
- **Cálculo individual**: N Dijkstras por ciclo, cada uno potencialmente O((V + E) log V).
- **Corte por rango individual**: El Dijkstra compartido se ejecuta completo una vez. Cazadores de rango pequeño descartan la ruta si `dist > rango`. El costo total es siempre 1 Dijkstra.

**Optimización de invalidación (§5.2)**: Se marca una bandera `_rutasInvalidas` cuando cambia el estado de una puerta o el jugador se mueve. El Dijkstra solo se recalcula si la bandera está activa al momento de decidir. Si ninguna puerta cambió y el jugador no se movió desde el último cálculo, se reutilizan las distancias anteriores.

### Módulos nuevos

| Módulo | Responsabilidad |
|---|---|
| `model/Dijkstra.py` | Montículo binario propio para Dijkstra + función `dijkstraInverso(salas, salaJugador)` que devuelve tabla de distancias y predecesores |
| `model/Cazador.py` | Función `elegirDestinoCazador(enemigo, distancias, salas)` que aplica las reglas de §3.2 |

### Montículo para Dijkstra (MinHeapDijkstra)

Montículo binario de pares `(distancia, salaId)` con operación `disminuirClave`. Se implementa con lista plana y mapa de posiciones (usando `Tabla` propia) para mantener O(log n) en la extracción y O(log n) en la disminución.

---

## Cambios a módulos existentes

| Módulo | Cambio |
|---|---|
| `model/Entidades.py` | Agregar `costo` a `Salida` y `rango` a `Enemigo` |
| `model/Juego.py` | `_construirSalas`: leer costo de salida. `_enemigoSeComporta`: agregar caso `"cazador"`. `_programarEnemigo` y `_moverEnemigo`: usar costo de salida en lugar de costo fijo |
| `model/Constantes.py` | (sin cambios sustanciales; `COSTO_ACCION_ENEMIGO` ya no se usa como costo de movimiento) |
| `view/Consola.py` | Mostrar costos de salidas y etiqueta "[cazador]" |
| `view/presentacion.py` | Incluir costos de salidas en la instantánea |

---

## Mediciones planificadas (`--bench`)

1. Dijkstra compartido vs. individual: 1 cazador, 10, 30 cazadores en cripta sintética.
2. Rango pequeño vs. rango grande: verificar que el corte por rango no afecta el cálculo compartido.
3. Invalidación: puertas estables (0 cambios) vs. inestables (cambio cada turno). Recálculo siempre vs. reutilización con bandera.
4. Ciclo de eventos con cazadores: mediana del ciclo con 30 cazadores activos < 20 ms.
