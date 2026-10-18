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

- **Python 3.11 o superior** (probado con **3.14.0**).
- Dependencias externas: **`requests`** (modo en línea y `--offline`), **`pytest`** (pruebas) y
  **`pygame-ce`** (solo la interfaz gráfica, que es el arranque por defecto; se usa la edición
  comunitaria porque `pygame` clásico no tiene ruedas para Python 3.14).
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

`requirements.txt` del repositorio:

```
requests>=2.31
pytest>=8.0
pygame-ce>=2.5          # para la interfaz grafica, el arranque por defecto
```

## Uso

Todos los comandos se ejecutan desde la raíz del proyecto
(con `uv run main.py ...` o `python main.py ...`).

| Comando | Qué hace |
|---|---|
| `python main.py` | Abre la interfaz gráfica estilo Pokémon con las criptas de demostración locales |
| `python main.py --consola` | Juega en la terminal: lista las criptas del servicio y pide el nombre |
| `python main.py --cripta cripta-01 --nombre Ana --semilla 7` | Inicia directamente una cripta con semilla y nombre fijos |
| `python main.py --offline <carpeta>` | Usa respuestas guardadas en disco en lugar de HTTP |
| `python main.py --offline datos_demo` | Lo mismo, con el paquete publicado en el repositorio |
| `python main.py --replay partida.log` | Reproduce una partida completa, sin interacción y sin vista |
| `python main.py --gui` | Equivale al arranque por defecto (se mantiene por compatibilidad) |
| `python main.py --gui --offline datos_demo` | Interfaz gráfica sobre el paquete sin conexión |
| `python main.py --bench` | Ejecuta los benchmarks por subsistema |
| `python main.py --puntajes` | Muestra la tabla de puntajes locales sin iniciar una partida |
| `python main.py --cache-size 10` | Cambia el tope de fichas de catálogo en memoria (por defecto 25) |
| `python main.py --log mi_partida.log` | Elige el archivo de bitácora de la partida (por defecto `partida.log`) |

Banderas disponibles: `--consola`, `--bench`, `--offline DIR`, `--replay LOG`, `--gui`,
`--puntajes`, `--cache-size N`, `--cripta ID`, `--semilla N`, `--nombre NOMBRE`, `--log ARCHIVO`.

> **Importante:** cada partida nueva **sobrescribe** el archivo de bitácora indicado con `--log`.
> Copie `partida.log` con otro nombre antes de jugar de nuevo si quiere conservarlo.

### Comandos dentro del juego (consola)

El modo texto se abre con `--consola`; sin esa bandera `python main.py` lanza la interfaz gráfica.

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

## Interfaz gráfica (por defecto)

`python main.py` —o `python main.py --gui`, que ya equivale a lo mismo— abre la vista estilo
Pokémon (pygame-ce). Es **otra vista del mismo
MVC**: no toca el modelo ni el controlador, solo lee instantáneas
(`view/presentacion.py`) y despacha acciones por `Controlador.ejecutarAccion`.
Las estructuras de datos, la agenda, el retroceso y el presupuesto de red son los mismos
que en la consola.

| Tecla | Acción |
|---|---|
| flechas | mover el cursor |
| `Z` / Enter | confirmar (avanzar, atacar, usar) |
| `X` / Esc | cancelar, retroceder en los menús |
| `I` | abrir la bolsa (inventario) |
| ratón | clic sobre cualquier opción de menú |

Pantallas: selección de cripta y semilla, sala con el explorador y los enemigos, combate por
turnos con barra de vida, bolsa con detalle del objeto y vistas ordenadas, menú de sistema
(guardar, cargar, bitácora, retroceso, salir) y resumen final. El minimapa, el HUD y la
bitácora de 20 mensajes muestran el mismo estado que `view/Consola.py`.

Sin banderas de datos, la GUI juega contra `adapters/proveedor_demo.py` (cripta generada en
memoria, sin red). Con `--offline DIR` o `--cripta ID` usa los adaptadores de Diego, así que
puede mostrarse sobre el servicio real o sobre el paquete del repositorio. La bitácora de la
partida (`--log`) y la tabla de puntajes se escriben igual que en consola, por lo que una
partida gráfica se puede reproducir después con `--replay`.

## Modo sin conexión (`--offline`)

`--offline <carpeta>` hace que el programa lea las respuestas desde disco usando el **mismo
contrato lógico** que el cliente HTTP (`adapters/clienteCripta.py`); el modelo no sabe de dónde
vienen los datos. Estas lecturas **no cuentan** como solicitudes de red.

