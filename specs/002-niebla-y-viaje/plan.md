# Plan de Implementación: Niebla de Guerra y Viaje Automático («ir a»)

**Rama**: `002-niebla-y-viaje` | **Fecha**: 2026-11-01 | **Spec**: [spec.md](spec.md)

---

## Resumen

Implementar la niebla de guerra y memoria de puertas a través de una clase propia `MapaConocido` en el modelo, registrar sus mutaciones en el `Diario` reversible para soporte de retroceso, e incorporar el comando interactivo `mapa` y la orden `ir a <sala>` con recálculo paso a paso y desempate determinista sobre el subgrafo conocido. La antorcha revela las salas vecinas y la observación de puertas se limita a la sala del jugador. El viaje usa el núcleo de búsqueda de la spec 005.

---

## Verificación de la Constitución

1. **Estructuras propias**: PASA. `MapaConocido` utiliza `Tabla` propia (`model/Tabla.py`) para registrar salas exploradas y memoria de puertas. Sin `dict` ni `set`.
2. **Determinismo**: PASA. Desempate idéntico al cazador: primer paso hacia la vecina de menor ID.
3. **Separación MVC**: PASA. El modelo conserva el mapa conocido, valida el viaje y ejecuta cada paso. El controlador repite los pasos, los registra en la bitácora y muestra el motivo de detención.
4. **Reversibilidad y persistencia**: PASA. Cada nueva revelación de sala o cambio en la memoria de puertas registra su inversa en el `Diario`.

---

## Estructura de Datos: `MapaConocido` (model/MapaConocido.py)

### Campos de estado:

* `_exploradas`: `Tabla` con `idSala -> True`.
* `_memoriaPuertas`: `Tabla` con una clave formada por los dos IDs de sala, ordenados para consultar la conexión en ambos sentidos. El valor es `True` si se recuerda cerrada y `False` si se recuerda abierta. Si la clave está ausente, la puerta está sin observar.
* `_registrador`: callback hacia el `Diario` para registrar operaciones inversas.

### Métodos principales:

* `marcarExplorada(sala)`: Marca una sala como explorada y registra su inversa si el estado cambia. Se usa para las vecinas reveladas por la antorcha.
* `explorarSala(sala)`: Marca la sala del jugador como explorada y llama a `actualizarPuertasObservadas(sala)`.
* `actualizarPuertasObservadas(sala)`: Actualiza la memoria de las puertas de la sala donde está el jugador. La inversa restaura el estado anterior o elimina la observación si fue la primera.
* `estadoSala(idSala, salasIndice)`: Devuelve `ESTADO_EXPLORADA`, `ESTADO_AVISTADA` o `ESTADO_DESCONOCIDA`.
* `estadoPuertaRecordada(uId, vId)`: Devuelve `PUERTA_ABIERTA`, `PUERTA_CERRADA` o `PUERTA_SIN_OBSERVAR` a partir de la memoria.
* `puertaRecordadaAbierta(uId, vId)`: Devuelve `True` únicamente si el jugador recuerda abierta la puerta.

---

## Algoritmo de Búsqueda para «ir a» (`model/Dijkstra.py`)

Se reutilizan `calcularDistancias` y `elegirPrimerPaso` del núcleo de búsqueda de la spec 005 (K-05):

* `_reglaConocimiento(mapaConocido)` admite una salida si su destino está explorado y `puertaRecordadaAbierta(sala.id, salida.destinoId)` devuelve `True`. Una puerta recordada cerrada o sin observar queda fuera de la búsqueda.
* `elegirPasoViajeAutomatico(salaActual, salaDestino, salasIndice, mapaConocido)` calcula las distancias desde el destino y elige una salida que pertenezca a una ruta de costo mínimo. Si varias vecinas cumplen esa condición, elige la de menor ID. Devuelve `(salida, salida.costo)` al encontrar un paso y `(None, None)` cuando no hay ruta. Si origen y destino coinciden, devuelve `(None, 0)`.
* La búsqueda desde el destino se apoya en la simetría de las conexiones: cada salida tiene una inversa con la misma puerta y costo. `tests/test_rutas_invalidacion.py` comprueba esa condición en las criptas de demostración y verifica el costo mínimo y el desempate de «ir a».
* `bench/BenchNiebla.py` mide el cálculo de un paso con el mapa conocido completo. Con `python main.py --bench` se midió `cripta-06`, de 300 salas. En 200 pares de prueba, el promedio fue de 1.098 ms y el peor tiempo medido fue de 2.115 ms, por debajo del límite de 5 ms. Se encontró ruta en 51 pares.

---

## Control del Viaje Automático (`controller/ControladorJuego.py`)

Al recibir `ir a <sala>`:

1. El controlador convierte el identificador a entero y llama a `Modelo.validarViaje(destId)`. El modelo rechaza sin consumir tiempo si no hay una partida en curso, la sala no existe, el destino no está explorado o el jugador ya está allí.
2. El controlador llama a `Modelo.pasoViaje(destId)` hasta que el modelo devuelve un motivo de detención o termina la partida.
   * Si hay enemigos en la sala actual, el modelo detiene el viaje antes de moverse. Esto incluye la sala de partida.
   * El modelo recalcula la ruta con el conocimiento vigente. Si no hay ruta, devuelve el motivo correspondiente.
   * Si hay un paso disponible, ejecuta un movimiento ordinario (`ACC_MOVER`). `aplicarDanio` marca `_jugadorRecibioDanio` si el jugador recibe daño. `pasoViaje` consulta esa marca al finalizar el movimiento, de modo que una curación en el mismo paso no oculte el daño.
   * El viaje se detiene al llegar al destino, si hay enemigos tras el movimiento, si el jugador recibió daño, si el movimiento fue rechazado o si termina la partida.
3. Bitácora: el controlador registra `# ir a <destino>` como comentario previo y anota cada movimiento realizado en `partida.log`. Al terminar, muestra el motivo correspondiente.

Para `mapa`, `_mostrarMapa()` consulta `estadoPuertaRecordada` y muestra «abierta», «cerrada» o «sin observar».

---

## Mecánica de la Antorcha (`model/efectos.py` y `model/Juego.py`)

En `model/Juego.py`, al ejecutarse `_aplicarMover(direccion)`:

* La sala de destino se registra con `mapaConocido.explorarSala(destino)`, que observa las puertas de la sala a la que entró el jugador.
* Si `self.efectos.antorchaEncendida(self.jugador)` indica que la antorcha está activa:
  * Para cada salida de `destino`, la sala vecina se marca como explorada mediante `mapaConocido.marcarExplorada(salida.destino)`.
  * Revelar una vecina no observa sus otras puertas ni activa sus enemigos o trampas.
  * Cada revelación nueva registra su inversa en el `Diario`.