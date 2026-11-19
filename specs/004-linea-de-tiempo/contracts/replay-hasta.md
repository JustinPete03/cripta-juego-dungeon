# Contrato de Interfaz: Reproducción no Interactiva `--replay ... --hasta <t>`

**Contraparte**: Diego (Módulo CLI y Replay)  
**Feature**: `004-linea-de-tiempo`  
**Módulos**: `main.py`, `controller/ControladorJuego.py`, `model/LineaTiempo.py`

---

## 1. Interfaz de Línea de Comandos (`main.py`)

- **Banderas**:
  - `--replay <ruta_archivo.log>`: Activa el modo de reproducción.
  - `--hasta <t>`: Instante de reloj virtual límite hasta el cual se debe reproducir la simulación.
  - `--checkpoint-cada <K>`: Frecuencia de puntos de control (por defecto 20).
- **Invariante no interactivo**: No se debe instanciar `pygame`, ni inicializar ventanas gráficas ni pedir entradas interactivas al usuario (`sys.stdin`).

---

## 2. Salida y Comportamiento (`controller/ControladorJuego.py`)

- Se reproducen las acciones del archivo de registro hasta el instante $t$.
- Se emite a la salida estándar (`stdout`) el resumen formateado por `formatearResumenHistoria(modelo, reloj=t)`.
- **Terminación anticipada**: Si el instante $t$ solicitado supera el reloj final de la partida (muerte o escape del jugador), se reproduce hasta el desenlace de la partida, se emite el estado final y se indica explícitamente en `stdout` que la partida concluyó antes del instante solicitado.
