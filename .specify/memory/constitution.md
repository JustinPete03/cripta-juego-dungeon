# Constitución del Proyecto CRIPTA

## Principios fundamentales

### I. Estructuras de datos propias (sin atajos de biblioteca)

Las estructuras de datos de los problemas evaluados (§5 de Parte I y §5 de Parte II) se implementan a mano. Está **prohibido** usar como índice, caché, conjunto o cola de prioridad en caminos evaluados:

- `dict`, `set`, `frozenset`
- `heapq`, `bisect`
- `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`)
- `networkx`, `graphlib`, `scipy.sparse.csgraph` o cualquier biblioteca de grafos o búsqueda de rutas

Se permite `list` como almacenamiento contiguo, `struct`, `json`, `csv`, `argparse`, `requests`, `random` y el resto de la biblioteca estándar que no resuelva directamente el problema evaluado. Las estructuras propias de la Parte I (`Tabla`, `Conjunto`, `Agenda`, `Inventario`, `Diario`, `cache_estructuras`, `ordenamiento/`) pueden reutilizarse y extenderse.

### II. Determinismo estricto

Misma cripta, misma semilla y mismas acciones producen la misma partida, byte a byte en la salida. El generador aleatorio es un `random.Random(semilla)` propio del modelo. Los desempates se resuelven por regla explícita (menor id, menor tiempo, número de secuencia), nunca por orden de inserción de `dict` o `set`.

### III. Separación MVC

- El **modelo** (`model/`) no conoce HTTP, archivos ni interfaz.
- El **controlador** (`controller/`) traduce comandos a acciones del modelo.
- Las **vistas** (`view/`) leen instantáneas del modelo sin modificarlo.
- Los **adaptadores** (`adapters/`) manejan red, disco y persistencia.
- `--replay` y `--bench` se ejecutan sin instanciar la vista.

### IV. Ningún dato de una cripta concreta en el código

Ni ids de sala, ni ids de entidad, ni cantidad de páginas, ni presupuestos, ni estadísticas codificadas. Las únicas literales de catálogo permitidas están en fuentes de prueba, benchmarks y datos de demostración.

### V. Respeto del presupuesto de solicitudes

`presupuesto_solicitudes` se respeta **antes** de solicitar, no solo se reporta al final. Un movimiento que no puede descargarse se rechaza sin gastar tiempo virtual. En `--offline` el presupuesto no aplica.

### VI. Toda afirmación de rendimiento se respalda con `--bench`

Ninguna decisión de estructura de datos se justifica solo con análisis teórico. `--bench` mide las alternativas consideradas con cargas sintéticas deterministas por semilla y reporta tiempos, conteos y memoria.

### VII. Especificación precede a implementación

Cada capacidad nueva sigue el flujo: `spec.md` → clarificaciones → `plan.md` → `tasks.md` → análisis → implementación. Una especificación que no describe lo que el programa hace, o un programa que hace cosas que ninguna especificación describe, son defectos del mismo tipo.

### VIII. Trazabilidad completa

- Cada requisito funcional tiene un identificador estable (`FR-xxx`).
- Cada caso del Apéndice B del enunciado aparece como escenario de aceptación.
- Cada escenario tiene al menos una prueba automatizada que cita el identificador.
- Cada tarea de `tasks.md` referencia los requisitos que atiende.

### IX. Presupuestos de procesamiento

| Operación | Límite |
|---|---|
| Ciclo de eventos entre dos decisiones del jugador | 20 ms |
| Verificación de resolubilidad | 200 ms |
| Consulta `historia` | 50 ms |
| Cálculo de un paso de `ir a` | 5 ms |

Medidos en el equipo local, sin red ni renderizado, con las condiciones del enunciado (§6.1).

## Pila técnica

- **Lenguaje**: Python 3.11+
- **Dependencias de producción**: `requests`, `pygame-ce`
- **Dependencias de desarrollo**: `pytest`
- **Agente de especificaciones**: Antigravity (Google)
- **Gestión de entorno**: pip / venv

## Gobierno

Esta constitución aplica a las cuatro capacidades de la segunda parte y a cualquier revisión de decisiones de la primera parte. Cualquier cambio requiere una enmienda documentada.

**Versión**: 1.0.0 | **Ratificada**: 2026-11-01
