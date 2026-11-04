# Especificación: Niebla de Guerra y Viaje Automático («ir a»)

**Carpeta**: `specs/002-niebla-y-viaje`
**Creada**: 2026-11-01
**Estado**: Especificada y clarificada

---

## Clarificaciones

### Sesión 2026-11-01

- **Q1: ¿Cuándo pasa una sala a estar Explorada vs Avistada vs Desconocida?**
  - **Decisión**:
    - **Explorada**: Cuando el jugador entra a ella al menos una vez (la inicial en t=0), o cuando se explora como vecina por efecto de una antorcha encendida. Revela nombre, salidas, costo de cada salida y estado de sus puertas según la última observación.
    - **Avistada**: Sala que nunca fue explorada, pero es destino de una salida de una sala explorada. El jugador solo sabe que existe una sala allí (su ID).
    - **Desconocida**: Cualquier sala que no sea explorada ni avistada. El jugador no sabe nada de ella.

- **Q2: ¿Cómo funciona la memoria de puertas del jugador?**
  - **Decisión**: El jugador observa el estado real de una puerta siempre que esté en cualquiera de las dos salas que conecta. El mapa conocido recuerda ese estado observado. Si la puerta cambia posteriormente (ej. cierre automático diferido) sin que el jugador esté en una de las dos salas contiguas, el mapa sigue recordando el estado previo hasta que el jugador vuelva a una de esas salas.

- **Q3: ¿Qué efecto tiene la Antorcha encendida?**
  - **Decisión**: Mientras la antorcha esté encendida, al entrar a una sala quedan exploradas inmediatamente todas sus vecinas (a través de salidas abiertas o cerradas). Esto revela el nombre y salidas de las vecinas, pero NO su contenido interior (no despierta enemigos ni activa trampas). Si se usa un pergamino de retroceso, las salas exploradas por antorcha en ese paso vuelven a su estado previo.

- **Q4: ¿Cómo se comporta el comando `ir a <destino>`?**
  - **Decisión**:
    - Solo permite destinos que estén en estado *Explorada*. Si el destino no está explorado, se rechaza de inmediato sin consumir tiempo virtual.
    - Calcula la ruta de costo mínimo utilizando **únicamente** salas exploradas y salidas recordadas como abiertas.
    - Desempata de la misma forma que el cazador: primer paso hacia la vecina de menor ID entre las óptimas.
    - Cada paso es una acción ordinaria de movimiento del jugador: consume tiempo según el costo de la salida y la velocidad, y entre paso y paso se despachan normalmente los eventos del reloj virtual.
    - No abre puertas cerradas aunque el jugador tenga la llave correspondiente.
    - Recalcula la ruta antes de cada paso.

- **Q5: ¿Cuándo se interrumpe el viaje de `ir a`?**
  - **Decisión**: El viaje se detiene cuando:
    1. Llega a la sala destino.
    2. El jugador entra a una sala que contiene enemigos (activos o dormidos).
    3. El jugador recibe daño (por trampa, veneno, ataque, etc.).
    4. Se actualiza una puerta observada como cerrada y ya no existe una ruta conocida abierta hacia el destino.

- **Q6: ¿Cómo interactúa el pergamino de retroceso con `ir a`?**
  - **Decisión**: Como cada paso de `ir a` es una acción de movimiento individual, el pergamino revierte únicamente el último paso dado, y el viaje automático se cancela (no continúa).

- **Q7: ¿Cómo se registra `ir a` en `partida.log`?**
  - **Decisión**: Cada paso se registra como un movimiento normal (`n`, `s`, `e`, `o`). La orden `ir a <sala>` se anota como un comentario previo `# ir a <sala>` para trazabilidad.

- **Q8: ¿Qué comando permite visualizar el mapa conocido?**
  - **Decisión**: El comando `mapa` en la consola muestra las salas exploradas, sus salidas conocidas y las salas avistadas.

---

## Historias de usuario

### US-1: Conocimiento parcial del mapa y memoria de puertas (Prioridad P1)

Como jugador, solo debo conocer las salas que he explorado y las puertas que he observado, para experimentar la niebla de guerra.

**Escenarios de aceptación**:

1. **Sala inicial explorada**: Al iniciar la partida en t=0, la sala inicial está explorada y sus vecinas están avistadas. Las demás salas son desconocidas.
2. **Actualización de puerta observada**: El jugador observa el estado de una puerta cuando se encuentra en una sala que la contiene. Si una puerta se cierra automáticamente mientras el jugador está lejos, el mapa conocido sigue creyendo que está abierta hasta que el jugador entra a una de las salas contiguas.
3. **Efecto de la antorcha**: Con la antorcha encendida, al entrar a una sala, todas sus vecinas pasan a estado exploradas (con nombre y salidas visibles) sin que sus enemigos o trampas se activen.
4. **Retroceso con antorcha**: Si se usa un pergamino de retroceso tras haber explorado vecinas con antorcha, la exploración de esas vecinas se revierte a su estado anterior.

### US-2: Viaje automático mediante `ir a` (Prioridad P1)

Como jugador, quiero poder trasladarme automáticamente entre salas exploradas mediante `ir a <sala>`, ahorrando comandos manuales repetitivos pero respetando el tiempo y los peligros del mundo.

**Escenarios de aceptación**:

1. **Rechazo hacia sala no explorada**: `ir a` hacia una sala no explorada se rechaza y no consume tiempo virtual.
2. **Ruta mínima y desempate**: Se elige el camino de menor costo sobre salas exploradas y puertas recordadas como abiertas. Si hay empate, se avanza hacia la vecina de menor ID.
3. **Paso a paso con tiempo real del reloj**: Cada paso ejecuta un movimiento normal con costo de salida y permite la ejecución de eventos programados del reloj entre pasos.
4. **Puerta cerrada en ruta**: Si el mapa recordaba abierta una puerta pero al llegar el jugador observa que está cerrada, el mapa se actualiza y la ruta se recalcula; si no queda ruta abierta conocida, el viaje se detiene sin consumir tiempo adicional.
5. **Detención por enemigos**: Si un paso entra a una sala con enemigos (dormidos o activos), los enemigos dormidos se activan normalmente y el viaje se detiene inmediatamente.
6. **Detención por daño**: Si el jugador recibe daño durante un paso, el viaje se detiene.
7. **Retroceso durante viaje**: Un pergamino de retroceso revierte únicamente el último paso y el viaje no continúa.

---

## Requisitos funcionales

- **FR-011**: Toda sala se encuentra para el jugador en estado `Explorada`, `Avistada` o `Desconocida`.
- **FR-012**: La sala inicial está explorada desde el instante 0.
- **FR-013**: El mapa conocido guarda la última observación del estado de cada puerta (`abierta` o `cerrada`). La observación se actualiza cuando el jugador entra o está en cualquiera de las dos salas conectadas por la salida.
- **FR-014**: Mientras la antorcha esté encendida, entrar a una sala explora automáticamente todas sus salas vecinas a través de cualquier salida, revelando su nombre y salidas sin activar sus contenidos.
- **FR-015**: Las alteraciones al mapa conocido (salas exploradas, memoria de puertas) son parte del estado del juego y se revierten fielmente con el pergamino de retroceso.
- **FR-016**: El comando `ir a <sala>` solo acepta salas exploradas; de lo contrario se rechaza sin consumir tiempo.
- **FR-017**: La ruta de `ir a` se calcula sobre el subgrafo de salas exploradas y salidas recordadas abiertas, minimizando la suma de costos y desempatando por menor ID de vecina.
- **FR-018**: Cada paso de `ir a` es una acción de movimiento ordinaria; el viaje se detiene si se llega al destino, si se entra a una sala con enemigos, si el jugador recibe daño o si deja de haber ruta conocida.
- **FR-019**: `ir a` no abre puertas aunque el jugador posea la llave.
- **FR-020**: La interfaz ofrece el comando `mapa` para mostrar las salas exploradas, salidas conocidas y salas avistadas.

---

## Requisitos de rendimiento

- **PR-003**: El cálculo de un paso de `ir a` sobre el mapa conocido completo toma menos de 5 ms (§6.1).
- **PR-004**: Explorar nuevas salas cuesta proporcionalmente a las salas reveladas, no al tamaño total del mapa conocido (§5.3).
