# CRIPTA — Juego de mazmorra dirigido por eventos

Proyecto 1 de **Estructuras de Datos II** (II Ciclo 2026).
Diseño, implementación y evaluación de estructuras de datos propias en un juego de mazmorra
por eventos, con contenido descargado de un servicio web.

> Las reglas del juego están especificadas por el enunciado; las decisiones de estructuras
> de datos son nuestras y están justificadas en `Documento_de_Decisiones`.

## Integrantes

| Integrante | Responsabilidad principal |
|---|---|
| Diego Barquero | Cliente HTTP/offline, presupuesto de red, precarga, bitácora y `--replay`, tabla de puntajes |
| Keilor Baltodano | Caché de fichas, ordenamientos, bench |
| Jorge | Inventario, historial reversible (pergaminos de retroceso) |
| Justin | Motor de eventos, agenda, rastro, bitácora en pantalla |
| Jurnier | Efectos, guardado binario |

## Requisitos

- **Python 3.11 o superior** (probado con 3.14).
- Dependencia externa: **`requests`** (solo para el modo en línea).
- Todo lo demás (estructuras de datos, ordenamientos, formato binario) es código propio y
  solo usa la biblioteca estándar (`struct`, `json`, `argparse`, etc.).

## Instalación (entorno limpio)

```bash
git clone <URL-DEL-REPOSITORIO>
cd cripta-juego-dungeon

# Con uv
uv venv
uv pip install -r requirements.txt

# O con venv + pip
python -m venv .venv
# Windows:  .venv\Scripts\activate        Linux/macOS:  source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` debe contener:

```
requests
pytest
```

## Uso

Todos los comandos se ejecutan desde la raíz del proyecto
(con `uv run main.py ...` o `python main.py ...`).

| Comando | Qué hace |
|---|---|
| `python main.py` | Lista las criptas del servicio, pide el nombre e inicia una partida interactiva |
| `python main.py --cripta cripta-01 --nombre Ana --semilla 7` | Inicia directamente una cripta con semilla y nombre fijos |
| `python main.py --offline <carpeta>` | Usa respuestas guardadas en disco en lugar de HTTP |
| `python main.py --replay partida.log` | Reproduce una partida completa, sin interacción y sin vista |
| `python main.py --bench` | Ejecuta los benchmarks por subsistema |
| `python main.py --cache-size 10` | Cambia el tope de fichas de catálogo en memoria (por defecto 25) |
| `python main.py --log mi_partida.log` | Elige el archivo de bitácora de la partida (por defecto `partida.log`) |

Banderas disponibles: `--bench`, `--offline DIR`, `--replay LOG`, `--cache-size N`,
`--cripta ID`, `--semilla N`, `--nombre NOMBRE`, `--log ARCHIVO`.

> **Importante:** cada partida nueva **sobrescribe** el archivo de bitácora indicado con `--log`.
> Copie `partida.log` con otro nombre antes de jugar de nuevo si quiere conservarlo.

### Comandos dentro del juego

| Comando | Acción |
|---|---|
| `n` / `s` / `e` / `o` | Moverse al norte, sur, este u oeste |
| `abrir <n\|s\|e\|o>` | Abrir una puerta cerrada con la llave correspondiente |
| `atacar [k]` | Atacar al enemigo número *k* de la sala (por defecto el 1) |
| `esperar` (o `z`) | Pasar tiempo sin hacer nada |
| `recoger [k]` | Recoger el objeto número *k* del suelo (por defecto el 1) |
| `soltar` | Soltar el objeto que se está viendo en el inventario |
| `equipar` | Equipar el objeto actual (arma o armadura) |
| `usar` | Usar el objeto actual (poción, antídoto, antorcha, pergamino) |
| `sig` / `ant` | Recorrer el inventario hacia adelante / atrás |
| `inv` | Mostrar el inventario |
| `ordenar <peso\|valor\|nombre>` | Vista ordenada del inventario (no altera el orden real) |
| `retroceso` (o `pergamino`) | Usar un pergamino de retroceso |
| `guardar <archivo>` / `cargar <archivo>` | Guardado y carga de la partida (ver *Estado*) |
| `ayuda` | Mostrar la ayuda |
| `salir` (o `q`) | Terminar la sesión de forma controlada |

