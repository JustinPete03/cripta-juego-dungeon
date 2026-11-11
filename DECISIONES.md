# Documento de Decisiones de Diseño

**Proyecto CRIPTA — Estructuras de Datos II · II Ciclo 2026**  
*Desarrollo dirigido por especificaciones (SDD) y diseño formal de estructuras de datos.*

---

# PRIMERA PARTE — DECISIONES DE DISEÑO BASE

---

## 2.10 Efectos Temporales

### 1. Problema
Los efectos temporales (veneno cada 80 unidades durante 400, regeneración cada 200, antorcha con apagado diferido y cambio de velocidad con reajuste de la próxima acción según §2.3) son eventos discretos programados en la agenda. El sistema debe poder cancelar un efecto antes de que se dispare (por ejemplo, al beber un antídoto o por muerte súbita del actor) y reprogramar una acción ya agendada cuando cambia la velocidad, **sin recorrer todos los eventos pendientes** (§4.1). Además, todo cambio debe ser estrictamente invertible mediante el pergamino de retroceso.

### 2. Alternativas consideradas
* **(A) Referencia directa al nodo del evento (Elegida)**: Cada efecto activo almacena una referencia directa a su evento en la agenda y a un flag de vigencia. La cancelación es $O(1)$ al marcar el flag en la tupla sin alterar el montículo de eventos.
* **(B) Búsqueda exhaustiva lineal en la agenda al cancelar**: Recorrer la agenda de eventos buscando el propietario. Se descartó formalmente porque su costo es $\Theta(N)$ respecto a la cantidad de eventos pendientes, degradando el bucle a medida que la cripta se puebla de enemigos.
* **(C) Validación pasiva en tiempo de disparo**: Dejar los eventos sin cancelar en la agenda y validar al ser extraídos si el efecto sigue vivo. Se descartó porque acumula eventos huérfanos que saturan la memoria y complica la reversibilidad atómica del diario de retroceso.

### 3. Decisión
Se implementó `efectosJuego` como controlador unificado de efectos activos. Cada `efectoActivo` (veneno, regeneración, antorcha, velocidad) guarda su próximo evento y estado booleano. La mutación pasa exclusivamente por métodos del `Modelo` (`asignar`, `agregarA`, `quitarDe`), que registran su operación inversa en el `Diario`. Cuando se altera la velocidad, `cambiarVelocidad` calcula el nuevo tiempo residual proporcional mediante la fórmula de P1 §2.3:
$$\text{tiempo\_restante}' = \max\left(1, \frac{\text{tiempo\_restante} \cdot \text{vel\_antigua}}{\text{vel\_nueva}}\right)$$
y reprograma el evento en la agenda asignándole un nuevo número de secuencia determinista.

### 4. Análisis de Complejidad
* **Cancelación de efecto**: $O(1)$ tiempo, $O(1)$ espacio auxiliar. Solo marca `evento.cancelado = True`. El montículo binario lo descarta perezosamente al emerger en la raíz ($O(\log N)$ amortizado al extraer).
* **Disparo de pulso**: $O(\log N)$ para encolar el siguiente pulso en la agenda.
* **Reprogramación por velocidad**: $O(1)$ para invalidar el anterior y $O(\log N)$ para insertar el reprogramado.

### 5. Evidencia Empírica (`bench/benchEfectos.py`)
Medición de cancelación directa frente a búsqueda lineal en agenda:

| Eventos pendientes | Cancelar directo | Buscando en agenda | Ratio de ventaja |
|:---:|:---:|:---:|:---:|
| 100 | 0.78 µs | 3.43 µs | **4.4x** |
| 1 000 | 0.79 µs | 22.46 µs | **28.4x** |
| 10 000 | 1.60 µs | 310.08 µs | **193.8x** |

La cancelación directa se mantiene acotada entre 0.75 y 1.60 µs ($O(1)$), mientras que la búsqueda lineal escala asintóticamente hasta consumir 0.31 ms por cancelación con 10 000 eventos.

### 6. Límites Conocidos
La cancelación perezosa retiene temporalmente memoria en el montículo hasta que los eventos cancelados son alcanzados por el puntero del reloj virtual. Si se acumulan millones de eventos cancelados en el futuro lejano sin dispararse, la memoria del montículo no se libera inmediatamente.

---

## 2.12 Tabla de Puntajes Local y Criterios de Desempate

### 1. Problema
Almacenar y mantener ordenado el historial de partidas terminadas (victorias y derrotas) bajo criterios jerárquicos estrictos, sin utilizar `list.sort()` ni `sorted()`, los cuales están prohibidos por §4.9.

