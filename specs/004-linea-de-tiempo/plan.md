# Plan de Implementación: Línea de Tiempo y Puntos de Control

**Feature**: `004-linea-de-tiempo`  
**Spec**: [spec.md](spec.md)  
**Constitución**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)

---

## 1. Arquitectura y Estructuras de Datos

### 1.1 Modelo de la Línea de Tiempo (`model/LineaTiempo.py`)
- **Clase `LineaTiempo`**:
  - `self.k`: Frecuencia de puntos de control (acciones del jugador entre puntos de control consecutivos, por defecto 20, acotado a $k \ge 1$ con `max(1, k)`).
  - `self._puntosControl`: Lista ordenada de instancias de la clase `PuntoControl`. Cada punto almacena:
    - `numAccion`: Índice de la acción del jugador ($0, K, 2K, \dots$).
    - `reloj`: Tiempo del reloj virtual al registrar el punto de control.
    - `snapshot`: Copia serializada completa generada por `modelo.capturarEstado()`. Incluye el estado del generador pseudoaleatorio propio (`random.Random.getstate()`), la agenda de eventos, mapa conocido, inventario, etc.
    - Implementación: Clase ligera con `__slots__ = ("numAccion", "reloj", "snapshot")` con acceso por atributos sin diccionarios internos en memoria.
  - `self._acciones`: Lista ordenada de instancias de la clase `RegistroAccion`. Cada registro almacena:
    - `numAccion`: Número de secuencia de la acción realizada por el jugador.
    - `accion`: Instancia de `Accion` (tipo y argumento).
    - `reloj`: Tiempo del reloj virtual en el momento de tomar la decisión.
    - Implementación: Clase ligera con `__slots__ = ("numAccion", "accion", "reloj")`.

- **Invariantes de los Puntos de Control (`self._puntosControl`)**:
  1. **Existencia del punto base**: Siempre existe el punto de control inicial con `numAccion = 0` y `reloj = relojInicial`, registrado de forma determinista en `iniciarPartida()`. La lista nunca está vacía.
  2. **Orden estrictamente creciente en acciones**: Para cualesquiera índices $i < j$, `_puntosControl[i].numAccion < _puntosControl[j].numAccion` ($0, K, 2K, \dots$).
  3. **Orden monótono no decreciente en reloj virtual**: Para cualesquiera índices $i < j$, `_puntosControl[i].reloj <= _puntosControl[j].reloj`.
  4. **Validez de la búsqueda binaria**: Debido a estos invariantes, las funciones de búsqueda binaria sobre `numAccion` y sobre `reloj` son formalmente correctas y deterministas en tiempo $O(\log(P))$, donde $P = |\text{\_puntosControl}| \le \lfloor N/K \rfloor + 1$.
  5. **Anexado eficiente en $O(1)$**: Se implementará que al registrar un nuevo punto de control, solo es necesario consultar o comparar con el último elemento de la lista `_puntosControl[-1]` (o reemplazarlo si coincide en `numAccion`), logrando una inserción $O(1)$ sin recorrer la lista.

- **Búsqueda de Puntos de Control**:
  - `buscarPuntoControlMasCercanoAccion(k)`: Búsqueda binaria propia sobre `_puntosControl` buscando el mayor punto con `numAccion <= k - 1`. Costo $O(\log(N / K))$.
  - `buscarPuntoControlMasCercanoTiempo(t)`: Búsqueda binaria propia sobre `_puntosControl` buscando el mayor punto con `reloj <= t`. Costo $O(\log(N / K))$.

