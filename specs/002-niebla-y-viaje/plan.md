# Plan de Implementación: Niebla de Guerra y Viaje Automático («ir a»)

**Rama**: `002-niebla-y-viaje` | **Fecha**: 2026-11-01 | **Spec**: [spec.md](spec.md)

---

## Resumen

Implementar la niebla de guerra y memoria de puertas a través de una clase propia `MapaConocido` en el modelo, registrar sus mutaciones en el `Diario` reversible para soporte de retroceso, e incorporar el comando interactivo `mapa` y la orden `ir a <sala>` con recálculo paso a paso y desempate determinista sobre el subgrafo conocido.

---

## Verificación de la Constitución

1. **Estructuras propias**: PASA. `MapaConocido` utiliza `Tabla` propia (`model/Tabla.py`) para registrar salas exploradas y memoria de puertas. Sin `dict` ni `set`.
2. **Determinismo**: PASA. Desempate idéntico al cazador: primer paso hacia la vecina de menor ID.
3. **Separación MVC**: PASA. El subgrafo conocido es estado del modelo. El controlador orquesta los pasos de `ir a`.
4. **Reversibilidad y persistencia**: PASA. Toda revelación de sala o cambio en memoria de puertas registra su inversa en el `Diario`.

---

## Estructura de Datos: `MapaConocido` (model/MapaConocido.py)

### Campos de estado:
* `_exploradas`: `Tabla` con `idSala -> True`.
* `_memoriaPuertas`: `Tabla` con `idPuerta -> bool` (True si recordada cerrada, False si recordada abierta).
* `_registrador`: callback hacia el `Diario` para registrar operaciones inversas.

### Métodos principales:
* `explorarSala(sala)`: Marca una sala como explorada e inspecciona sus salidas para registrar en memoria de puertas el estado actual observado.
* `actualizarPuertasObservadas(sala)`: Si el jugador está en `sala`, actualiza la memoria de todas las puertas de sus salidas directas.
* `estadoSala(idSala, esqueleto)`: Devuelve `EXPLORADA`, `AVISTADA` o `DESCONOCIDA`.
* `puertaRecordadaAbierta(puerta)`: Consulta la memoria del jugador. Si nunca fue observada, se asume su estado del esqueleto.
* `revertirExploracion(salaId)`: Utilizada por el closure inverso en el `Diario`.

---

## Algoritmo de Búsqueda para «ir a» (`model/Dijkstra.py`)

Se reutiliza el motor de Dijkstra propio (`MinHeapDijkstra`), adaptándolo para ejecutar sobre el subgrafo conocido del jugador:
* Solo transita por salas donde `mapaConocido.estaExplorada(idSala) == True`.
* Solo atraviesa salidas donde `mapaConocido.puertaRecordadaAbierta(puerta) == True`.
* Desempate determinista: búsqueda inversa desde el destino hacia las salas conocidas; el jugador en $u$ escoge la vecina $v$ que minimice el costo total y desempatando por $\min(v.id)$.

---

## Control del Viaje Automático (`controller/ControladorJuego.py`)

Al recibir `ir a <sala>`:
1. Validar que la sala destino esté en `mapaConocido.estaExplorada(destinoId)`. Si no, rechazar sin tiempo.
2. Iniciar bucle de pasos:
   * Guardar vida previa del jugador.
   * Recalcular ruta con el conocimiento vigente.
   * Si no hay ruta, detenerse informando que no hay camino abierto conocido.
   * Ejecutar la acción ordinaria de movimiento (`ACC_MOVER`).
   * Condiciones de parada inmediata:
     - Llegada al destino.
     - Presencia de enemigos en la sala destino (dormidos o activos).
     - Pérdida de vida / daño recibido durante el turno.
     - Fin de partida (victoria o derrota).
3. Bitácora: Registrar `# ir a <destino>` como comentario previo a los movimientos en `partida.log`.

---

## Mecánica de la Antorcha (`model/efectos.py` y `model/Juego.py`)

En `model/Juego.py`, al ejecutarse `_aplicarMover(destino)`:
* Si el efecto antorcha está activo en el jugador (`modelo.efectos.antorchaActiva(modelo)`):
  * Para cada salida de `destino`:
    * La sala vecina se marca como explorada mediante `mapaConocido.explorarVecinaAntorcha(vecina)`.
    * No se carga su contenido ni se activan enemigos/trampas.
    * Cada revelación registra su inversa en el `Diario`.