### 2. Alternativas consideradas
* **(A) Quicksort in situ**: Descartado por no garantizar estabilidad por defecto ante registros con métricas idénticas y por su peor caso degenerativo $O(N^2)$ ante entradas preordenadas.
* **(B) Bubble Sort**: Descartado por ineficiencia cuadrática sistemática constante.
* **(C) Inserción directa multicriterio estable (Elegida)**: La tabla histórica se actualiza añadiendo partidas de una en una al finalizar cada juego. Inserción opera en $O(N)$ sobre secuencias casi ordenadas.

### 3. Decisión
Se implementó `GestorTablaPuntajes` con ordenamiento por inserción estable multicriterio:
1. **Criterio 1 (Mayor mérito)**: Cantidad de enemigos derrotados (orden descendente).
2. **Criterio 2 (Desempate 1)**: Menor tiempo virtual final del reloj (orden ascendente).
3. **Criterio 3 (Desempate 2)**: Menor cantidad de acciones realizadas por el jugador (orden ascendente).

### 4. Análisis de Complejidad
* **Inserción de partida individual**: $\Theta(N)$ comparaciones y desplazamientos in situ en el peor caso; $\Theta(1)$ si se añade con menor puntaje al final.
* **Memoria auxiliar**: $O(1)$ espacio adicional (in situ sobre la lista interna).

---

## 4.2 Precarga Anticipada de Contenido

### 1. Problema
Cada petición HTTP incurre en una latencia de red de ~400 ms y la cripta impone un límite estricto `presupuesto_solicitudes` (§5.1). Cruzar una salida requiere tener el contenido de la sala destino en memoria antes de confirmar la acción, sin alterar ni pausar el reloj virtual del juego.

### 2. Alternativas consideradas
* **(A) Descarga reactiva individual (On-Demand)**: Solicitar cada sala al instante de cruzar la puerta. Descartada porque incurre en latencia perceptible en cada movimiento y agota el presupuesto en las primeras 10 a 20 salas.
* **(B) Descarga exhaustiva inicial completa**: Descargar todo el contenido de la cripta al inicio. Descartada porque viola el presupuesto en criptas grandes y desperdicia solicitudes en salas remotas que nunca se visitan.
* **(C) Precarga por lotes de vecindad BFS (Elegida)**: Al entrar a una sala, se exploran las salas vecinas a distancia topológica 1 y 2 que aún no están en memoria, agrupándolas en lotes de hasta 10 identificadores ordenados.

### 3. Decisión
Se implementó `GestorRedPrecarga.precargarVecindad` mediante una cola FIFO sobre el esqueleto. Antes de emitir cualquier solicitud HTTP, el gestor valida con `_reservar(1)` que exista saldo suficiente en `presupuesto_solicitudes`. Si queda exactamente 1 solicitud en la recámara, la precarga se recorta cortésmente a solo la sala actual para preservar el presupuesto ante emergencias de catálogo.

### 4. Análisis de Complejidad
* **Selección de vecinas**: $O(V_{\text{local}} + E_{\text{local}})$ acotado a $k \le 10$ salas, es decir, $O(1)$ respecto al tamaño total de la cripta.
* **Solicitudes HTTP**: Acotadas a $\lceil N_{\text{visitadas}} / 10 \rceil$.

---

## 4.3 y 4.4 Caché de Fichas de Catálogo y Persistencia en Disco

### 1. Problema
Cada ficha de catálogo no disponible en RAM requiere una solicitud HTTP `/catalogo?ids=...`. La memoria RAM debe acotarse mediante un tope configurable (`--cache-size`, def. 25). Se debe seleccionar qué ficha desalojar garantizando que **jamás se expulse una ficha referenciada por un enemigo vivo, trampa o el inventario**, y preservando en disco las fichas desalojadas para que el juego pueda recuperarlas sin generar tráfico de red.

### 2. Alternativas consideradas
* **(A) FIFO simple**: Desaloja la ficha más antigua sin considerar frecuencia ni protección activa. Descartada porque expulsaría enemigos presentes en la sala actual.
* **(B) LRU con lista doble y contador de referencias activas (Elegida)**: Asocia a cada entrada un contador `referencias_activas` y marca de acceso temporal. Si la memoria se llena, se expulsa la menos recientemente usada con `referencias_activas == 0`. Al salir de RAM, la ficha se persiste en `.cache_cripta/cat_<version>/<id>.json`.
* **(C) Descarte puro sin persistencia en disco**: Descartada porque cada re-visita a un enemigo ya visto requeriría nuevas solicitudes HTTP, agotando el presupuesto.

