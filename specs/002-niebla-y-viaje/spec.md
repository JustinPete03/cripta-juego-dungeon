# Especificación: Niebla de Guerra y Viaje Automático («ir a»)

**Carpeta**: `specs/002-niebla-y-viaje`  
**Creada**: 2026-11-01  
**Estado**: Especificada y clarificada

---

## Clarificaciones

### Sesión 2026-11-01, con las reglas actualizadas tras la revisión

- **Q1: ¿Cuándo pasa una sala a estar Explorada, Avistada o Desconocida?**
  - **Explorada**: El jugador ha entrado en la sala al menos una vez, incluida la sala inicial en t=0, o la ha revelado con una antorcha encendida. El mapa muestra su nombre, sus salidas, el costo de cada salida y el estado recordado de sus puertas.
  - **Avistada**: La sala nunca fue explorada, pero es destino de una salida de una sala explorada. El jugador solo conoce su identificador.
  - **Desconocida**: La sala no es explorada ni avistada. El jugador no tiene información sobre ella.

- **Q2: ¿Cómo funciona la memoria de puertas del jugador?**
  - El jugador observa el estado real de una puerta cuando se encuentra en cualquiera de las dos salas que conecta. El mapa muestra el último estado observado, «abierta» o «cerrada». Si todavía no hubo ninguna observación, muestra «sin observar».
  - Si una puerta cambia mientras el jugador está lejos, el mapa conserva el último estado observado. La observación se actualiza cuando el jugador vuelve a una de las salas contiguas o presencia un cambio mientras está en una de ellas.

- **Q3: ¿Qué efecto tiene la antorcha encendida?**
  - Al entrar en una sala con la antorcha encendida, quedan exploradas todas sus vecinas, incluso las conectadas por una puerta cerrada. Se revelan sus nombres, salidas y costos. La observación de puertas se limita a las que conectan con la sala donde está el jugador.
  - Revelar una sala vecina no despierta a sus enemigos ni activa sus trampas. Si se usa un pergamino de retroceso, las salas exploradas por la antorcha durante ese paso vuelven a su estado previo.

- **Q4: ¿Cómo se comporta el comando `ir a <destino>`?**
  - Solo acepta destinos explorados. Si el destino no está explorado, se rechaza de inmediato sin consumir tiempo virtual.
  - Calcula la ruta de costo mínimo por salas exploradas y salidas cuyas puertas se recuerdan abiertas. Una puerta «sin observar» queda fuera del cálculo, aunque esté abierta en la cripta.
  - Desempata de la misma forma que el cazador: el primer paso va hacia la vecina de menor ID entre las rutas óptimas.
  - Cada paso es un movimiento ordinario. Consume tiempo según el costo de la salida y la velocidad del jugador. Los eventos del reloj virtual se despachan normalmente.
  - El viaje no abre puertas cerradas aunque el jugador tenga la llave correspondiente.
  - La ruta se recalcula antes de cada paso.

- **Q5: ¿Cuándo se interrumpe el viaje de `ir a`?**
  - Si la sala de partida contiene enemigos, el viaje se detiene antes del primer movimiento, sin consumir tiempo virtual.
  - Durante el viaje, se detiene al llegar al destino, al terminar un paso en una sala con enemigos, al recibir daño durante un paso o cuando ya no hay una ruta conocida. Recibir daño provoca la detención aunque una curación durante el mismo paso recupere toda la vida perdida.

- **Q6: ¿Cómo interactúa el pergamino de retroceso con `ir a`?**
  - Como cada paso de `ir a` es una acción de movimiento individual, el pergamino revierte únicamente el último paso dado y el viaje automático se cancela.

- **Q7: ¿Cómo se registra `ir a` en `partida.log`?**
  - Cada paso se registra como un movimiento normal (`n`, `s`, `e`, `o`). La orden `ir a <sala>` se anota como un comentario previo `# ir a <sala>` para trazabilidad.

- **Q8: ¿Qué comando permite visualizar el mapa conocido?**
  - El comando `mapa` muestra las salas exploradas, sus salidas con sus costos, el estado recordado de las puertas y las salas avistadas.

---

## Historias de usuario

### US-1: Conocimiento parcial del mapa y memoria de puertas (Prioridad P1)

Como jugador, quiero que el mapa refleje las salas que conozco y el estado de las puertas que he observado para experimentar la niebla de guerra.

**Escenarios de aceptación**

