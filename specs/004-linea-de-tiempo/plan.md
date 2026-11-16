# Plan de Implementación: Línea de Tiempo y Puntos de Control

**Feature**: `004-linea-de-tiempo`
**Spec**: [spec.md](spec.md)

---

## 1. Arquitectura y Estructuras de Datos

### 1.1 Modelo de la Línea de Tiempo (`model/LineaTiempo.py`)
- Clase `LineaTiempo`:
  - `_k`: Frecuencia de puntos de control (acciones entre puntos de control, por defecto 20).
  - `_puntosControl`: Lista ordenada de puntos de control. Cada punto de control almacena:
    - `numAccion`: Índice de la acción del jugador (0, $K$, $2K$, ...).
    - `reloj`: Tiempo del reloj virtual en el momento del punto de control.
    - `snapshot`: Copia serializada completa generada por `model.estado.capturar(modelo)`. Incluye el estado del generador `random.Random` (`getstate()`), la agenda, mapa conocido, inventario, etc.
  - `_acciones`: Lista de acciones canónicas ejecutadas por el jugador:
    - Tuplas `(numAccion, accion, relojDecision)`.
  - Búsqueda del punto de control más cercano anterior a una acción $k$ o tiempo $t$:
    - Como los puntos de control se guardan exactamente cada $K$ acciones, el índice del punto de control anterior a la acción $k$ se obtiene directamente como $(k // K) \times K$ en tiempo $O(1)$.
    - Para un tiempo $t$, se realiza una búsqueda binaria en la lista de puntos de control sobre `reloj`, tomando $O(\log(N / K))$.

### 1.2 Reconstrucción de Estados: Hacia Adelante (Forward Re-simulation)
- **Decisión de diseño**: Re-simulación hacia adelante desde el punto de control anterior más cercano.
  - Al consultar `historia <t>` o `historia #k`, se localiza el punto de control previo más cercano (a distancia máxima $K - 1$ acciones).
  - Se instancia un modelo auxiliar / clon mediante `restaurar(modeloAux, snapshot)`.
  - Se re-simulan las acciones del jugador intermedias hasta alcanzar la acción solicitada o el tiempo $t$.
  - Como máximo se ejecutan $K - 1$ acciones, garantizando el cumplimiento estricto del requisito de que ninguna consulta procese más de $K$ acciones.
  - El modelo vivo de la partida permanece intacto y la consulta toma típicamente menos de 1 ms (muy inferior al límite de 50 ms).

### 1.3 Recorte ante Pergamino de Retroceso (Rollback)
- Al ejecutarse `_retroceder()`, se conoce la cantidad de acciones deshechas.
- `lineaTiempo.recortar(nuevasAcciones)`:
  - Trunca la lista `_acciones` a la nueva longitud.
  - Elimina de `_puntosControl` cualquier punto de control cuyo `numAccion` sea superior al nuevo total.
  - Costo de recorte: $O(1)$ amortizado al desapilar desde el final, sin recorrer toda la historia previa.

### 1.4 Formateo de la Consulta Histórica
- Método `resumenEstado(modelo)`:
  - Extrae y formatea en texto plano:
    - Reloj y número de acción.
    - Sala del jugador (ID y nombre).
    - Estadísticas (vida/vida_max, ataque, defensa, velocidad).
    - Inventario (objetos con sus nombres en catálogo).
    - Efectos activos (nombre y duración/pulsos).
    - Enemigos presentes en la sala con su vida actual.
    - Mapa conocido (conteo y lista de exploradas y avistadas).

### 1.5 Persistencia y Formato Binario (`adapters/guardadoPartida.py`)
- Se incrementa `VERSION_FORMATO = 3`.
- Se añade la sección `"linea_tiempo"` a `SECCIONES`.
- Al guardar, se empaca `lineaTiempo.capturar()`.
- Al cargar:
  - Si el encabezado declara `version == 2` (Parte I), se lanza un `ValueError("Formato incompatible: el archivo es de la versión 2 (Parte I) y no contiene la línea de tiempo requerida en la Parte II.")`.
  - Si la versión es 3, se restaura la línea de tiempo junto con el resto del estado.

---

## 2. Módulos Afectados

1. **`model/LineaTiempo.py`** (Nuevo):
   - Estructura `LineaTiempo`, almacenamiento de checkpoints cada $K$ acciones, registro de acciones, recorte en retroceso y método de consulta histórica.
2. **`model/Juego.py`**:
   - Integración de `lineaTiempo` en `Modelo`.
   - Registro de checkpoint en `iniciarPartida()` (acción 0) y tras cada acción del jugador.
   - Llamada a `lineaTiempo.recortar()` en `_retroceder()`.
   - Métodos `consultarHistoriaTiempo(t)` y `consultarHistoriaAccion(k)`.
3. **`controller/ControladorJuego.py`**:
   - Comandos `historia <t>` e `historia #k` en `interpretar()` y `procesar()`.
   - Soporte para argumento `hastaReloj` en `reproducir()`.
4. **`adapters/guardadoPartida.py`**:
   - Soporte para `VERSION_FORMATO = 3` y sección `"linea_tiempo"`.
   - Detección explícita y rechazo de archivos versión 2.
5. **`main.py`**:
   - Banderas `--checkpoint-cada K` y `--hasta <t>`.
   - Integración con `--replay <log> --hasta <t>` sin instanciar la vista.
6. **`tests/test_linea_tiempo.py`** (Nuevo):
   - Pruebas unitarias y de aceptación de todas las historias de usuario de la línea de tiempo.
7. **`bench/BenchLineaTiempo.py`** (Nuevo):
   - Medición de memoria y tiempo de consulta para $K \in [5, 20, 50, \infty]$.
   - Verificación de consulta en partida de 5 000 acciones en $< 50$ ms.

---

## 3. Complejidad Esperada

- **Registro de acción**: $O(1)$ la mayor parte de las veces. Cada $K$ acciones se realiza un punto de control con costo $O(\text{tamaño del estado})$, amortizado a $O(\text{tamaño del estado} / K)$ por acción.
- **Memoria total**: $O(\frac{N}{K} \cdot S + N \cdot A)$, donde $S$ es el tamaño del snapshot y $A$ es el tamaño de una acción ($A \ll S$).
- **Consulta histórica**: $O(\log(N / K) + K \cdot \text{costo\_accion}) = O(K)$. Para $K = 20$, re-simular 20 acciones toma $< 1$ ms.
- **Recorte por retroceso**: $O(1)$ desapilando los últimos elementos.