### 3. Decisión
Se implementó `CacheCatalogo` combinando tabla hash con encadenamiento propio (algoritmo djb2 y factor de carga 0.75) y política LRU. El almacenamiento persistente `AlmacenFichasDisco` serializa fichas en formato JSON individual validado por versión de catálogo.

### 4. Análisis de Complejidad
* **Búsqueda en RAM**: $O(1)$ tiempo promedio ($\alpha \le 0.75$).
* **Desalojo LRU**: $O(N)$ en el peor caso para ubicar la candidata con cero referencias entre las $N \le \text{cache\_size}$ entradas.
* **Recuperación desde disco**: $O(1)$ lectura de sistema de archivos sin consumir presupuesto HTTP.

### 5. Evidencia Empírica (`bench/Cache.py`)
Medición con patrón de acceso sesgado (Zipfiano, 1 000 peticiones):

| Capacidad RAM | Tasa Aciertos LRU | Tasa Aciertos FIFO | Solicitudes sin Disco | Solicitudes con Disco | Ahorro de Red |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 5 | 25.6 % | 25.2 % | 744 | 59 | **92.1 %** |
| 10 | 49.3 % | 45.8 % | 507 | 59 | **88.4 %** |
| **25 (Def.)** | **82.5 %** | **74.2 %** | **175** | **59** | **66.3 %** |
| 50 | 91.7 % | 90.6 % | 83 | 59 | **28.9 %** |

**Conclusión empírica**: Con persistencia en disco, toda ficha única se descarga a lo sumo **una sola vez** de la red (59 llamadas constantes), amortizando el costo de red a cero para fichas ya descubiertas.

---

## 4.5 Inventario del Jugador

### 1. Problema
El jugador debe poder examinar su inventario bidireccionalmente (`sig`, `ant`) desde un cursor activo, soltar el objeto observado en $O(1)$, equipar armas y armaduras desplazándolas al frente del orden real en $O(1)$, y generar vistas ordenadas por peso, valor o nombre sin alterar la secuencia física interna.

### 2. Alternativas consideradas
* **(A) Arreglo contiguo (`list`)**: Descartado porque equipar o soltar desde posiciones intermedias requiere desplazar $O(N)$ elementos contiguos en memoria, violando el requisito de costo constante independiente de la posición.
* **(B) Lista simplemente enlazada**: Descartado porque recorrer hacia atrás (`ant`) requiere $O(N)$ o una pila auxiliar.
* **(C) Lista doblemente enlazada con cursor y punteros cabeza/cola (Elegida)**: Cada nodo almacena `objeto`, `ant`, `sig` y flag `enlazado`.

### 3. Decisión
Se implementó `Inventario` sobre una lista doblemente enlazada propia. El equipamiento mantiene referencias directas `self.arma` y `self.armadura`. Las vistas ordenadas generan una copia superficial de referencias y delegan su ordenamiento en el selector adaptativo (§4.9).

### 4. Análisis de Complejidad
* **Avanzar / Retroceder cursor**: $O(1)$ tiempo, $O(1)$ espacio.
* **Equipar / Soltar objeto actual**: $O(1)$ tiempo estricto mediante desenlace y reenlace de punteros adyacentes.
* **Vistas ordenadas**: $O(N \log N)$ mediante Merge Sort o $O(N)$ mediante Inserción si ya está casi ordenado.

### 5. Evidencia Empírica (`bench_retroceso`)
Microsegundos por operación al equipar o soltar en función del tamaño $N$:

| Tamaño $N$ | Lista Enlazada (Equipar) | Arreglo Contiguo (Equipar) | Lista Enlazada (Soltar) | Arreglo Contiguo (Soltar) |
|:---:|:---:|:---:|:---:|:---:|
| 10 | 0.38 µs | 0.20 µs | 0.38 µs | 0.18 µs |
| 100 | 0.38 µs | 0.29 µs | 0.47 µs | 0.19 µs |
| 1 000 | 0.39 µs | 0.53 µs | 0.41 µs | 0.24 µs |
| 10 000 | **0.41 µs** | 3.50 µs | **0.40 µs** | 0.70 µs |

La lista doblemente enlazada mantiene un costo plano de ~0.4 µs ($O(1)$), independizándose del tamaño de la colección.

---

## 4.6 Pergaminos de Retroceso e Historial Reversible

### 1. Problema
El jugador puede usar hasta 5 pergaminos de retroceso consecutivos para revertir acciones previas. Debe restaurar íntegramente: reloj virtual, vida de actores, posiciones, inventario, estado de puertas, activación de trampas y estado determinista del generador pseudoaleatorio `random.Random`, **sin hacer copias completas del estado en cada acción**.

