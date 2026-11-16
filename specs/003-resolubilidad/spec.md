# Especificación: Verificación de Resolubilidad

**Carpeta**: `specs/003-resolubilidad`
**Creada**: 2026-11-01
**Estado**: Especificada y clarificada

---

## Clarificaciones

### Sesión 2026-11-01

- **Q1: ¿Qué define que una cripta sea resoluble?**
  - **Decisión**: Una cripta es resoluble si, partiendo de la sala inicial y bajo los supuestos de verificación (§3.5), el jugador puede obtener la `llave_salida` y llegar a la `sala_salida` a través de una puerta que requiere dicha llave.

- **Q2: ¿Cuáles son los supuestos formales de la verificación (§3.5)?**
  - **Decisión**:
    1. El jugador puede atravesar cualquier salida abierta y cualquier salida cerrada cuya llave ya obtuvo.
    2. Las llaves nunca se consumen (abrir una puerta no gasta la llave).
    3. Todo enemigo puede ser derrotado (no hay bloqueos por combate).
    4. Una llave que suelta un enemigo se considera obtenible en la sala donde ese enemigo inicia.
    5. Las trampas y los cierres automáticos no impiden ganar, pues una puerta puede volver a abrirse con la misma llave.

- **Q3: ¿Qué debe reportarse si la cripta es resoluble?**
  - **Decisión**: Un orden topológico determinista de obtención de llaves, en el que cada llave aparece después de todas las llaves necesarias para alcanzarla.

- **Q4: ¿Qué debe reportarse si la cripta NO es resoluble?**
  - **Decisión**:
    1. Las llaves que no pudieron ser obtenidas.
    2. Las puertas de la frontera bloqueada (puertas cerradas adyacentes a la región alcanzable) con la llave requerida por cada una.
    3. La ubicación exacta (sala / enemigo) donde se encuentra cada una de esas llaves requeridas.
    4. Si existe un ciclo de dependencias (por ejemplo, una llave ubicada detrás de una puerta que solo ella misma abre, directa o indirectamente), el reporte debe señalar explícitamente el ciclo concreto detectado.

- **Q5: ¿Qué comportamiento tienen las banderas `--verificar` y `--forzar`?**
  - **Decisión**:
    - `--verificar <idCripta>`: Ejecuta únicamente la verificación de resolubilidad e imprime el reporte en stdout (con código de salida 0 si es resoluble o 1 si no lo es), sin instanciar ninguna vista interactiva (consola o GUI).
    - `--forzar`: Si la partida normal detecta que la cripta no es resoluble, por defecto NO inicia y muestra el reporte; pero con la bandera `--forzar`, la partida inicia de todos modos tras mostrar la advertencia.

- **Q6: ¿De dónde se obtienen las llaves y cómo afecta al presupuesto de solicitudes?**
  - **Decisión**: Se consultan vía `GET /criptas/<id>/llaves` (§4.2). Esta solicitud cuenta dentro de `presupuesto_solicitudes`. En modo `--offline`, se lee del archivo local sin consumir red.

---

## Historias de usuario

### US-1: Verificación de Resolubilidad y Reporte (Prioridad P1)

Como jugador o evaluador, quiero verificar si una cripta puede ganarse antes de jugarla, para no invertir tiempo en una mazmorra imposible y entender sus dependencias.

**Escenarios de aceptación**:

1. **Cripta resoluble con orden determinista**:
   - Dadas dos ejecuciones independientes sobre la misma cripta con múltiples órdenes válidos, ambas producen idéntico orden determinista de obtención de llaves.
2. **Llave en enemigo**:
   - Una llave está en el campo `suelta` de un enemigo errante: la verificación la ubica en la sala inicial del enemigo.
3. **Cripta no resoluble sin `--forzar`**:
   - Cuando se intenta jugar una cripta no resoluble sin la bandera `--forzar`, la partida no inicia, el programa muestra el reporte detallado y termina de forma controlada.
4. **Cripta no resoluble con `--forzar`**:
   - Cuando se pasa `--forzar`, el programa imprime el reporte de no resolubilidad y permite iniciar la partida.
5. **Detección de ciclo de llave**:
   - La `llave_salida` está detrás de la única puerta que ella misma abre (o en una cadena circular $K_1 \rightarrow K_2 \rightarrow K_1$): la verificación reporta que la cripta no es resoluble y señala el ciclo concreto.
6. **Ejecución no interactiva con `--verificar`**:
   - Ejecutar `python main.py --verificar cripta-01` ejecuta solo la verificación, imprime el reporte y no abre la ventana gráfica ni el bucle de consola.

---

## Requisitos funcionales

- **FR-021**: El cliente HTTP y Offline consultan la ubicación de llaves (`GET /criptas/<id>/llaves`) respetando el presupuesto de red.
- **FR-022**: La verificación determina resolubilidad usando el esqueleto y la lista de llaves bajo los supuestos de §3.5.
- **FR-023**: El algoritmo de verificación se ejecuta de forma incremental con complejidad $O(V + E + K)$, sin reiniciar el recorrido por cada llave obtenida.
- **FR-024**: Si la cripta es resoluble, el resultado incluye un orden determinista de obtención de llaves.
- **FR-025**: Si la cripta no es resoluble, el resultado reporta:
  - Llaves inalcanzables.
  - Puertas de la frontera bloqueada y la llave que requiere cada una.
  - Ubicación de cada llave requerida.
  - Ciclo de dependencia concreto si una llave depende de sí misma directa o indirectamente.
- **FR-026**: La bandera CLI `--verificar <idCripta>` ejecuta únicamente la verificación sin instanciar la vista interactiva.
- **FR-027**: Una cripta no resoluble impide iniciar la partida interactiva a menos que se proporcione la bandera CLI `--forzar`.
- **FR-028**: Si la salida de la cripta requiere `llave_salida`, el programa verifica que se pueda alcanzar la sala de salida a través de una puerta abierta con dicha llave.

---

## Requisitos de rendimiento

- **PR-005**: La verificación de resolubilidad toma menos de 200 ms sobre la cripta publicada más grande (§6.1).
- **PR-006**: El costo total del recorrido crece linealmente con $V + E + K$ (recorrido incremental frente a la alternativa ingenua de repetir el recorrido por llave) (§5.4).