`recoger` y `atacar` reciben el **número** que aparece en pantalla, no el nombre.
`equipar`, `usar` y `soltar` actúan sobre el objeto que aparece como *«viendo»*; use `sig` y
`ant` para cambiarlo. Al terminar la partida se muestra el resumen y el reporte de red.

## Modo sin conexión (`--offline`)

`--offline <carpeta>` hace que el programa lea las respuestas desde disco usando el **mismo
contrato lógico** que el cliente HTTP (`adapters/clienteCripta.py`); el modelo no sabe de dónde
vienen los datos. Estas lecturas **no cuentan** como solicitudes de red.

La carpeta debe contener los archivos del paquete publicado por el curso. Los nombres que
`adapters/clienteOffline.py` espera son, entre otros: `criptas.json`, `<id>_general.json`,
`<id>_contenido.json` y `catalogo.json`.

> Si el paquete oficial usa otros nombres, ajuste `clienteOffline.py`.

## Replay y bitácora

Cada acción del jugador que cambia el estado se anexa a un archivo de texto:

```
HEADER|<id_cripta>|<version_cripta>|<version_catalogo>|<semilla>
ACCION|<comando>
ACCION|<comando>
...
```

`--replay` reconstruye la partida con la misma cripta, la misma semilla y las mismas acciones;
el resultado final (reloj, acciones, derrotados, estado) coincide con la partida original.
Si la versión de la cripta o del catálogo del log ya no coincide con la disponible, el programa
**se detiene y lo informa** en lugar de reproducir contra datos distintos (§4.11).

## Presupuesto de red y caché

- Cada cripta declara `presupuesto_solicitudes`; el valor se lee de los datos generales y
  **no está escrito en el código**.
- Se usan lotes (hasta 10 salas por solicitud de contenido, hasta 10 ids por solicitud de
  catálogo) y precarga anticipada por búsqueda en anchura sobre el esqueleto.
- Las fichas del catálogo se guardan en `.cache_cripta/cat_<version_catalogo>/<id>.json` y
  sobreviven al cierre del programa; si cambia la versión del catálogo se descartan.
- Al terminar la partida se imprime: solicitudes realizadas, presupuesto, aciertos y fallos
  de caché.

## Archivos que genera el programa

| Archivo / carpeta | Contenido |
|---|---|
| `partida.log` (o el de `--log`) | Bitácora de la partida para `--replay` |
| `puntajes_locales.json` | Tabla de puntajes (nombre, cripta y versión, acciones, derrotados, tiempo final) |
| `.cache_cripta/` | Caché persistente de fichas del catálogo |
| `*.sav` | Archivos de guardado binario (cuando se usa `guardar`) |

Estos archivos están en `.gitignore`.

## Pruebas

```bash
python -m pytest
```

Algunos archivos de `tests/` no siguen el patrón `test_*.py` y pytest no los recoge por
defecto; para correrlos explícitamente:

```bash
python -m pytest tests/TestMotor.py tests/PruebaRetroceso.py tests/pruebaEfectos.py tests/pruebaGuardado.py
```

`TestMotor.py` incluye la prueba del requisito de procesamiento (§5.2): un ciclo completo de
eventos entre dos decisiones del jugador debe tomar menos de 20 ms con cientos de enemigos activos.

## Benchmarks (`--bench`)

```bash
python main.py --bench
```

Ejecuta cargas sintéticas y reporta tiempos por subsistema: ordenamientos, caché, guardado
binario frente a JSON y efectos. Los resultados de referencia están en `resultados_bench.txt`
y se analizan en el Documento de Decisiones. Los tiempos dependen del equipo; los conteos
(comparaciones, solicitudes) no.

