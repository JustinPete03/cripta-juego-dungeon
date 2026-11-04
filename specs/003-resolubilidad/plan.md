# Plan de Implementación: Verificación de Resolubilidad

**Rama**: `003-resolubilidad` | **Fecha**: 2026-11-01 | **Spec**: [spec.md](spec.md)

---

## Resumen

Diseñar e implementar el algoritmo de verificación de resolubilidad de criptas antes de iniciar la partida, bajo los supuestos de §3.5. Emplea un recorrido incremental $O(V + E + K)$ sobre estructuras propias (`Tabla`), genera el orden determinista de obtención de llaves o el reporte de frontera bloqueada con detección de ciclos, y conecta las banderas CLI `--verificar` y `--forzar`.

---

## Verificación de la Constitución

1. **Estructuras propias**: PASA. El algoritmo opera sobre `Tabla` propia (`model/Tabla.py`) para registrar salas alcanzadas, llaves obtenidas, puertas en espera y ubicaciones. Prohibido `dict`, `set`, `heapq`, `networkx`.
2. **Determinismo**: PASA. Recorrido con desempate por orden canónico de direcciones (N, S, E, O) y menor ID de sala. Ciclos reportados en orden determinista.
3. **Separación MVC**: PASA. La lógica de verificación reside en `model/Resolubilidad.py` y no conoce vistas.
4. **Presupuesto de solicitudes**: PASA. La llamada a `GET /criptas/<id>/llaves` descuenta del presupuesto de red en modo online y se lee de disco en `--offline`.

---

## Algoritmo Incremental de Recorrido ($O(V + E + K)$ frente a alternativa ingenua)

### Justificación (§5.4):
La alternativa ingenua repite un recorrido completo (BFS/DFS) desde la sala inicial cada vez que se descubre una nueva llave. En una cripta con $K$ llaves encadenadas, el costo de la alternativa ingenua es $O(K \cdot (V + E))$.
Nuestro diseño **incremental** mantiene una lista de puertas dormidas indexadas por la llave que necesitan (`puertasBloqueadasPorLlave`: `Tabla(idLlave -> listaDePuertas)`).
* Cada sala se visita **a lo sumo una vez**.
* Cada salida se examina **a lo sumo dos veces** (al encontrarla y cuando se desbloquea su llave).
* Cuando una sala alcanzada contiene una llave, se despiertan inmediatamente las salidas que esperaban por ella y se encolan sus destinos.
* Costo total: $O(V + E + K)$, lineal con el tamaño del grafo y las llaves.

---

## Detección Determinista de Ciclos de Dependencia

Si la cripta no es resoluble:
1. Se recopilan las llaves inalcanzables y sus salas correspondientes.
2. Para cada llave inalcanzable $K_A$, se trazan las puertas bloqueadas que impiden llegar a su sala desde la región alcanzada. Si una puerta bloqueada requiere la llave $K_B$, existe una arista de dependencia $K_A \leftarrow K_B$ ($K_A$ necesita $K_B$ para ser obtenida).
3. Se detecta el ciclo determinista mediante búsqueda en profundidad (DFS) propia sobre el grafo de dependencias de llaves.
4. Si una llave requiere abrir una puerta que solo ella misma abre, se reporta el ciclo directo `[K -> K]`. Para cadenas indirectas, se reporta la secuencia cíclica `[K1 -> K2 -> ... -> K1]`.

---

## Cambios a la Arquitectura

| Módulo | Cambio |
|---|---|
| `adapters/clienteCripta.py` | Agregar método abstracto `obtenerLlaves(idCripta)` |
| `adapters/clienteHttp.py` | Implementar `GET /criptas/{id}/llaves` |
| `adapters/clienteOffline.py` | Implementar lectura de llaves desde disco / sintetización |
| `model/Resolubilidad.py` | Clase `ResultadoResolubilidad` y función `verificarResolubilidad(...)` |
| `main.py` | Banderas `--verificar <idCripta>` y `--forzar` |
| `bench/BenchResolubilidad.py` | Benchmark comparando recorrido incremental vs repetido por llave |

---

## Mediciones planificadas (`--bench`)

1. **Recorrido incremental frente a repetido por llave**: Criptas sintéticas encadenadas con 10, 30, 50 y 100 llaves en serie.
2. **Tiempo de verificación en cripta grande**: Medición para asegurar cumplimiento del límite de 200 ms (§6.1).
