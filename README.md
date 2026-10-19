# CRIPTA — Juego de mazmorra dirigido por eventos

Proyecto 1 de **Estructuras de Datos II** (II Ciclo 2026).
Diseño, implementación y evaluación de estructuras de datos propias en un juego de mazmorra
por eventos, con contenido descargado de un servicio web.

> Las reglas del juego están especificadas por el enunciado; las decisiones de estructuras
> de datos son nuestras y se justifican en el Documento de Decisiones de Diseño (sección 8
> del enunciado), que acompaña a esta entrega como documento aparte.

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

## Presupuesto de red

- Cada cripta declara `presupuesto_solicitudes`; el valor se lee de los datos generales y
  **no está escrito en el código**. Antes de *cualquier* solicitud el gestor reserva el costo
  (`_reservar`), así que el tope se respeta en la partida y no solo se reporta al final.
- Se usan lotes: hasta 10 salas por solicitud de contenido y hasta 10 ids por solicitud de
  catálogo, con los ids deduplicados y ordenados de forma determinista para que la misma
  partida siempre pida lo mismo.
- La precarga es cortés, no obligatoria: si el presupuesto no alcanza el lote de 10 salas, se
  recorta; si queda una sola solicitud en la recámara, se precarga nada más la sala del
  jugador; si se agota, la partida sigue y `asegurarContenidoSala` descarga la sala puntual
  antes de entrar.
- Cuando el presupuesto no da para meter una sala, el movimiento **se rechaza con un mensaje y
  sin gastar tiempo virtual** (§2.3 deja el mando al presupuesto). El modelo nunca entra a una
  sala sin contenido.
- Lecturas locales no cuentan como red (§5.1): en `--offline` el presupuesto no aplica y el
  reporte lo dice en lugar de mostrar un porcentaje vacío.
- Los reintentos tras HTTP 429 sí cuentan, y el esqueleto se recorre por páginas hasta que la
  *respuesta* dice cuántas hay (`total_paginas`), no con un número fijo escrito en el cliente.
- El reporte de §5.1 —solicitudes realizadas, presupuesto, aciertos y fallos de caché, fichas
  desalojadas y salas registradas— se imprime al terminar la partida en **ambas vistas**
  (consola e interfaz gráfica), porque el controlador recibe la función de reporte del adaptador.

## Caché y resolución del catálogo (§4.3 / §4.4)

Resolver una ficha (`asegurarCatalogo`, en `adapters/estrategiaRed.py`) agrupa, deduplica y
ordena los ids que una sala va a necesitar —enemigos, objetos del suelo y trampas— y los pide en
lotes de 10; un id que ya está en memoria o en disco nunca vuelve a generarse una solicitud.

- Tabla hash propia (`model/cache_estructuras.py`): cubetas que arrancan en 7 y crecen con el
  factor de carga 0.75 al superar `cubetas × 0.75`, con tope `--cache-size`. Sin ese crecimiento,
  un `--cache-size` grande degradaría cada búsqueda a un recorrido de cadena.
- Desalojo LRU justificado: la menos usada. La política opera solo sobre fichas **fuera de uso**;
  una ficha referenciada por un enemigo vivo, el inventario o la sala actual se protege en una
  pasada con el conjunto de ids en uso, antes de cada acceso —incluida la reinserción que produce
  un acierto en disco, que es justo la que puede desalojarla.
- Una ficha liberada de memoria sigue en `.cache_cripta/cat_<version_catalogo>/<id>.json`:
  recuperarla cuesta una lectura de disco, no una solicitud de red. Solo genera red una ficha
  nunca persistida o de otra versión de catálogo, y la caché sobrevive al cerrar el programa.
- El registro de salas que ya se conoce también es tabla hash propia, no `dict` (§7).
- Medido en `--bench` (ver `resultados_bench.txt`): con patrón sesgado y tope 25, LRU acierta
  82.5 % frente a 74.2 % de FIFO; con persistencia en disco la sesión restaurada necesita **0**
  solicitudes frente a las 175 de la misma carga sin disco; y la búsqueda se mantiene en ~2-3 µs
  con cadena media 0.78 tanto con 25 como con 1600 fichas en memoria.

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
pruebas porque no siguen la convención `test_*.py`. La suite son 173 pruebas.

Dos de los archivos pinan las reglas que más fácil se rompen:

- `tests/test_cache_catalogo.py` — la caché viva: las cubetas crecen con `--cache-size`, se
  desaloja la menos usada, una ficha en uso **no** se desaloja (ni por un acierto en disco), la
  persistencia relee sin red y `asegurarCatalogo` deduplica, ordena y corta los lotes en 10.
- `tests/test_presupuesto_red.py` — `presupuesto_solicitudes` se agota antes de pedir, no
  después; en `--offline` no aplica; y el movimiento rechazado por presupuesto no avanza el reloj.