### 2. Alternativas consideradas
* **(A) Clonación profunda de estado (Deep Copy)**: Clonar el modelo antes de cada turno. Descartado porque satura la memoria ($O(N \cdot S)$) y dispara excepciones de recursión (`RecursionError`) en criptas grandes.
* **(B) Diario de deltas reversibles con pila de clausuras inversas (Elegida)**: Cada mutación atómica del modelo (`asignar`, `agregarA`, `quitarDe`) apila en el `Diario` una función de restitución que revierte exactamente la mutación.

### 3. Decisión
El `Diario` mantiene un buffer circular de 5 intervalos. Cada intervalo almacena la secuencia de funciones inversas generadas durante el turno del jugador y las subsiguientes respuestas de los enemigos. Retroceder desapila y ejecuta las clausuras en orden cronológico inverso ($LIFO$).

### 4. Análisis de Complejidad
* **Registrar cambio**: $O(1)$ amortizado al apilar clausura en lista.
* **Cerrar intervalo**: $O(1)$ sobre el buffer circular de 5 entradas.
* **Retroceder turno**: $O(K)$, donde $K$ es el número de microcambios ocurridos en el intervalo.

### 5. Evidencia Empírica (`bench_retroceso`)
Comparación entre Diario Reversible vs Copia Completa de Estado:

| Escenario | Salas | Enemigos Activos | Tiempo Diario (µs) | Tiempo Copia (µs) | Memoria Diario | Memoria Copias |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Pocos activos | 20 | 2 | 27 µs | 1 227 µs | 150 KB | 324 KB |
| Pocos activos | 100 | 18 | 133 µs | 7 001 µs | 296 KB | 1 694 KB |
| Pocos activos | 300 | 58 | 460 µs | 27 217 µs | 703 KB | 4 860 KB |
| Estrés máximo | 300 | 598 | **7 881 µs** | 36 960 µs | **6 103 KB** | 5 890 KB |

El diario reversible resulta entre **3 y 59 veces más rápido** que la copia profunda, permitiendo retrocesos instantáneos sin pausas en el ciclo de juego.

---

## 4.9 Ordenamientos

### 1. Problema
El sistema requiere ordenar colecciones heterogéneas: inventario por peso/valor/nombre, lotes de identificadores de catálogo para determinismo en el replay, y tabla de puntajes locales. Se prohibió expresamente el uso de `sort()` y `sorted()`.

### 2. Alternativas consideradas
* **(A) Insertion Sort**: Excelente para arreglos pequeños ($N \le 32$) o preordenados ($O(N)$), pero cuadrático en el peor caso ($O(N^2)$).
* **(B) Merge Sort**: Óptimo y garantizado $O(N \log N)$ en todos los casos, pero requiere memoria auxiliar $O(N)$ y sobrecosto de recursión en arreglos diminutos.
* **(C) Selector Adaptativo Híbrido (Elegido)**: Inspecciona la longitud $N$ y mide el número de inversiones (pares desordenados). Elige Inserción si $N \le 32$ (o $N \le 8$ con comparaciones costosas) o si las inversiones son $\le 5\%$; en caso contrario delega en Merge Sort.

### 3. Evidencia Empírica (`bench/Ordenamientos.py`)
Mediana en ms con entradas aleatorias:

| Tamaño $N$ | Inserción (ms) | Mezcla (ms) | Selección (ms) | Algoritmo Ganador |
|:---:|:---:|:---:|:---:|:---:|
| 8 | **0.005 ms** | 0.012 ms | 0.009 ms | **Inserción** |
| 16 | **0.014 ms** | 0.022 ms | 0.027 ms | **Inserción** |
| 32 | **0.046 ms** | 0.047 ms | 0.090 ms | **Empate / Punto de Cruce** |
| 64 | 0.166 ms | **0.108 ms** | 0.294 ms | **Mezcla** |
| 128 | 0.609 ms | **0.253 ms** | 1.009 ms | **Mezcla** |

El punto de cruce empírico exacto se ubica en $N = 32$, justificando matemáticamente la regla de decisión del selector.

---

## 4.10 Guardado Binario de la Partida

### 1. Problema
Persistir la partida en un archivo binario de bajo nivel con formato propio. Al restaurar una sala específica, debe recuperarse **sin leer el archivo completo** mediante acceso aleatorio con `seek()`.

### 2. Alternativas consideradas
* **(A) Serialización JSON completa**: Descartada porque para leer una sola sala requiere parsear el documento íntegro, tardando hasta 14.7 ms en criptas de 20 000 salas.
* **(B) Formato binario con bloques de sala e índice al final (Elegida)**: Encabezado fijo (`MAGIC`, versión, cantidad, offset índice). Cada sala se empaqueta con `struct` y al final del archivo reside una tabla de entradas de tamaño fijo `(idSala, offset, longitud)`.

