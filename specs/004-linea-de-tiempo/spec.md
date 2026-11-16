# Especificación: Línea de Tiempo y Puntos de Control

**Carpeta**: `specs/004-linea-de-tiempo`
**Creada**: 2026-11-01
**Estado**: Especificada y clarificada

---

## Clarificaciones

### Sesión 2026-11-01

- **Q1: ¿Qué define el estado del juego en un instante $t$ (§3.6)?**
  - **Decisión**: Es el estado de la partida después de ejecutar todos los eventos con tiempo virtual menor o igual que $t$. Si a $t$ le corresponde una decisión del jugador, es el estado justo antes de tomar dicha decisión.
  - Si ocurren múltiples eventos en el mismo instante $t$, la consulta muestra el estado resultante tras ejecutar todos ellos.

- **Q2: ¿Qué información mínima debe presentarse en una consulta histórica?**
  - **Decisión**:
    1. Reloj virtual actual de la consulta.
    2. Sala del jugador (identificador y nombre).
    3. Vida y estadísticas del jugador (vida actual/máxima, ataque, defensa y velocidad).
    4. Inventario (objetos con sus nombres).
    5. Efectos temporales activos (nombre y duración restante).
    6. Enemigos presentes en la sala del jugador con su vida actual.
    7. Mapa conocido en ese instante (salas exploradas y avistadas).

- **Q3: ¿Cómo interactúan las consultas históricas con la simulación viva y el retroceso?**
  - **Decisión**:
    - Las consultas históricas no consumen tiempo virtual, no se registran como acciones en la bitácora (`partida.log`) y no modifican el estado de la partida en curso ni el historial de retroceso.
    - Intentar consultar un instante $t$ posterior al reloj actual se rechaza con un mensaje de error.
    - Cuando se utiliza un pergamino de retroceso, las acciones revertidas dejan de existir en la línea de tiempo: la línea de tiempo describe la historia de la partida tal como quedó tras el retroceso.

- **Q4: ¿Qué restricciones aplican a los puntos de control y la memoria (§3.6, §5.5)?**
  - **Decisión**:
    - Se permite almacenar copias completas del estado (puntos de control), pero como máximo una cada $K$ acciones del jugador, configurable mediante la bandera CLI `--checkpoint-cada K` (con un valor por defecto justificado empíricamente con mediciones).
    - Fuera de los puntos de control, la memoria solo almacena la información necesaria para reconstruir los cambios. La memoria total debe crecer con la cantidad de cambios ocurridos y puntos de control cada $K$, nunca como el producto de acciones por el tamaño del estado completo.
    - Una consulta histórica no puede requerir aplicar o deshacer cambios de más de $K$ acciones del jugador.

- **Q5: ¿Qué comportamiento tiene la bandera `--replay ... --hasta <t>` (§3.6)?**
  - **Decisión**:
    - Reproduce la bitácora sin instanciar la vista interactiva hasta el instante $t$ e imprime el resumen del estado en ese instante.
    - Si $t$ es posterior al final de la partida, reproduce hasta el final, imprime el estado final e indica explícitamente que la partida concluyó antes del instante solicitado.

- **Q6: ¿Cómo se maneja la persistencia y la compatibilidad con partidas previas (§3.6, §4.10)?**
  - **Decisión**:
    - Guardar y cargar la partida conserva la línea de tiempo completa.
    - Si se intenta cargar un archivo de guardado de la primera parte (formato binario anterior sin línea de tiempo), el programa detecta la incompatibilidad y la rechaza con un error explícito, sin cargarla en silencio.

---

## Historias de usuario

### US-1: Consulta Histórica en Partida Interactiva (Prioridad P1)

Como jugador o evaluador, quiero consultar el estado de la partida en cualquier instante $t$ o antes de cualquier acción $\#k$, para inspeccionar la evolución del juego sin alterar mi partida ni consumir tiempo virtual.

**Escenarios de aceptación**:

1. **Consulta válida por tiempo (`historia <t>`)**:
   - Dado un instante $t \le \text{reloj actual}$, ejecutar `historia <t>` muestra el reloj, la sala, las estadísticas del jugador, el inventario, los efectos activos, los enemigos de la sala y el mapa conocido correspondientes a ese instante.
2. **Eventos simultáneos en $t$**:
   - Dados múltiples eventos ocurridos en el mismo instante $t$, `historia <t>` refleja el estado tras la ejecución de todos ellos.
3. **Consulta por número de acción (`historia #k`)**:
   - Dado $1 \le k \le \text{acciones realizadas}$, `historia #k` muestra el estado justo antes de que el jugador ejecutara la acción número $k$.