### 1.2 Reconstrucción de Estados: Hacia Adelante 
- **Decisión de diseño**: Re-simulación hacia adelante desde el punto de control anterior más cercano.
  - Al consultar `historia <t>` o `historia #k`, se localiza el punto de control previo más cercano (a distancia máxima $K - 1$ acciones).
  - Se instancia una réplica mediante la función auxiliar `_crearModeloAuxiliar(proveedor, semilla, snapshot)`, que construye un modelo auxiliar completo invocando `_construirSalas(esqueleto)` e `iniciarPartida()`, y luego aplica `restaurarEstado(snapshot)`.
  - Se re-simulan las acciones del jugador intermedias hasta alcanzar la acción solicitada o el instante $t$ (procesando eventos de la agenda hasta $t$).
  - Como máximo se ejecutan $K - 1$ acciones intermedias, garantizando que ninguna consulta procese más de $K$ acciones.
  - El modelo vivo de la partida permanece estrictamente intacto.

- **Evaluación experimental y decisión con datos (Decisión L-03)**:
  - Hoy en día, la consulta construye un modelo auxiliar completo en cada invocación.
  - Se medirá el tiempo de respuesta con la **cripta más grande disponible** bajo una partida sintética de **5 000 acciones continuas** del jugador.
  - Con los datos empíricos de dicha medición se decidirá formalmente entre:
    1. **Reutilizar el esqueleto ya construido**: Compartir la topología inmutable de las salas de la cripta entre el modelo vivo y el modelo de consulta (shallow copy de salas y sólo clonar estado dinámico) para eliminar el costo de construcción de salas.
    2. **Reconstrucción hacia atrás con inversas**: Retroceder paso a paso mediante deltas inversos desde el estado actual o punto de control posterior.
  - **Aislamiento estricto de red y caché**: Las consultas históricas tienen terminantemente prohibido realizar solicitudes de red HTTP (`requests`) y tienen prohibido modificar o alterar el estado o tamaño de la caché del proveedor (`cache_estructuras` / `cache`).
  - **Verificación automatizada**: Se incluye una prueba automatizada específica en `tests/test_linea_tiempo.py` que comprueba que el contador de peticiones de red y el contenido de la caché de estructuras no sufren cambios tras ejecutar múltiples consultas históricas ($\Delta \text{red} = 0$, $\Delta \text{caché} = 0$).

### 1.3 Recorte ante Pergamino de Retroceso (Rollback)
- Al ejecutarse `_retroceder()`, se conoce la cantidad de acciones deshechas por el pergamino.
- `lineaTiempo.recortar(nuevoTotalAcciones)`:
  - Trunca `self._acciones` mediante `del self._acciones[nuevoTotalAcciones:]`.
  - Elimina de `self._puntosControl` cualquier punto cuyo `numAccion > nuevoTotalAcciones` desapilando desde el final con `pop()`.
  - **Costo real de recorte**: El costo es **proporcional a la cantidad de acciones descartadas** ($O(\Delta)$, donde $\Delta = \text{acciones deshechas}$). Como el pergamino de retroceso del juego revierte como máximo 5 acciones, $\Delta \le 5$, el costo de recorte está estrictamente acotado a como máximo 5 acciones , sin recorrer jamás la historia acumulada previa de la partida.

### 1.4 Formateo de la Consulta Histórica
- Función `formatearResumenHistoria(modelo, numAccion=None, reloj=None)`:
  - Extrae y formatea en texto plano conforme a la especificación (§3.6):
    - Encabezado con reloj virtual y número de acción (o sólo reloj si es por tiempo).
    - Sala actual del jugador (ID y nombre).
    - Estadísticas del jugador: vida actual/máxima, ataque (+bono), defensa (+bono), velocidad.
    - Inventario con conteo y nombres catalogados de los objetos.
    - Efectos activos con conteo, nombres traducidos por `nombreEfecto(clase)` y duración restante en pulsos.
    - Enemigos presentes en la sala con ID de instancia y vida actual/máxima.
    - Mapa conocido con conteo de salas exploradas y avistadas.