### 3. Evidencia Empírica (`bench/benchGuardado.py`)
Tiempo de carga de una sola sala:

| Total Salas en Archivo | Formato Binario Propio | JSON Completo | Factor de Aceleración |
|:---:|:---:|:---:|:---:|
| 20 | 82.1 µs | 105.4 µs | 1.3x |
| 200 | 96.0 µs | 157.4 µs | 1.6x |
| 2 000 | 87.3 µs | 1 011.9 µs | **11.6x** |
| 20 000 | **137.3 µs** | 14 720.1 µs | **107.2x más rápido** |

La búsqueda binaria directa sobre el índice en disco mantiene la recuperación de cualquier sala en $O(\log N)$ lecturas microscópicas (~100 µs), cumpliendo estrictamente con la especificación.

---

# SEGUNDA PARTE — DECISIONES DE DISEÑO AVANZADAS

---

## 5.1 La Ruta más Barata del Cazador

* **Especificación**: `specs/001-terreno-y-cazador/spec.md`
* **Plan**: `specs/001-terreno-y-cazador/plan.md`

### 1. Problema
El enemigo cazador debe perseguir al jugador utilizando la ruta de costo mínimo basada en salidas con pesos variables ($\ge 1$, por defecto 100), sin abrir puertas cerradas y respetando su rango de persecución. En una partida pueden coexistir decenas de cazadores simultáneamente persiguiendo al mismo objetivo. Contar salas (BFS simple) no encuentra la ruta más barata porque las salidas tienen costos no uniformes. El desempate exige que, entre vecinas con igual costo total óptimo $d$, se escoja la vecina de menor ID.

### 2. Alternativas consideradas
* **(A) Dijkstra individual por cazador**: Cada cazador ejecuta un Dijkstra desde su posición hacia el jugador. Con $N$ cazadores activos el costo escala como $O(N \cdot (V + E) \log V)$, ejecutando decenas de búsquedas redundantes en cada turno.
* **(B) Dijkstra compartido inverso desde la sala del jugador (Elegida)**: Se ejecuta una única búsqueda de caminos mínimos desde la sala actual del jugador hacia todo el grafo de salidas abiertas. Todos los cazadores activos leen sus distancias en $O(1)$ sobre la `Tabla` propia resultante.

### 3. Decisión
Se implementó un algoritmo de Dijkstra propio con un montículo binario de mínimos propio (`MinHeapDijkstra` en `model/Dijkstra.py`) y almacenamiento de distancias en `Tabla` propia (`model/Tabla.py`), cumpliendo con la prohibición estricta de `heapq`, `dict` y `set`. La búsqueda se ejecuta desde la sala del jugador; cada cazador consulta $d = \text{distancias.obtener}(u.\text{id})$. Si $d > \text{rango}$ o no hay ruta, espera (costo 100). Si $d \le \text{rango}$, examina sus salidas abiertas y selecciona la vecina con menor ID que satisfaga:
$$\text{costo}(u, v) + \text{dist}(v, \text{jugador}) = d$$
garantizando el desempate determinista exigido por §3.2.

### 4. Análisis de Complejidad
* **Tiempo**: Un único Dijkstra por ciclo de eventos: $O((V + E) \log V)$, donde $V$ es el número de salas y $E \le 4V$ las salidas. La consulta y decisión de cada cazador toma $O(\text{salidas}) \le O(4) = O(1)$.
* **Espacio**: $O(V)$ para el montículo y la tabla hash de distancias.

### 5. Evidencia Empírica (`bench/BenchCazador.py`)
Medición sobre cripta de 100 salas con múltiples cazadores:

| Cantidad de Cazadores | Cálculo Compartido (ms) | Cálculo Individual (ms) | Factor de Ganancia |
|:---:|:---:|:---:|:---:|
| 1 cazador | 0.37 ms | 0.17 ms | 0.5x |
| 10 cazadores | 0.36 ms | 1.59 ms | **4.4x más rápido** |
| 30 cazadores | 0.38 ms | 4.93 ms | **13.0x más rápido** |
| 60 cazadores | 0.40 ms | 9.05 ms | **22.8x más rápido** |

---

## 5.2 Invalidación Inteligente de Rutas

* **Especificación**: `specs/001-terreno-y-cazador/spec.md`
* **Plan**: `specs/001-terreno-y-cazador/plan.md`

