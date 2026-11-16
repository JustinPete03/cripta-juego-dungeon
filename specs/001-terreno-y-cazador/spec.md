# Especificación: Terreno y Cazador

**Carpeta**: `specs/001-terreno-y-cazador`
**Creada**: 2026-11-01
**Estado**: Especificada y clarificada

---

## Clarificaciones

### Sesión 2026-11-01

- **Q1: ¿El campo `costo` de una salida aplica en ambos sentidos?**
  - **Decisión**: Sí. §3.1 lo dice explícitamente: «El costo es el mismo en ambos sentidos.»
  - **Impacto**: La `Salida` almacena el costo; la salida inversa comparte el mismo valor.

- **Q2: ¿Qué pasa si una salida no declara el campo `costo`?**
  - **Decisión**: Su costo es 100 (§3.1: «Si no lo declara, su costo es 100»).
  - **Impacto**: `_construirSalas` usa `info.get("costo", 100)`.

- **Q3: ¿El costo de moverse afecta también a errantes y rastreadores?**
  - **Decisión**: Sí. §3.1: «La regla aplica a todos los actores.» Errantes y rastreadores conservan su comportamiento pero el intervalo de su movimiento depende del costo de la salida atravesada.
  - **Impacto**: `_moverEnemigo` y `_programarEnemigo` deben usar el costo de la salida, no el costo fijo 100.

- **Q4: ¿El cazador abre puertas cerradas?**
  - **Decisión**: No. §3.2: «No abre puertas cerradas.» Solo considera salidas abiertas para su ruta.

- **Q5: ¿Cómo se desempata cuando hay múltiples vecinas que inician rutas de igual costo mínimo?**
  - **Decisión**: Se mueve a la vecina de menor id de sala (§3.2: «el cazador se mueve a la de menor id»). Este criterio aplica sin importar el algoritmo de cálculo.

- **Q6: ¿Cuándo espera el cazador?**
  - **Decisión**: Espera con costo 100 cuando (1) no existe ruta abierta hacia el jugador, o (2) el costo mínimo de la ruta excede su `rango` (§3.2).

- **Q7: ¿El cazador recalcula la ruta en cada turno?**
  - **Decisión**: La decisión debe ser idéntica a calcular desde cero en cada turno (§3.2 «equivalencia observable»). Puede reutilizar cálculos anteriores siempre que el resultado no cambie.

- **Q8: ¿El costo de `atacar`, `esperar` y demás acciones cambia con el terreno?**
  - **Decisión**: No. §3.1: «El costo de atacar, esperar y las demás acciones no cambia.» Solo moverse usa el costo de la salida.

---

## Historias de usuario

### US-1: Movimiento con costo de salida (Prioridad P1)

Como jugador, quiero que moverme por una salida cueste lo que la salida indica, para que el terreno tenga impacto táctico en la partida.

**Escenarios de aceptación**:

1. **Costo explícito.** Dada una salida con `costo: 250` y un actor con velocidad 100, cuando el actor la atraviesa, entonces el intervalo es `max(1, 250 * 100 // 100) = 250`.

2. **Costo por defecto.** Dada una salida sin campo `costo`, cuando un actor la atraviesa, entonces el intervalo es `max(1, 100 * 100 // velocidad)`, idéntico al comportamiento de la Parte 1.

3. **Velocidad alta y costo bajo.** Dado un actor con velocidad 200 y una salida con `costo: 1`, el intervalo es `max(1, 1 * 100 // 200) = max(1, 0) = 1`.

4. **Errantes y rastreadores con costo.** Un errante que cruza una salida de costo 250 tarda `max(1, 250 * 100 // velocidad)`, no `max(1, 100 * 100 // velocidad)`.

5. **Cambio de velocidad durante movimiento costoso.** Cuando cambia la velocidad de un actor que tiene programada una acción de movimiento con costo de salida, el tiempo restante se escala según P1 §2.3.

### US-2: Comportamiento del cazador (Prioridad P1)

Como diseñador, quiero que el cazador persiga al jugador por la ruta más barata dentro de su rango, para ofrecer un enemigo inteligente.

**Escenarios de aceptación**:

1. **Cazador comparte sala con el jugador.** Dado un cazador en la misma sala que el jugador, cuando llega su turno, entonces ataca (P1 §2.8).

2. **Cazador sin ruta.** Dado un cazador sin ruta abierta hacia el jugador, cuando llega su turno, entonces espera con costo 100.

3. **Cazador fuera de rango.** Dado un cazador cuyo costo mínimo `d` al jugador es mayor que su `rango`, cuando llega su turno, espera con costo 100.

4. **Cazador dentro de rango.** Dado un cazador con `d ≤ rango`, cuando llega su turno, se mueve un paso por la ruta de costo mínimo. El costo de la acción es el `costo` de la salida que atraviesa.

5. **Desempate por menor id.** Dadas dos vecinas `v1` (id=5) y `v2` (id=3) que inician rutas de igual costo mínimo, el cazador se mueve a `v2` (id=3).

6. **Ruta de menos salas vs. menor costo.** Existe una ruta de 2 salas con costo total 500 y otra de 4 salas con costo total 300. El cazador sigue la de costo 300.

7. **Puerta se cierra entre turnos.** Una puerta de la ruta del cazador se cierra antes de su siguiente turno. En ese turno, el cazador decide como si calculara desde cero y elige otra ruta o espera.

8. **Lectura de la ficha del cazador.** La ficha de catálogo incluye `"comportamiento": "cazador"` y `"rango": N`. El modelo lee estos campos al crear al enemigo.

---

## Requisitos funcionales

- **FR-001**: Cada salida del esqueleto tiene un campo `costo` (entero ≥ 1). Si el campo no está presente, el costo es 100.
- **FR-002**: El intervalo de la acción de moverse es `max(1, costo_salida * 100 // velocidad)`.
- **FR-003**: El costo de `atacar`, `esperar`, `recoger`, `usar`, `equipar` y `soltar` no cambia.
- **FR-004**: Errantes y rastreadores usan el costo de la salida que atraviesan para calcular su intervalo de movimiento.
- **FR-005**: El cazador, en su turno: si comparte sala con el jugador, ataca; si no, calcula el costo mínimo `d` desde su sala hasta el jugador usando solo salidas abiertas; si no hay ruta o `d > rango`, espera (costo 100); si `d ≤ rango`, se mueve un paso hacia la vecina de menor id entre las que inician una ruta óptima.
- **FR-006**: El cazador conoce el esqueleto completo y el estado actual de las puertas. No le afecta la niebla de guerra. No abre puertas cerradas.
- **FR-007**: La decisión del cazador es idéntica a la que daría un cálculo desde cero. Puede reutilizar cálculos si el resultado no cambia.
- **FR-008**: El desempate del cazador es: entre vecinas con `costo(u,v) + dist(v, jugador) = d`, elige la de menor id de sala.
- **FR-009**: La vista muestra los costos de las salidas de la sala actual y distingue a los cazadores de los demás enemigos.
- **FR-010**: La ficha del cazador en el catálogo incluye `"comportamiento": "cazador"` y `"rango"` (entero en unidades de costo).

---

## Requisitos de rendimiento

- **PR-001**: El ciclo de eventos entre dos decisiones del jugador no supera 20 ms con decenas de cazadores activos (§6.1).
- **PR-002**: La decisión de un cazador de rango pequeño no debe costar proporcionalmente al tamaño de la cripta, sino a la región dentro de su rango (§5.1).