### 1.5 Persistencia y Formato Binario (`adapters/guardadoPartida.py`)
- Se incrementa `VERSION_FORMATO = 3`.
- Se añade la sección `"linea_tiempo"` a `SECCIONES`.
- Al guardar: se empaqueta la salida de `self.lineaTiempo.capturar()` (diccionario con `k`, `puntosControl` y `acciones`).
- Al cargar:
  - Si el encabezado declara `version == 2` (Parte I), se lanza un `ValueError("Formato incompatible: el archivo es de la versión 2 (Parte I) y no contiene la línea de tiempo requerida en la Parte II.")`.
  - Si la versión es 3, se restaura la línea de tiempo mediante `self.lineaTiempo.restaurar(datos)` junto con el resto del estado.

---

## 2. Contratos de Interfaz (Pendientes de confirmación)

### 2.1 Contratos con Jurnier
1. **Guardado binario (`adapters/guardadoPartida.py`)**:
   - Persistencia y restauración de la sección `"linea_tiempo"` dentro de `VERSION_FORMATO = 3`.
   - Empaque determinista de checkpoints (`numAccion`, `reloj`, `snapshot`) y lista de acciones (`numAccion`, `tipo`, `argumento`, `reloj`).
   - Detección explícita y rechazo con `ValueError` ante archivos de versión 2 sin línea de tiempo.
2. **Reversión y aislamiento del mapa conocido (`model/MapaConocido.py`)**:
   - Al consultar la historia o recortar por retroceso, las salas exploradas y avistadas reflejadas deben corresponder con exactitud al instante histórico consultado.
   - La re-simulación histórica jamás debe mutar ni contaminar el objeto `mapaConocido` del modelo vivo de la partida.

### 2.2 Contrato con Diego
1. **Reproducción no interactiva `--replay <log> --hasta <t>` (`main.py` y `controller/ControladorJuego.py`)**:
   - Reproducción de la bitácora sin inicializar la vista interactiva (`pygame` ni consola de interacción con usuario).
   - Ejecución de las acciones de la bitácora hasta el instante $t$ virtual.
   - Emisión a la salida estándar (`stdout`) del resumen producido por `formatearResumenHistoria`.
   - Si la partida concluyó antes del instante $t$, emisión del estado final acompañada de un mensaje explícito indicando la terminación anticipada.

---

## 3. Módulos Afectados y Verificación de Nombres

1. **`model/LineaTiempo.py`**:
   - Clases: `PuntoControl`, `RegistroAccion`, `LineaTiempo`.
   - Atributos de `LineaTiempo`: `self.k`, `self._puntosControl`, `self._acciones`.
   - Métodos de `LineaTiempo`:
     - `registrarPuntoControl(numAccion, reloj, snapshot)`
     - `debeCrearPuntoControl(numAccion)`
     - `registrarAccion(numAccion, accion, relojDecision)`
     - `recortar(nuevoTotalAcciones)`
     - `cantidadPuntosControl()`
     - `cantidadAcciones()`
     - `buscarPuntoControlMasCercanoAccion(k)`
     - `buscarPuntoControlMasCercanoTiempo(t)`
     - `consultarAccion(modeloBase, k)`
     - `consultarTiempo(modeloBase, t)`
     - `capturar()`
     - `restaurar(datos)`
   - Funciones del módulo: `nombreEfecto(clase)`, `formatearResumenHistoria(modelo, numAccion=None, reloj=None)`, `_crearModeloAuxiliar(proveedor, semilla, snapshot)`.
2. **`model/Juego.py` (`Modelo`)**:
   - Atributo: `self.lineaTiempo = LineaTiempo(k=getattr(self, "kCheckpoint", 20))` instanciado en el constructor.
   - Inicialización: `self.lineaTiempo.registrarPuntoControl(0, self.reloj, self.capturarEstado())` en `iniciarPartida()`.
   - Registro de acción y punto: en `ejecutar(accion)`, invocando `registrarAccion` y evaluando `debeCrearPuntoControl` para llamar a `registrarPuntoControl`.
   - Recorte en retroceso: invocación a `self.lineaTiempo.recortar(self.jugador.acciones)` dentro de `_retroceder()`.
   - Métodos de consulta pública:
     - `consultarHistoriaAccion(k)`: delega en `self.lineaTiempo.consultarAccion(self, k)`.
     - `consultarHistoriaTiempo(t)`: delega en `self.lineaTiempo.consultarTiempo(self, t)`.
   - Métodos de estado: `capturarEstado()` (llama a `estado.capturar(self)`) y `restaurarEstado(datos)` (llama a `estado.restaurar(self, datos)`).