4. **Rechazo de consulta futura**:
   - Si se ejecuta `historia <t>` con $t > \text{reloj actual}$, o `historia #k` con $k > \text{acciones realizadas}$, el comando se rechaza con un mensaje de error y no modifica el estado.
5. **No interferencia con la partida**:
   - Ejecutar consultas históricas no añade entradas a `partida.log`, no gasta unidades de reloj virtual y no altera el diario de retroceso.

---

### US-2: Interacción con el Pergamino de Retroceso (Prioridad P1)

Como jugador, quiero que la línea de tiempo refleje fielmente la historia canónica tras usar un pergamino de retroceso, descartando las acciones que fueron anuladas.

**Escenarios de aceptación**:

1. **Recorte de historia tras retroceso**:
   - El jugador realiza acciones hasta el instante $t_2$ y luego usa un pergamino de retroceso que lo devuelve a $t_1$.
   - Consultar la historia en $t_1$ muestra el estado canónico actual.
   - Consultar la historia en un tiempo posterior a $t_1$ que correspondía a una acción revertida es rechazado como tiempo futuro.
2. **Eficiencia en el recorte**:
   - El recorte de la línea de tiempo ante un retroceso no recorre toda la historia acumulada de la partida.

---

### US-3: Reproducción no Interactiva con Límite de Tiempo (Prioridad P1)

Como evaluador o herramienta de análisis, quiero reproducir una bitácora hasta un tiempo determinado sin abrir la vista, para inspeccionar automáticamente el estado del juego en dicho instante.

**Escenarios de aceptación**:

1. **Replay hasta instante $t$**:
   - Ejecutar `python main.py --replay partida.log --hasta <t>` reproduce las acciones hasta $t$ y emite el resumen del estado histórico en la salida estándar.
2. **Replay con $t$ posterior al fin de partida**:
   - Si $t$ supera el tiempo en que la partida terminó, se emite el estado final acompañado de un mensaje indicando que la partida concluyó antes de $t$.

---

### US-4: Puntos de Control y Persistencia (Prioridad P2)

Como administrador del sistema, quiero que la memoria de la partida esté acotada mediante puntos de control configurables y que los archivos binarios preserven la línea de tiempo o alerten si son incompatibles.

**Escenarios de aceptación**:

1. **Acotamiento de puntos de control**:
   - No se genera más de un punto de control completo cada $K$ acciones del jugador, configurable con `--checkpoint-cada K`.
2. **Conservación de la línea de tiempo al guardar y cargar**:
   - Guardar una partida en archivo binario y recargarla permite continuar realizando consultas históricas de acciones anteriores al guardado.
3. **Detección de incompatibilidad de versiones previas**:
   - Si se intenta cargar un archivo binario generado con la versión de la primera parte, el cargador reporta explícitamente la incompatibilidad y detiene la carga.

---

## Requisitos funcionales

- **FR-029**: El sistema implementa la línea de tiempo registrando los cambios ocurridos en cada acción del jugador.
- **FR-030**: El comando interactivo `historia <t>` presenta el estado del juego tras procesar todos los eventos hasta el instante $t$.
- **FR-031**: El comando interactivo `historia #k` presenta el estado del juego justo antes de ejecutar la acción número $k$ del jugador.
- **FR-032**: Las consultas históricas no consumen tiempo virtual, no se escriben en `partida.log` y no afectan el diario de retroceso.
- **FR-033**: Las consultas a instantes posteriores al reloj actual o a números de acción superiores a los ejecutados se rechazan con un mensaje descriptivo.
- **FR-034**: El pergamino de retroceso recorta la línea de tiempo eliminando las acciones anuladas sin recorrer toda la historia previa.
- **FR-035**: La bandera CLI `--replay <log> --hasta <t>` reproduce la partida hasta el instante $t$ y emite el resumen del estado sin instanciar la vista interactiva. Si $t$ supera el final de la partida, emite el estado final informando la terminación anticipada.
- **FR-036**: El sistema almacena puntos de control completos como máximo una vez cada $K$ acciones del jugador, configurable mediante la bandera CLI `--checkpoint-cada K`.
- **FR-037**: La reconstrucción del estado en cualquier consulta histórica requiere aplicar o revertir cambios de no más de $K$ acciones del jugador.
- **FR-038**: El guardado binario persiste la línea de tiempo y rechaza explícitamente archivos de versiones anteriores incompatibles.

---

## Requisitos de rendimiento

- **PR-007**: La consulta de historia toma menos de 50 ms sobre una partida de al menos 5 000 acciones del jugador utilizando el valor de $K$ por defecto (§6.1).
- **PR-008**: El consumo de memoria de la línea de tiempo crece proporcionalmente a la cantidad de cambios ocurridos más un punto de control cada $K$ acciones, y no como el producto de acciones por el tamaño del estado completo (§5.5).