`TestMotor.py` incluye la prueba del requisito de procesamiento (sección 5.2): con 600 enemigos
activos, el ciclo de eventos entre dos decisiones del jugador toma **~7 ms de mediana**
(se reporta mediana, p90 y peor; se compara la mediana porque la cola de la distribución son
interrupciones del sistema operativo, no del motor).

## Benchmarks (`--bench`)

```bash
python main.py --bench
```

Ejecuta cargas sintéticas y reporta tiempos por subsistema en seis bloques: ordenamientos,
caché (LRU frente a FIFO, disco y costo de búsqueda), guardado binario frente a JSON, efectos,
motor (agenda, rastro y bitácora) y retroceso con inventario. Cada bloque compara la estructura
viva contra alternativas, así que la salida es la evidencia de las decisiones. Los resultados de
referencia están en `resultados_bench.txt` y se analizan en el Documento de Decisiones. Los
tiempos dependen del equipo; los conteos (comparaciones, solicitudes) no.

## Arquitectura (MVC + adaptadores)

```
main.py                  Punto de entrada y banderas
model/                   Reglas del juego y estructuras de datos (sin red, disco ni interfaz)
  Juego.py               Modelo: reloj virtual, combate, puertas, trampas, retroceso
  Agenda.py              Agenda de eventos (montículo con cancelación y desempate por secuencia)
  Diario.py              Historial reversible (máx. 5 acciones, sin copias del estado)
  Inventario.py          Lista doblemente enlazada con cursor
  Tabla.py               Tabla hash propia: cubetas, factor de carga, djb2 (restricción sección 7)
  Rastro.py, Bitacora.py Rastro del jugador y bitácora circular de 20 mensajes
  efectos.py             Veneno, regeneración, antorcha, velocidad
  efectosTrampa.py       Extensión que contagia el veneno que declara la ficha de una trampa
  cache_estructuras.py   Caché de fichas (hash + LRU + en uso) y registro de salas
  estado.py              Traductor modelo <-> datos planos para el guardado
  ordenamiento/          Inserción, mezcla, selección y selector automático
  cache/                 Alternativa descartada (recorre la lista doble, O(n)); ver sección 4.4
controller/              ControladorJuego.py: traduce texto a acciones y coordina el flujo
view/                    Dos vistas del mismo estado, intercambiables
  Consola.py             Vista de consola
  Grafica.py             Vista pygame estilo Pokémon (--gui): escenas, menús, animaciones
  presentacion.py        Instantáneas del modelo para dibujar (no importa pygame)
  sprites.py             Hoja de sprites pixel art (rectángulos sobre una cuadrícula 16x16)
adapters/                Red y disco detrás de interfaces
  clienteCripta.py       Interfaz del cliente (incluye cuentaComoRed para el presupuesto)
  clienteHttp.py         Cliente HTTP (encabezado X-Cripta-Client-Id, manejo de 429)
  clienteOffline.py      Cliente que lee desde disco (no gasta presupuesto)
  estrategiaRed.py       Presupuesto, precarga por lotes y reporte de red
  ProveedorRed.py        Une cliente + caché para el modelo
  proveedor_demo.py      Fuente local para la GUI sin red
  bitacoraReplay.py      Bitácora de partida y validación de versiones
  tablaPuntajes.py       Tabla de puntajes local
  codBinary.py           Codificador binario propio (tag + cuerpo), sin JSON ni compresores
  guardadoBinario.py     Formato binario sección 4.10: índice por sala, versión de formato
  guardadoPartida.py     Partida completa sobre ese mismo contenedor (cripta/esqueleto/estado)
  guardadoJson.py        Contraparte JSON que usa el bench de sección 4.10 para comparar
  persistenciaCache.py   Fichas en disco por versión de catálogo (sección 4.4)
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
- El jugador **gana** al entrar a la sala de salida con la puerta que da acceso a ella abierta —
  la abrió él con la llave, o la cripta ya la entregó abierta (una puerta `cerrada: false` en el
  esqueleto no deja nada que abrir, y el requisito es entrar con acceso, no pulsar `abrir`)—,
  y **pierde** si su vida llega a 0.
- El pergamino de retroceso revierte la última acción del jugador y todo lo ocurrido después
  (máximo 5 acciones hacia atrás); no consume tiempo virtual.

## Restricciones de implementación

Las estructuras de datos usadas para resolver los problemas del sección 4 son propias: está
prohibido sustituirlas por equivalentes de bibliotecas, usar `dict` como índice o caché,
y `list.sort()` / `sorted()` en los ordenamientos evaluados. Se permite `list` como
almacenamiento contiguo, y `struct`, `json`, `requests` y `argparse`.

## Documentación de la entrega

- Documento de Decisiones de Diseño (sección 8 del enunciado): una sección por cada problema de
  sección 4 con problema, alternativas, decisión, complejidad, evidencia empírica y límites
  conocidos. La escribe el equipo aparte de este README.
- Bitácora de prompts de LLM (sección 10.3): archivo aparte de la entrega.
- `resultados_bench.txt` — salida de referencia de `--bench`, generada en el equipo local.

## Estado y limitaciones conocidas

> Actualice esta sección antes de cada entrega.

- [x] Todos los modos conectados en `main.py`: consola, `--offline`, `--replay`, `--puntajes`,
  `--bench` e `--gui` usan el mismo modelo, el mismo controlador y los mismos adaptadores.
- [x] Paquete sin conexión publicado en `datos_demo/` (las cuatro criptas del servicio).
- [x] Interfaz gráfica (`view/Grafica.py`) con las mismas 11 interacciones de sección 10.2 que la consola.
- [x] `guardar` / `cargar` conectados a la interfaz. `model/estado.py` expone `capturar` /
  `restaurar` (reloj, posición, inventario, efectos, agenda, semilla y estado del azar) y
  `Modelo.capturarEstado` / `restaurarEstado` los publican; `adapters/guardadoPartida.py` los
  guarda sobre el **mismo** contenedor binario de `adapters/guardadoBinario.py` (índice al final,
  payloads con `adapters/codBinary.py`: tag + cuerpo, sin JSON ni compresores), con magic y
  versión de formato para detectar archivos incompatibles.
- [x] El veneno se origina en trampas del contenido: la ficha declara `veneno` (daño por pulso)
  y `model/efectosTrampa.py` (extensión de `efectosJuego`, no lo modifica) lo contagia en
  `alActivarTrampa`. §2.10 fija la regla pero no el nombre del campo, y las fichas publicadas del
  servicio solo traen `{id, nombre, clase, daño, rearme}`, así que el veneno es una extensión
  opcional: se ejercita en `adapters/proveedor_demo.py` (demo gráfica) y en
  `tests/pruebaTrampaVeneno.py`, que incluye el caso de ficha sin el campo.
- [x] Persistencia de esqueleto y contenido por versión de cripta: el archivo `*.sav` embebe
  `esqueleto` y `contenido` junto a `cripta` (id, versión de cripta y de catálogo, semilla);
  al cargar se valida la identidad y se reconstruye el mundo con `_construirSalas`, sin red.
- [x] Ningún `dict` hace de índice, caché o tabla de búsqueda en el camino evaluado (§7). La
  tabla hash propia está en dos sitios con el mismo esquema (cubetas encadenadas, factor de
  carga, djb2): `model/Tabla.py` —`Tabla` y `Conjunto`, que usan el cliente offline, la
  deduplicación de lotes, el conjunto de fichas en uso y el índice de `model/estado.py`— y las
  cubetas de `model/cache_estructuras.py` (caché de fichas y registro de salas). El índice del
  guardado es un arreglo ordenado con búsqueda binaria, que es lo que da el acceso aleatorio por
  sala de §4.10.
- [x] `presupuesto_solicitudes` se respeta antes de solicitar, no solo se reporta (§5.1), con
  rechazo de movimiento sin gasto de tiempo cuando no alcanza y precarga recortable.
- [x] §9 sin datos de una cripta específica en el código: ni ids de sala, ni ids de entidad, ni
  cantidad de páginas, ni presupuestos, ni estadísticas. Las únicas literales de catálogo están
  en `bench/benchGuardado.py` (datos sintéticos) y en las fuentes de prueba y demo.

## Limitaciones conocidas

- **Agenda**: el montículo propio gana claramente frente al escaneo lineal (47 ms frente a
  2 984 ms con 5 000 eventos), pero `--bench` mide que con pocos eventos simultáneos una lista
  ordenada es más rápida que el montículo (n = 100: 47.9 ms frente a 116.7 ms; n = 1 500:
  29.7 frente a 36.9) porque el desplazamiento de `list` va en C mientras el sift compara en
  Python. Se mantiene el montículo por §4.1 —obtener el siguiente sin examinar todos— y porque
  el enunciado espera cientos de eventos simultáneos con decenas de miles de operaciones; la
  cruza empírica está en `resultados_bench.txt` y es honesta reportarla.
- **Campos de catálogo que el enunciado nombra pero el servicio no publica**: `regeneracion` y
  `modificador_velocidad` (§2.10 y §2.7) no aparecen en ninguna de las fichas reales cacheadas en
  `.cache_cripta/cat_be68d322d2f5/`. Se leen con valor por defecto, así que sus efectos quedan
  inactivos con los datos de hoy y solo se ejercitan con fichas de prueba. Si una cripta nueva
  los trae, el camino ya está escrito; la unidad de `modificador_velocidad` (multiplicador) es
  una suposición documentada en `model/efectos.py`.
- **El requisito de 20 ms (§5.2)** se verifica con la mediana del ciclo de 600 enemigos; en este
  equipo la mediana ronda 7-17 ms, pero bajo carga del sistema la prueba `testCicloMenorA20ms`
  puede tocar 25 ms por interrupciones del planificador de Windows, no del motor.
- El Documento de Decisiones (sección 8) y la bitácora de prompts (sección 10.3) son documentos
  aparte que el equipo debe escribir antes de la entrega.
