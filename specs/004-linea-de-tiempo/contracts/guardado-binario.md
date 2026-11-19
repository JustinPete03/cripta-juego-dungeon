# Contrato de Interfaz: Guardado Binario y Reversión de Mapa

**Contraparte**: Jurnier (Módulo de Persistencia y Mapa)  
**Feature**: `004-linea-de-tiempo`  
**Módulos**: `adapters/guardadoPartida.py`, `model/MapaConocido.py`, `model/LineaTiempo.py`

---

## 1. Persistencia Binaria (`adapters/guardadoPartida.py`)

- **Versión del Formato**: `VERSION_FORMATO = 3`.
- **Sección añadida**: `"linea_tiempo"`.
- **Estructura serializada de la línea de tiempo**:
  - `k`: Entero con la frecuencia de checkpoints.
  - `puntosControl`: Lista de objetos/diccionarios con `numAccion`, `reloj` y `snapshot`.
  - `acciones`: Lista de tuplas/listas `[numAccion, tipo, argumento, reloj]`.
- **Compatibilidad hacia atrás**:
  - Si el encabezado del archivo declara `version == 2` (Parte I), el deserializador debe lanzar `ValueError("Formato incompatible: el archivo es de la versión 2 (Parte I) y no contiene la línea de tiempo requerida en la Parte II.")`.
  - Si la versión es 3, el cargador invoca `lineaTiempo.restaurar(datos)`.

---

## 2. Reversión y Aislamiento del Mapa Conocido (`model/MapaConocido.py`)

- Al consultar `historia <t>` o `historia #k`, el snapshot restaurado contiene las salas exploradas y avistadas hasta ese instante.
- **Invariante de Aislamiento**: La re-simulación en el modelo réplica no debe invocar métodos que modifiquen el `mapaConocido` del modelo vivo de la partida.
- **Invariante de Retroceso**: Cuando el jugador usa un pergamino de retroceso, el mapa conocido regresa al estado correspondiente a las acciones retenidas tras `lineaTiempo.recortar()`.