3. **`controller/ControladorJuego.py`**:
   - Comandos interactivos `historia <t>` e `historia #k` en `procesar()`, delegando en `_mostrarHistoria(arg)`.
   - Soporte para argumento `hastaReloj` en `reproducirHasta()`.
4. **`adapters/guardadoPartida.py`**:
   - `VERSION_FORMATO = 3` y sección `"linea_tiempo"`.
   - Detección y rechazo explícito de versiones anteriores.
5. **`main.py`**:
   - Banderas CLI `--checkpoint-cada K` y `--hasta <t>`.
   - Ejecución `--replay <log> --hasta <t>` sin instanciar la vista interactiva.
6. **`tests/test_linea_tiempo.py`**:
   - Suite de pruebas de aceptación y unitarias para FR-029 a FR-038.
   - Prueba de no afectación de red ni mutación de caché durante consultas históricas.
7. **`bench/BenchLineaTiempo.py`**:
   - Medición de memoria retenida y tiempos de consulta para $K \in [5, 20, 50, \infty]$.
   - Evaluación sobre 5 000 acciones.

---

## 4. Complejidad y Criterios de Rendimiento

### 4.1 Complejidad Teórica
- **Registro de acción**: $O(1)$ la mayor parte de las veces. Cada $K$ acciones se captura un punto de control con costo $O(\text{tamaño del snapshot})$, amortizado a $O(\text{tamaño del snapshot} / K)$ por acción.
- **Memoria total**: $O(\frac{N}{K} \cdot S + N \cdot A)$, donde $S$ es el tamaño de un snapshot completo y $A$ es el tamaño de un `RegistroAccion` ($A \ll S$).
- **Consulta histórica**: $O(\log(N / K) + K \cdot \text{costo\_accion}) = O(K)$. Para $K = 20$, re-simular como máximo 19 acciones toma típicamente menos de 5 ms.
- **Recorte ante retroceso**: $O(\Delta)$, proporcional a la cantidad de acciones descartadas ($\Delta \le 5$), acotado como máximo a 5 acciones.

### 4.2 Criterio de Rendimiento contra el Límite de 50 ms
- Conforme al Principio IX de la Constitución del Proyecto CRIPTA y el requisito PR-007, el límite presupuestario para la consulta `historia` es de **50 ms**.
- **Criterio estricto de aceptación**: La métrica comparada contra el límite de 50 ms es el **peor caso por consulta (tiempo máximo observado)**, y **no la mediana ni el promedio**, medido sobre una partida sintética de al menos **5 000 acciones continuas** del jugador con el valor por defecto $K = 20$.

---

## 5. Cumplimiento Constitucional (Principio I)

- **Prohibición de bibliotecas y estructuras nativas en caminos evaluados**:
  - Está **prohibido** el uso de `dict`, `set`, `frozenset`, `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `Counter`, `defaultdict`), `networkx` o cualquier biblioteca de grafos o utilidades de búsqueda.
  - La búsqueda binaria de puntos de control se implementa a mano en métodos propios (`buscarPuntoControlMasCercanoAccion` y `buscarPuntoControlMasCercanoTiempo`).
  - Los registros de puntos y acciones utilizan clases con `__slots__` optimizadas (`PuntoControl` y `RegistroAccion`).
  - El almacenamiento contiguo se realiza exclusivamente con listas estándar de Python (`list`) tratadas como arreglos contiguos.