## Arquitectura (MVC + adaptadores)

```
main.py                  Punto de entrada y banderas
model/                   Reglas del juego y estructuras de datos (sin red, disco ni interfaz)
  Juego.py               Modelo: reloj virtual, combate, puertas, trampas, retroceso
  Agenda.py              Agenda de eventos (montículo con cancelación y desempate por secuencia)
  Diario.py              Historial reversible (máx. 5 acciones, sin copias del estado)
  Inventario.py          Lista doblemente enlazada con cursor
  Rastro.py, Bitacora.py Rastro del jugador y bitácora circular de 20 mensajes
  efectos.py             Veneno, regeneración, antorcha, velocidad
  cache_estructuras.py   Caché de fichas y registro de salas
  ordenamiento/          Inserción, mezcla, selección y selector automático
controller/              ControladorJuego.py: traduce texto a acciones y coordina el flujo
view/                    Consola.py: vista de consola
adapters/                Red y disco detrás de interfaces
  clienteCripta.py       Interfaz del cliente
  clienteHttp.py         Cliente HTTP (encabezado X-Cripta-Client-Id, manejo de 429)
  clienteOffline.py      Cliente que lee desde disco
  estrategiaRed.py       Precarga por lotes y reporte de red
  ProveedorRed.py        Une cliente + caché para el modelo
  bitacoraReplay.py      Bitácora de partida y validación de versiones
  tablaPuntajes.py       Tabla de puntajes local
  guardadoBinario.py     Formato binario propio (índice por sala, versión de formato)
bench/                   Benchmarks
tests/                   Pruebas
```

Los modos `--replay` y `--bench` se ejecutan **sin instanciar la vista**. El modelo no conoce
HTTP ni archivos: recibe sus datos a través de la interfaz `ProveedorDatos`.

## Reglas del juego, en breve

- El tiempo es un **reloj virtual entero**; no hay rondas. Cada actor tiene un
  `tiempo_siguiente` y el orden de ejecución es (tiempo, número de secuencia).
- Intervalo de una acción: `max(1, costo * 100 // velocidad)`.
- Daño: `max(1, ataque + randint(0, 4) - defensa)`, con un `random.Random(semilla)` propio.
- Los enemigos se activan cuando el jugador entra a su sala. Hay tres comportamientos:
  guardián, errante y rastreador (este sigue el rastro fresco, de menos de 400 unidades).
- El jugador **gana** al entrar a la sala de salida tras abrir con la llave la puerta que
  da acceso a ella, y **pierde** si su vida llega a 0.
- El pergamino de retroceso revierte la última acción del jugador y todo lo ocurrido después
  (máximo 5 acciones hacia atrás); no consume tiempo virtual.

## Restricciones de implementación

Las estructuras de datos usadas para resolver los problemas del §4 son propias: está
prohibido sustituirlas por equivalentes de bibliotecas, usar `dict` como índice o caché,
y `list.sort()` / `sorted()` en los ordenamientos evaluados. Se permite `list` como
almacenamiento contiguo, y `struct`, `json`, `requests` y `argparse`.

## Documentación del proyecto

- `Documento_de_Decisiones` — una sección por cada problema del §4 con problema,
  alternativas, decisión, complejidad, evidencia empírica y límites conocidos.
- `PROMPTS_LLM` — bitácora de uso de modelos de lenguaje.
- `resultados_bench.txt` — salida de referencia de `--bench`.

## Estado y limitaciones conocidas

> Actualice esta sección antes de cada entrega.

- [ ] `guardar` / `cargar` desde la interfaz: el formato binario por sala existe
  (`adapters/guardadoBinario.py`), falta conectar el guardado del estado completo.
- [ ] El veneno aún no se origina en trampas del contenido.
- [ ] Persistencia de esqueleto y contenido de salas por versión de cripta.
- [ ] Verificar el requisito de 20 ms (§5.2) en el equipo de evaluación.