El repositorio incluye `datos_demo/` con las cuatro criptas publicadas por el servicio
(`criptas.json`, `catalogo_version.json`, `catalogo.json` y, por cripta,
`<id>_general.json`, `<id>_version.json`, `<id>_salas_p1.json`, `<id>_contenido.json`),
que son exactamente los nombres que espera `adapters/clienteOffline.py`.
Sirve para demostrar `--offline` y `--replay` sin conexión; si el curso publica otro paquete,
copie sus archivos con estos mismos nombres.

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
**se detiene y lo informa** en lugar de reproducir contra datos distintos (sección 4.11).

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
python -m pytest          # recoge también TestMotor.py, PruebaRetroceso.py, pruebaEfectos.py...
```

`pytest.ini` declara los patrones de nombre del proyecto (`Test*.py`, `Prueba*.py`,
`prueba*.py`, `Diario*.py` y `test_*.py`); sin él, pytest ignora en silencio la mitad de las
pruebas porque no siguen la convención `test_*.py`.

`TestMotor.py` incluye la prueba del requisito de procesamiento (sección 5.2): con 600 enemigos
activos, el ciclo de eventos entre dos decisiones del jugador toma **~7 ms de mediana**
(se reporta mediana, p90 y peor; se compara la mediana porque la cola de la distribución son
interrupciones del sistema operativo, no del motor).

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
view/                    Dos vistas del mismo estado, intercambiables
  Consola.py             Vista de consola
  Grafica.py             Vista pygame estilo Pokémon (--gui): escenas, menús, animaciones
  presentacion.py        Instantáneas del modelo para dibujar (no importa pygame)
  sprites.py             Hoja de sprites pixel art (rectángulos sobre una cuadrícula 16x16)
adapters/                Red y disco detrás de interfaces
  clienteCripta.py       Interfaz del cliente
  clienteHttp.py         Cliente HTTP (encabezado X-Cripta-Client-Id, manejo de 429)
  clienteOffline.py      Cliente que lee desde disco
  estrategiaRed.py       Precarga por lotes y reporte de red
  ProveedorRed.py        Une cliente + caché para el modelo
  proveedor_demo.py      Fuente local para la GUI sin red
  bitacoraReplay.py      Bitácora de partida y validación de versiones
  tablaPuntajes.py       Tabla de puntajes local
  guardadoBinario.py     Formato binario propio (índice por sala, versión de formato)
datos_demo/              Paquete sin conexión de las cuatro criptas del servicio
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

Las estructuras de datos usadas para resolver los problemas del sección 4 son propias: está
prohibido sustituirlas por equivalentes de bibliotecas, usar `dict` como índice o caché,
y `list.sort()` / `sorted()` en los ordenamientos evaluados. Se permite `list` como
almacenamiento contiguo, y `struct`, `json`, `requests` y `argparse`.

## Documentación del proyecto

- `Documento_de_Decisiones` — una sección por cada problema del sección 4 con problema,
  alternativas, decisión, complejidad, evidencia empírica y límites conocidos.
- `PROMPTS_LLM` — bitácora de uso de modelos de lenguaje.
- `resultados_bench.txt` — salida de referencia de `--bench`.

## Estado y limitaciones conocidas

> Actualice esta sección antes de cada entrega.

- [x] Todos los modos conectados en `main.py`: consola, `--offline`, `--replay`, `--puntajes`,
  `--bench` e `--gui` usan el mismo modelo, el mismo controlador y los mismos adaptadores.
- [x] Paquete sin conexión publicado en `datos_demo/` (las cuatro criptas del servicio).
- [x] Interfaz gráfica (`view/Grafica.py`) con las mismas 11 interacciones de sección 10.2 que la consola.
- [x] `guardar` / `cargar` conectados a la interfaz. `model/estado.py` expone `capturar` /
  `restaurar` (reloj, posición, inventario, efectos, agenda, semilla y estado del azar) y
  `Modelo.capturarEstado` / `restaurarEstado` los publican; `adapters/guardadoPartida.py` los
  guarda en un contenedor binario propio (`*.sav`, índice al final, payloads zlib+JSON).
  `adapters/guardadoBinario.py` (por sala) queda intacto y sigue sirviendo para su sección.
- [x] El requisito de 20 ms (sección 5.2) verificado en el equipo local (mediana ~7 ms con 600 enemigos).
- [x] El veneno se origina en trampas del contenido: la ficha declara `veneno` (daño por pulso)
  y `model/efectosTrampa.py` (extensión de `efectosJuego`, no lo modifica) lo contagia en
  `alActivarTrampa`. Ejercitado en `datos_demo/catalogo.json` y en la demo gráfica.
- [x] Persistencia de esqueleto y contenido por versión de cripta: el archivo `*.sav` embebe
  `esqueleto` y `contenido` junto a `cripta` (id, versión de cripta y de catálogo, semilla);
  al cargar se valida la identidad y se reconstruye el mundo con `_construirSalas`, sin red.