### 1. Problema
Entre los turnos de los cazadores ocurren eventos: el jugador se mueve, las puertas se abren o se cierran automáticamente, otros actores cambian de sala o mueren. La decisión del cazador debe ser estrictamente idéntica a la que produciría un cálculo desde cero (§3.2). Recalcular Dijkstra en cada turno de cada enemigo desperdicia CPU si el entorno no ha cambiado.

### 2. Alternativas consideradas
* **(A) Recálculo continuo ciego**: Se ejecuta Dijkstra en cada turno de cazador. Garantiza corrección pero consume hasta 0.36 ms por cazador por turno.
* **(B) Invalidación perezosa por eventos topológicos (Elegida)**: Se mantiene una bandera `_rutasCazadorValidas` y la tabla de distancias en caché. La bandera se invalida únicamente cuando ocurre un evento que altera la topología o el destino:
  1. Movimiento del jugador (`_aplicarMover`).
  2. Apertura de puerta (`_aplicarAbrir`).
  3. Cierre automático de puerta (`_manejarCierrePuerta`).
  4. Retroceso temporal con pergamino (`_retroceder`).
  Eventos ajenos (daño, ataques, movimiento de otros enemigos, cambios de velocidad) NO invalidan la topología del grafo ni las distancias hacia el jugador.

### 3. Evidencia Empírica (`bench/BenchCazador.py`)
* **Con recálculo continuo**: 0.365 ms por turno.
* **Con reutilización inteligente**: 0.026 ms por turno.
* **Ahorro de trabajo**: **13.9x menos tiempo de CPU**.
* **Presupuesto de procesamiento (§6.1)**: Mediana de 0.02 ms por ciclo de eventos (< límite de 20 ms).

---

## 5.3 El Mapa Conocido y Viaje Automático («ir a»)

* **Especificación**: `specs/002-niebla-y-viaje/spec.md`
* **Plan**: `specs/002-niebla-y-viaje/plan.md`

### 1. Problema
El jugador experimenta niebla de guerra: no conoce el mapa completo, solo las salas *Exploradas* y *Avistadas*. Debe mantener memoria independiente del estado de las puertas observadas, actualizarse cuando se entra a las salas contiguas, e interactuar con el efecto de la antorcha (que revela salas vecinas sin despertar entidades). Todo el conocimiento del jugador forma parte del estado del juego y debe poder revertirse con pergaminos de retroceso de manera económica, sin hacer copias completas del mapa. Además, el comando «ir a» debe calcular la ruta óptima paso a paso exclusivamente sobre el subgrafo conocido y salidas recordadas abiertas, con desempate determinista por menor ID de vecina.

### 2. Decisión
Se implementó `MapaConocido` sobre `Tabla` propia con dispersión djb2.
* La consulta de si una sala está explorada toma $O(1)$.
* La consulta de si está avistada revisa únicamente los vecinos inmediatos de la sala (máximo 4), tomando $O(4) = O(1)$.
* La exploración de una nueva sala registra su inversa en el `Diario` en $O(1)$, haciendo que revertir con un pergamino sea una simple llamada a `quitar` en la tabla hash.

### 3. Evidencia Empírica (`bench/BenchNiebla.py`)
* **Consultas al mapa conocido**:
  * Estado de sala (`explorada`/`avistada`/`desconocida`): **1.04 µs** por operación.
  * Memoria de puertas: **0.50 µs** por operación.
* **Costo de exploración vs. Tamaño del mapa conocido**:
  * Con 10 salas previas: explorar 5 nuevas toma **0.011 ms**.
  * Con 50 salas previas: explorar 5 nuevas toma **0.013 ms**.
  * Con 300 salas previas: explorar 5 nuevas toma **0.012 ms**.
  * El costo es estrictamente plano ($O(1)$) e independiente del tamaño del mapa conocido.
* **Cálculo de un paso de «ir a»**: **1.39 ms** sobre 200 salas (límite exigido: < 5 ms).

---

## 5.4 Verificación de Resolubilidad y Detección de Ciclos

* **Especificación**: `specs/003-resolubilidad/spec.md`
* **Plan**: `specs/003-resolubilidad/plan.md`

### 1. Problema
Antes de iniciar una partida o al invocar `--verificar <cripta>`, determinar si la cripta puede completarse exitosamente (§3.5). Si es resoluble, retornar una secuencia determinista de obtención de llaves; si no lo es, detallar la frontera bloqueada y reportar los ciclos de dependencias circulares (e.g. $[K \to K]$ o $[K_1 \to K_2 \to K_1]$), ejecutándose en menos de 200 ms.

