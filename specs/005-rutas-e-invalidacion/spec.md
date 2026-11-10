# Especificación: Rutas ponderadas e invalidación de rutas

**Carpeta**: `specs/005-rutas-e-invalidacion`
**Creada**: 2026-11-08
**Responsable**: Keilor Baltodano
**Estado**: Especificada y clarificada
**Enunciado**: §3.2 (conocimiento y equivalencia observable), §3.4 (desempate de «ir a»), §5.1, §5.2, §6.1, §6.3
**Relación con otras especificaciones**:
- `001-terreno-y-cazador` define **qué hace** el cazador en su turno (FR-005 a FR-008, FR-010). Esta especificación no repite esas reglas.
- `002-niebla-y-viaje` define **qué conoce** el jugador y **cuándo se detiene** un viaje. Esta especificación solo define cómo se elige el paso del viaje.

---

## Alcance

Por acuerdo del grupo (2026-11-08), esta especificación es dueña de:

1. Que la decisión del cazador siga siendo la de un cálculo desde cero **cuando el mapa cambia entre sus turnos** (§3.2, §5.2). Incluye el caso del Apéndice B «una puerta de la ruta del cazador se cierra entre dos de sus turnos», que deja de estar en 001 (en 001 se reemplaza por una referencia a esta especificación).
2. El **costo** de calcular rutas: rango pequeño frente a cripta grande, y decenas de cazadores (§5.1, §6.1).
3. El **criterio común** de elección del paso para el cazador y para «ir a»: el grupo decidió que ambos comparten una sola búsqueda de rutas (§5.3, punto 4).
4. Las **mediciones** de rutas de `--bench` (§6.3).

Los casos del Apéndice B «ruta de menos salas pero mayor costo» y «dos vecinas empatadas» siguen siendo de 001, porque son reglas del cazador.

---

## Clarificaciones

### Sesión 2026-11-08

- **Q1: ¿Qué es «la región que queda dentro de su rango» (§5.1)?**
  - **Decisión**: Las salas cuyo costo mínimo hasta la sala del jugador, usando solo salidas abiertas, es menor o igual que el rango.
  - **Impacto**: PR-010 se mide contando las salas examinadas para decidir, y comparando el tiempo de decisión en criptas de tamaños distintos con la misma región alrededor del jugador.

- **Q2: Si hay cazadores con rangos distintos, ¿el costo debe depender del rango de cada uno o puede depender del mayor rango activo?**
  - **Decisión**: Puede depender del **mayor rango entre los cazadores activos**. Todos persiguen al mismo jugador, así que el cálculo de un ciclo se comparte entre todos; un cálculo por cazador repetiría trabajo (pregunta 1 de §8).
  - **Impacto**: PR-010 se cumple respecto al mayor rango activo. `--bench` compara esta decisión contra un cálculo individual por cazador (PR-012) para mostrar bajo qué condiciones conviene cada uno.

- **Q3: ¿Cuántos cazadores son «decenas» y cuál es la cripta de referencia?**
  - **Decisión**: Se mide con 30 y 60 cazadores activos. Mientras no se publique la cripta de referencia (§6.1), se usan la cripta de demostración más grande y criptas sintéticas de 1000 salas. Cuando se publique, se repite la medición con ella.

- **Q4: Si dos salidas de una misma sala llevan a la misma vecina, ¿cuál se usa?**
  - **Decisión**: El desempate de §3.2 es entre **vecinas** (menor id). Hacia la vecina elegida se usa la salida abierta de menor costo; si dos salidas abiertas hacia ella cuestan lo mismo, se usa la primera en el orden de direcciones del juego (N, S, E, O).

- **Q5: ¿Qué pasa si la ficha de un cazador no declara `rango`?**
  - **Decisión**: Fuera del alcance de esta especificación: la lectura de la ficha es de 001 (FR-010). Aquí se asume que todo cazador tiene un rango entero.

---

## Historias de usuario

### US-1: Persecución correcta en un mapa que cambia (Prioridad P1)

Como jugador, quiero que los cazadores tomen siempre la decisión que daría un cálculo desde cero, aunque entre sus turnos cambien las puertas o yo me mueva, para que su comportamiento sea predecible y justo.

**Escenarios de aceptación**:

1. **Una puerta de la ruta se cierra entre dos turnos** (Apéndice B). En el turno siguiente, el cazador decide como si calculara desde cero: toma otra ruta, o espera con costo 100 si ya no hay ruta o si la nueva supera su rango. [FR-039, FR-040]
2. **Se cierra una puerta lejos de cualquier ruta mínima.** Ninguna decisión de ningún cazador cambia respecto a la que habría tomado sin ese cierre. [FR-039, FR-041]
3. **Se abre una puerta que crea un atajo.** En el turno siguiente, el cazador usa la nueva ruta si es más barata. [FR-039, FR-040]
4. **Se abre una puerta que no acorta ninguna ruta.** Ninguna decisión cambia. [FR-039, FR-041]
5. **El jugador se mueve.** En su siguiente turno, cada cazador decide hacia la sala nueva del jugador. [FR-040]
6. **Un pergamino revierte el movimiento del jugador.** En su siguiente turno, cada cazador decide hacia la sala restaurada, no hacia la revertida. [FR-040]
7. **Eventos que no cambian rutas.** Otro actor cambia de sala, cambia la velocidad de un cazador o muere un cazador. Las decisiones de los demás cazadores coinciden con un cálculo desde cero. [FR-040]
8. **Se carga una partida guardada.** La primera decisión de cada cazador después de cargar coincide con un cálculo desde cero. [FR-040]
9. **Se activa un cazador de rango mayor que todos los activos.** Su decisión coincide con un cálculo desde cero. [FR-040, FR-043]
10. **Muchas rutas de igual costo.** En una cuadrícula donde todas las salidas cuestan lo mismo existen muchas rutas mínimas. En cada turno, el cazador va a la vecina de menor id entre las que inician una ruta mínima, sin importar el orden en que se examinen las salas. [FR-042]
11. **Rango exactamente igual al costo.** Si el costo mínimo hasta el jugador es igual al rango, el cazador se mueve. [FR-039]
12. **Simulación larga con puertas que cambian.** En una partida simulada de cientos de turnos (con semilla) donde se abren y cierran puertas al azar, cada decisión de cazador coincide con la de un cálculo desde cero. [FR-039, FR-040, FR-041]

### US-2: El costo de decidir depende del rango, no del tamaño de la cripta (Prioridad P1)

Como diseñador, quiero que muchos cazadores puedan perseguir al jugador sin que el juego se vuelva lento, y que un cazador de rango pequeño cueste lo mismo en una cripta pequeña que en una enorme.

**Escenarios de aceptación**:

1. **Misma región, criptas de distinto tamaño.** Un cazador de rango pequeño, cerca del jugador, en criptas de unas 100, 1000 y 5000 salas (en el bench, cuadrículas de 10×10, 32×32 y 71×71: 100, 1024 y 5041 salas). El tiempo de su decisión y la cantidad de salas examinadas son aproximadamente iguales en las tres. [PR-010]
2. **Ruta más cara que el rango.** El cazador espera con costo 100, y decidirlo no requiere examinar salas fuera de la región del mayor rango activo. [PR-010]
3. **Decenas de cazadores.** Con 30 y con 60 cazadores activos persiguiendo al mismo jugador, ningún ciclo entre dos decisiones del jugador supera 20 ms. [PR-009]

### US-3: El viaje automático elige el paso con el mismo criterio (Prioridad P2)

Como jugador, quiero que «ir a» elija su paso igual que el cazador, para que el viaje sea predecible.

**Escenarios de aceptación**:

1. **Dos vecinas exploradas empatadas.** Dos vecinas exploradas inician rutas conocidas de costo mínimo hacia el destino. El viaje da el primer paso hacia la de menor id. [FR-044]
2. **Menos salas pero mayor costo en el mapa conocido.** Entre una ruta conocida de pocas salas y costo alto y otra de más salas y costo menor, el viaje sigue la de menor costo. [FR-044]

### US-4: Evidencia medible con `--bench` (Prioridad P2)

Como evaluador, quiero que `--bench` muestre con datos las decisiones de rutas, para poder comprobar cada afirmación de rendimiento.

**Escenarios de aceptación**:

1. **Comparaciones de §6.3.** `--bench` reporta: un cazador frente a muchos, rango pequeño frente a grande, cálculo compartido frente a individual, y reutilización frente a recálculo con puertas estables e inestables. [PR-011, PR-012]
2. **Ciclo con cazadores activos.** El bench del ciclo de eventos informa cuántas decisiones de cazador ocurrieron por ciclo; si son cero, la medición falla. [PR-013]
3. **Alternativas equivalentes.** Antes de comparar tiempos, el bench comprueba que las alternativas producen las mismas decisiones; si difieren, la medición falla. [PR-013]
4. **Determinismo.** Dos ejecuciones con la misma semilla generan las mismas criptas sintéticas y las mismas decisiones. [PR-011]

---

## Requisitos funcionales

- **FR-039**: En cada turno, la decisión de un cazador es idéntica a la que se obtendría calculando desde cero en ese instante, con las salidas abiertas en ese instante y la sala actual del jugador (refuerza FR-007 de 001).
- **FR-040**: Entre dos turnos de un cazador pueden ocurrir: aperturas y cierres de puertas (por el jugador o automáticos), movimientos del jugador, cambios de sala de otros actores, cambios de velocidad, activación o muerte de cazadores, uso del pergamino de retroceso y carga de una partida. Después de cualquiera de ellos se cumple FR-039.
- **FR-041**: Un cálculo de rutas anterior solo puede reutilizarse si se puede demostrar que el evento ocurrido no cambia la respuesta. Si no se puede demostrar, se recalcula.
- **FR-042**: El desempate por menor id (FR-008 de 001) se cumple siempre, incluso cuando existen muchas rutas de igual costo, sin depender del orden en que se examinen las salas. Si varias salidas llevan a la vecina elegida, se aplica la decisión de Q4.
- **FR-043**: Las rutas del cazador usan únicamente salidas abiertas en el instante de la decisión, y su cálculo puede limitarse al mayor rango entre los cazadores activos (Q2). El costo de una salida es el mismo en ambos sentidos (§3.1).
- **FR-044**: «ir a» elige su paso con el mismo criterio que el cazador (ruta de costo mínimo; primer paso hacia la vecina de menor id), aplicado únicamente sobre el conocimiento del jugador que define 002 (§3.4).

---

## Requisitos de rendimiento

- **PR-009**: Con 30 y con 60 cazadores activos, el peor ciclo de eventos entre dos decisiones del jugador no supera 20 ms, sin red ni renderizado (§6.1, Q3).
- **PR-010**: El costo de las decisiones de los cazadores crece con la región que queda dentro del mayor rango activo y no con el tamaño total de la cripta (§5.1, Q1, Q2).
- **PR-011**: `--bench` incluye las comparaciones de rutas de §6.3 sobre criptas sintéticas deterministas por semilla.
- **PR-012**: `--bench` compara el cálculo compartido contra un cálculo individual por cazador, y la reutilización contra recalcular siempre, con puertas estables y con puertas que cambian en cada ciclo (§5.1, §5.2).
- **PR-013**: Cada medición de rutas verifica que ejercita lo que dice medir (que ocurren decisiones de cazador y que las alternativas comparadas deciden lo mismo) antes de reportar tiempos.

---

## Casos borde

- Cazador y jugador en la misma sala: se aplica la regla de ataque de 001.
- El jugador está en una sala sin salidas abiertas: ningún cazador de otra sala tiene ruta y todos esperan con costo 100.
- Varios cazadores en la misma sala: cada uno llega a la misma decisión.
- No hay cazadores activos: no se calcula ninguna ruta de cazador.
- La partida termina (victoria o muerte): no se toman más decisiones de cazador.

---

## Supuestos

- El esqueleto completo, incluido el costo de cada salida, se descarga al iniciar la cripta (§3.2).
- Las dos salidas que conectan un mismo par de salas comparten una sola puerta y el mismo costo (§3.1).

---

## Trazabilidad con el Apéndice B

| Caso del Apéndice B | Especificación y escenario |
|---|---|
| Ruta de menos salas pero mayor costo frente a ruta de más salas y menor costo | 001, US-2 escenario 6 (y para «ir a», 005 US-3 escenario 2) |
| Dos vecinas inician rutas de costo mínimo | 001, US-2 escenario 5 (y para «ir a», 005 US-3 escenario 1) |
| Una puerta de la ruta del cazador se cierra entre dos de sus turnos | **005, US-1 escenario 1** |
| Cazador sin ruta abierta / ruta más cara que el rango | 001, US-2 escenarios 2 y 3 |