1. **Sala inicial explorada.** Al iniciar la partida en t=0, la sala inicial está explorada y sus vecinas están avistadas. Las demás salas son desconocidas.
2. **Actualización de puerta observada.** El jugador observa una puerta abierta. Si la puerta se cierra automáticamente mientras el jugador está lejos, el mapa sigue mostrando «abierta» hasta que el jugador vuelve a una de las salas que conecta. Entonces muestra «cerrada».
3. **Efecto de la antorcha.** Al entrar en A con la antorcha encendida, quedan exploradas todas sus vecinas. Si B es vecina de A y tiene una salida hacia C cuya puerta el jugador nunca observó, el mapa muestra B como explorada, A–B con su estado observado y B–C como «sin observar». Revelar B tampoco activa sus enemigos ni sus trampas.
4. **Retroceso con antorcha.** Si se usa un pergamino tras un paso que reveló vecinas con la antorcha, se restaura el estado previo de esas salas y de las observaciones de puertas que cambiaron durante el paso.
5. **Puerta abierta sin observar.** Si una puerta está abierta en la cripta y el jugador nunca la ha observado, `mapa` muestra «sin observar».

### US-2: Viaje automático mediante `ir a` (Prioridad P1)

Como jugador, quiero poder trasladarme automáticamente entre salas exploradas mediante `ir a <sala>`, ahorrando comandos manuales repetitivos pero respetando el tiempo y los peligros del mundo.

**Escenarios de aceptación**

1. **Rechazo hacia sala no explorada.** `ir a` hacia una sala no explorada se rechaza sin consumir tiempo virtual.
2. **Ruta mínima y desempate.** Se elige el camino de menor costo entre salas exploradas y puertas recordadas como abiertas. Si hay empate, se avanza hacia la vecina de menor ID.
3. **Paso a paso con el reloj virtual.** Cada paso ejecuta un movimiento normal con el costo de la salida y permite que se ejecuten los eventos programados.
4. **Puerta cerrada en ruta.** Si el mapa recordaba una puerta abierta y el jugador observa que ahora está cerrada, se actualiza el mapa y se recalcula la ruta. Si ya no queda una ruta conocida abierta, el viaje se detiene sin consumir tiempo adicional.
5. **Detención por enemigos.** Si tras un paso hay enemigos en la sala, el viaje se detiene. Los enemigos dormidos de la sala a la que entra el jugador se activan normalmente.
6. **Detención por daño.** En un paso intermedio, el jugador recibe daño y una curación en ese mismo paso recupera la vida perdida. El viaje se detiene por daño antes de iniciar el siguiente paso.
7. **Retroceso durante el viaje.** Un pergamino de retroceso revierte únicamente el último paso y el viaje no continúa.
8. **Puerta sin observar en la ruta.** Si la única ruta hacia una sala explorada pasa por una puerta abierta que el jugador nunca observó, `ir a` se detiene por falta de ruta conocida.
9. **Enemigos en la sala de partida.** Si el jugador ordena `ir a` hacia otra sala explorada mientras hay enemigos en su sala actual, el viaje se detiene antes del primer movimiento. La posición del jugador y el reloj virtual quedan iguales.

---

## Requisitos funcionales

- **FR-011**: Toda sala se encuentra para el jugador en estado `Explorada`, `Avistada` o `Desconocida`.
- **FR-012**: La sala inicial está explorada desde el instante 0.
- **FR-013**: El mapa conocido muestra el último estado observado de cada puerta, «abierta» o «cerrada», o «sin observar» si nunca se observó. El jugador observa una puerta únicamente desde una de las dos salas que conecta.
- **FR-014**: Mientras la antorcha esté encendida, entrar en una sala explora automáticamente todas sus vecinas a través de cualquier salida. Se revelan su nombre, sus salidas y sus costos. Sus contenidos quedan inactivos y las puertas ajenas a la sala del jugador conservan su estado recordado.
- **FR-015**: Las alteraciones al mapa conocido (salas exploradas y memoria de puertas) son parte del estado del juego y se revierten fielmente con el pergamino de retroceso.
- **FR-016**: El comando `ir a <sala>` solo acepta salas exploradas. Si el destino no está explorado, se rechaza sin consumir tiempo.
- **FR-017**: `ir a` usa únicamente salas exploradas y salidas cuyas puertas se recuerdan abiertas. La ruta minimiza la suma de costos y desempata por menor ID de vecina en el primer paso.
- **FR-018**: Cada paso de `ir a` es un movimiento ordinario. El viaje se detiene antes de avanzar si hay enemigos en la sala de partida. Durante el viaje se detiene al llegar al destino, si termina un paso en una sala con enemigos, si el jugador recibe daño durante un paso o si deja de haber una ruta conocida. Una curación en el mismo paso no cancela la detención por daño.
- **FR-019**: `ir a` no abre puertas aunque el jugador posea la llave.
- **FR-020**: El comando `mapa` muestra las salas exploradas, sus salidas conocidas con sus costos, el estado recordado de las puertas y las salas avistadas.

---

## Requisitos de rendimiento

- **PR-003**: El cálculo de un paso de `ir a` sobre el mapa conocido completo de la cripta de referencia toma menos de 5 ms en el peor caso medido (§6.1).
- **PR-004**: Explorar nuevas salas cuesta proporcionalmente a las salas reveladas, independientemente del tamaño total del mapa conocido (§5.3).