### 2. Alternativas consideradas
* **(A) BFS repetido por cada llave encontrada (Ingenuo)**: Cada llave nueva reinicia la exploración desde la sala inicial. Complejidad $O(K \cdot (V + E))$, ineficiente en cadenas largas de llaves.
* **(B) Recorrido incremental con cola de eventos y puertas en espera (Elegida)**: Se realiza una única búsqueda en anchura incremental con costo $O(V + E + K)$. Si se halla una puerta cerrada cuya llave no se posee, la arista se registra en una lista de espera indexada en `Tabla` propia (`puertasEsperandoLlave`). Al recoger la llave, sus puertas en espera se "despiertan" y se encolan inmediatamente, sin reiniciar las salas ya visitadas.

### 3. Evidencia Empírica (`bench/BenchResolubilidad.py`)
Medición con cadenas de llaves encadenadas:

| Cantidad de Llaves $K$ | Recorrido Incremental (ms) | Recorrido Ingenuo (ms) | Factor de Ganancia |
|:---:|:---:|:---:|:---:|
| 10 llaves | 0.093 ms | 0.023 ms | — |
| 50 llaves | 0.642 ms | 0.475 ms | — |
| 100 llaves | **1.350 ms** | 1.884 ms | **1.4x más rápido** |

* **Presupuesto de procesamiento (§6.1, PR-005 < 200 ms)**: Verificación sobre cripta de 200 salas y 31 llaves: **1.19 ms** (un margen de seguridad de más de 160x).

---

## 5.5 Puntos de Control y Línea de Tiempo Reversible

* **Especificación**: `specs/004-linea-de-tiempo/spec.md`
* **Plan**: `specs/004-linea-de-tiempo/plan.md`

### 1. Problema
Permitir consultar el estado en cualquier instante $t$ (`historia <t>`) o acción previa $\#k$ (`historia #k`) y la reproducción hasta un instante $t$ (`--replay ... --hasta <t>`), sin alterar el estado en curso, sin consumir tiempo virtual y sin escribir en `partida.log`. No se permite guardar más de una copia completa cada $K$ acciones (configurable con `--checkpoint-cada K`, justificado con mediciones). Fuera de los checkpoints, solo se almacenan las acciones livianas. Al retroceder con un pergamino, la línea debe recortarse en $O(1)$.

### 2. Alternativas consideradas
* **(A) Inversión hacia atrás de cambios**: Almacenar clausuras inversas de toda la partida. Descartada por consumo gigantesco de memoria y porque el generador `random.Random` (Mersenne Twister) no posee inversión analítica simple.
* **(B) Copia completa en cada acción ($K = 1$)**: Descartada por violar la restricción de memoria de §5.5.
* **(C) Reconstrucción hacia adelante desde punto de control (Forward Re-simulation, Elegida)**: Se guarda un snapshot completo generado por `model.estado.capturar()` cada $K$ acciones. Para cualquier consulta, se ubica el punto de control anterior más cercano, se restaura un modelo réplica y se re-simulan a lo sumo $K - 1$ acciones hasta el instante pedido.

### 3. Evidencia Empírica y Justificación de $K = 20$ (`bench/BenchLineaTiempo.py`)
Medición sobre partida de 1 000 acciones variando $K$:

| Configuración | Puntos de Control | Memoria Retenida | Mediana de Consulta | Peor Caso |
|---|:---:|:---:|:---:|:---:|
| $K = 5$ | 201 | 5 220 KB | 2.29 ms | 3.75 ms |
| **$K = 20$ (Por Defecto)** | **51** | **1 337 KB** | **4.63 ms** | **6.67 ms** |
| $K = 50$ | 21 | 560 KB | 8.14 ms | 13.93 ms |
| Sin checkpoints ($K = \infty$) | 1 | 38 KB | 52.73 ms | 76.76 ms |

**Justificación técnica de $K = 20$**:
Con $K = 20$, el consumo de memoria se reduce en un **74 %** respecto a $K = 5$ (1.3 MB vs 5.2 MB), manteniendo tiempos de consulta excelentes (< 5 ms). A diferencia de $K = \infty$ que supera los 50 ms en consultas tardías, $K = 20$ garantiza cumplir con holgura el límite PR-007 (< 50 ms) incluso en partidas de 5 000 acciones (mediana: **3.57 ms**).

---

## 5.6 Revisión de Decisiones de la Primera Parte

* **Agenda de eventos**: Sigue siendo óptima. Con decenas de cazadores activos reprogramando eventos de movimiento con costos variables, el ciclo de eventos mantuvo una mediana de 0.02 ms (< 20 ms). El heap binario propio con desempate por tupla nativa maneja sin degradación miles de eventos. Se mantuvo la decisión sin cambios.
* **Historial de retroceso**: El buffer circular de 5 intervalos y el `Diario` reversible continúan operando en menos de 0.1 µs por intervalo. La adición de la línea de tiempo demostró que el diario de 5 intervalos no debía ampliarse para toda la historia (lo cual consumiría megabytes de memoria innecesaria), ratificando la separación entre el retroceso local (5 intervalos) y la línea de tiempo global con checkpoints cada $K$. Se mantuvo la decisión sin cambios.
* **Inventario**: La lista doblemente enlazada mantiene equipar y soltar en $O(1)$ (< 0.3 µs) independientemente del tamaño del inventario.
* **Formato de Guardado**: Evolucionó formalmente de `VERSION_FORMATO = 2` a `VERSION_FORMATO = 3` para incorporar la sección `"linea_tiempo"`, implementando la detección y rechazo explícito de partidas de la primera parte.

---

## 5.7 Auditoría Post-Evaluación y Mejoras de Arquitectura (Rúbrica)

Para atender directamente las observaciones de la rúbrica del profesor ("Manejo de errores más robusto", "Logging más detallado", "Interfaz básica", "Suite de pruebas ampliada", "Optimizaciones pendientes"), se implementaron las siguientes mejoras técnicas:

### 5.7.1 Manejo Robusto de Errores y Telemetría en `ClienteHTTP`
1. **Jerarquía Tipada de Excepciones**:
   * `ErrorRedCripta(RuntimeError)` como raíz común.
   * `ErrorConexionServidor`: captura específica de `requests.exceptions.ConnectionError`.
   * `ErrorTiempoEspera`: captura de `requests.exceptions.Timeout` con tiempo exacto transcurrido.
   * `ErrorLimiteFrecuenciaExcedido`: lanzado tras agotar los 5 reintentos en HTTP 429.
   * `ErrorRespuestaInvalida`: lanzado cuando el status es 200 pero el cuerpo no es JSON decodificable.
   * `ErrorHttp`: almacena código HTTP exacto y detalle textual (404 no encontrado, 500 error de servidor).
2. **Telemetría y Logging Estructurado**:
   * Reemplazo de `print()` por el módulo estándar `logging` (`logger = logging.getLogger("Cripta.Red")`).
   * Registro con microsegundos de latencia (`time.perf_counter()`), tamaño en bytes de la respuesta, encabezados enviados y estado de reintentos.

### 5.7.2 Optimización Asintótica de Topología de Red en `GestorRedPrecarga`
* **Problema detectado**: `_obtenerSalasContiguas` realizaba una búsqueda secuencial $\Theta(V)$ sobre la lista plana `esqueletoSalas` en cada paso del BFS de vecindad. En criptas grandes con cientos de salas, esto inducía un costo cuadrático $O(V \cdot K)$.
* **Solución implementada**: Creación de `self._mapaContiguas = Tabla()` durante `inicializarCripta`. Indexa la adyacencia de salida de cada sala en tiempo $O(V)$ una sola vez sobre tabla hash propia con dispersión djb2.
* **Resultado**: `_obtenerSalasContiguas` pasa de $O(V)$ a **$O(1)$ tiempo constante**. La suite completa de pruebas redujo su tiempo de ejecución de 3.52 s a **2.03 s** (más de un 40 % de mejora global).

### 5.7.3 Ampliación Exhaustiva de Pruebas Automatizadas
Se incorporó el módulo `tests/test_pruebas_ampliadas_rubrica.py` con 13 pruebas unitarias e integradas adicionales, elevando la suite a **235 pruebas automatizadas al 100 % de éxito**:
* Pruebas de capacidad unitaria ($N=1$) en la caché LRU.
* Validación de saturación con todas las fichas en uso (inhibición de desalojo y sobretope controlado).
* Mocks de red para fallos de conexión, timeouts, JSON truncado y agotamiento de reintentos 429.
* Rechazo explícito de partidas guardadas con magic corrupto o versión incompatible (v2 de P1).
* Truncamiento atómico de la línea de tiempo tras la ejecución de un pergamino de retroceso.

### 5.7.4 Rediseño Visual y Jugabilidad en `VistaConsola`
* Representación visual en recuadros Unicode estructurados.
* Barra dinámica de vida para jugador y enemigos (`[██████░░░░] 60/100`).
* Desglose explícito de costos de salidas y estado de puertas (`[N] ➔ Sala 2 | Costo: 100 | 🔓 Abierta`).
* Distinción jerárquica destacada para cazadores (`🏹 [CAZADOR PREDADOR - Rango: 600]`).
* Barra de comandos rápidos integrada en pantalla para una experiencia de usuario fluida y ergonómica.
