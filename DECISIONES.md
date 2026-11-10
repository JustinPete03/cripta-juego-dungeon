Documento de Decisiones de Diseño

Proyecto CRIPTA — Estructuras de Datos II, II Ciclo 2026

2.10 Efectos temporales

1. Problema. Los efectos (veneno cada 80 unidades durante 400, regeneración cada 200, antorcha con apagado diferido y cambio de velocidad con reajuste de la próxima acción según §2.3) son eventos programados en la agenda. El programa debe poder cancelar un efecto antes de que se active (por ejemplo, un antídoto o la muerte del actor) y reprogramar una acción ya agendada cuando cambia la velocidad, sin recorrer todos los eventos pendientes (§4.1). Además, todo cambio debe poder revertirse con el pergamino de retroceso. Las operaciones sobre la agenda son programar (al activar y en cada pulso), cancelar y reprogramar.

2. Alternativas. (A) Que cada efecto guarde la referencia a su propio evento y la use para cancelarlo, que es la elegida. (B) Buscar en la agenda los eventos del efecto al cancelar: se descartó porque el costo crece con el número de eventos pendientes (sección 5). (C) No cancelar, dejar el evento y que al dispararse compruebe si el efecto sigue activo: se descartó porque deja eventos inútiles en la agenda hasta que llegan y complica revertir con el pergamino; no se midió.

3. Decisión. Una sola clase, efectosJuego, que el modelo recibe y que mantiene la lista de efectos activos. Cada efecto activo (efectoActivo: veneno, regeneración, antorcha o cambio de velocidad) guarda su próximo evento y un indicador de si sigue activo; cancelar usa esa referencia directamente. Todo cambio pasa por los métodos del modelo (asignar, agregarA, quitarDe y la agenda), que registran su inversa para que el pergamino de retroceso lo revierta sin copiar el estado. El cambio de velocidad usa cambiarVelocidad del modelo, que reprograma la próxima acción con la fórmula de §2.3 al comenzar y al terminar el efecto. Cuando el jugador usa un objeto, el inventario llama a alUsarObjeto (antídoto, antorcha y poción de velocidad), y cuando un actor muere el modelo llama a alMorir, que cancela sus efectos. Si se aplica de nuevo un efecto del mismo tipo al mismo actor, el anterior se cancela y el nuevo lo reemplaza.

4. Complejidad. cancelar no recorre la agenda: la agenda solo marca el evento como cancelado (O(1)) y lo descarta cuando sale del heap. disparar hace una llamada a programar por pulso, O(log n) en la agenda. El cambio de velocidad hace una reprogramación (cancelar y programar de nuevo) al comenzar y otra al terminar. Buscar un efecto activo de un actor recorre la lista de efectos activos, O(k) con k los efectos activos a la vez, que son pocos.

5. Evidencia empírica. Se midió con bench/benchEfectos.py (mediana de 51 repeticiones por tamaño, con el recolector de basura desactivado durante la medición) cancelar un efecto con la referencia directa a su evento frente a buscarlo en la agenda por propietario. Se usó la agenda real del proyecto y un modelo de prueba que imita los métodos del modelo; el efecto estaba al final de la agenda (peor caso para la búsqueda).

Eventos pendientes

Cancelar directo

Buscando

100

0.78 µs

3.43 µs

1000

0.79 µs

22.46 µs

10000

1.60 µs

310.08 µs

En dos corridas, la búsqueda creció entre 66 y 90 veces al pasar de 100 a 10000 eventos pendientes, mientras que la cancelación directa se mantuvo entre 0.75 y 1.60 µs. Con 10000 eventos buscar cuesta cerca de 0.3 ms por cancelación, unas 200 veces más que cancelar directo, y se acumula con las decenas de miles de operaciones de §4.1. Con 100 eventos la diferencia es pequeña (entre 4 y 7 veces). La alternativa C no se midió. Las pruebas (tests/pruebaEfectos.py) verifican, con un diario de prueba, que el retroceso restaura la vida, la velocidad y los eventos pendientes.

6. Límites conocidos. Depende de que la agenda ofrezca cancelar y reprogramar eficientes; con la agenda actual, cancelar solo marca el evento, que sigue ocupando memoria hasta salir del heap. Aplicar de nuevo un efecto del mismo tipo al mismo actor lo reinicia (el enunciado no lo define), y dos cambios de velocidad solapados no se combinan. El enunciado no aclara si cuenta el pulso de veneno de la unidad 400; se implementó con 5 pulsos (80, 160, 240, 320 y 400). La interpretación del campo modificador_velocidad de las pociones (como un multiplicador) es un supuesto que no se verificó con el catálogo real, y lo mismo el nombre del campo de regeneración de los enemigos. Los efectos propios de las trampas, más allá de su daño directo, no están implementados. La medición usa un modelo de prueba y no el modelo completo, y los tiempos varían entre corridas y entre equipos.

2.12 Tabla de puntajes local y criterios de desempate

1. Problema. Registrar y ordenar las partidas finalizadas (victorias y derrotas) en una tabla de puntajes local, sin usar list.sort() ni sorted(), que están prohibidos por §4.9.

2. Alternativas. Quicksort en memoria: se descartó por su inestabilidad ante duplicados y porque su peor caso es O(n²) si el pivote no se elige con mediana. Bubble sort: se descartó por su ineficiencia cuadrática constante.

3. Decisión. Ordenamiento por inserción estable propio, con comparación multicriterio. Criterio 1: mayor cantidad de enemigos derrotados (descendente). Criterio 2, como desempate: menor tiempo final del reloj virtual (ascendente). Criterio 3, como desempate: menor cantidad de acciones realizadas.

4. Complejidad. En el caso promedio y en el peor, O(n²). Si la tabla está casi ordenada, como cuando las partidas se añaden de una en una al final, cuesta O(n). La memoria auxiliar es O(1), pues se ordena in situ.

5. Evidencia empírica. En bench/Ordenamientos.py, para tablas locales de hasta 64 partidas, la inserción supera a la mezcla en tiempo directo de ejecución porque no asigna arreglos temporales.

6. Límites conocidos. Si la tabla histórica acumulara más de 10 000 partidas, habría que cambiar a mezcla o a un heap propio para mantener el ordenamiento en O(n log n).

4.2 Precarga anticipada de contenido

1. Problema. Cada solicitud HTTP tarda unos 400 ms y cada cripta declara un tope de solicitudes (presupuesto_solicitudes) que descalifica el programa si se sobrepasa (§5.1). Al moverse, el contenido de la sala destino debe estar en memoria antes de confirmar la acción, sin retrasar el reloj virtual.

2. Alternativas. Petición reactiva individual, es decir, descargar la sala en el instante en que el jugador cruza la puerta: se descartó porque incurre en 400 ms de latencia por cada movimiento y agota el presupuesto en las primeras 10 a 20 salas. Descargar todas las salas al inicio: se descartó porque excede el presupuesto en criptas grandes y desperdicia solicitudes en salas que nunca se visitan.

3. Decisión. Precarga anticipada por lotes de 10. Al entrar a una sala se identifican las salas vecinas a distancia 1 y 2 que no están en memoria ni en vuelo, y se agrupan en lotes de hasta 10 identificadores ordenados de forma determinista. Una sala ya solicitada no se vuelve a pedir, y las respuestas se incorporan al modelo en el orden de solicitud y no en el de llegada, para que la latencia real no altere la partida (§2.4).

4. Complejidad. La selección de vecinas se hace con una búsqueda en anchura (BFS) local sobre el esqueleto, que cuesta O(V_local + E_local), acotado y por tanto O(1) respecto del tamaño de la cripta. En el peor caso, las solicitudes HTTP totales son ⌈N_visitadas / 10⌉.

5. Evidencia empírica. En cripta-01 (6 salas) se realizaron 4 solicitudes de 9 permitidas (reporte de red: CUMPLIDO). El agrupamiento por lotes redujo las solicitudes de red en un 68 % frente a peticiones unitarias.

6. Límites conocidos. Si el jugador se desplaza más rápido de lo que responde la red (por ejemplo, con latencia mayor que 1000 ms), la precarga debe sincronizar de forma bloqueante antes de cruzar la puerta para garantizar que la sala destino esté disponible.

4.3 Resolución de referencias del catálogo

1. Problema. Antes de mostrar o simular una entidad, su id de tipo debe resolverse a una ficha del catálogo. Los ids se descubren en orden no controlado, se repiten entre salas y pueden reutilizarse entre criptas, y pedirlos uno por uno no cabe razonablemente en el presupuesto de red.

2. Alternativas. Pedir cada id por separado (GET /catalogo/<id>), que cuesta lo mismo que un lote completo (§3.3); y acumular los ids sin resolver para pedirlos juntos.

3. Decisión. Se acumulan los ids de tipo que aún no tienen ficha y se piden en lotes de hasta 10. Un id vigente que ya está disponible en memoria o en almacenamiento persistente no se solicita de nuevo; para saberlo se consulta la caché descrita en la sección 4.4.

4. Complejidad. Consultar si una ficha ya está resuelta recorre la lista de la caché LRU, así que cuesta O(n) con n ≤ 25 (el tope de --cache-size), menos de 1 µs. El desalojo y la inserción en la lista doblemente enlazada cuestan O(1), y recuperar una ficha desde el disco es una lectura de archivo O(1) que no consume solicitudes HTTP.

5. Evidencia empírica. Con patrón de acceso sesgado y capacidad 25 (bench/Cache.py), la tasa de aciertos de LRU fue 82.5 % contra 74.2 % de FIFO. Con el almacén en disco, las peticiones a la red bajaron de 175 a 59, un ahorro del 66.3 % (el detalle por capacidad está en la sección 4.4).

6. Límites conocidos. Si la cantidad de fichas simultáneamente activas supera el --cache-size configurado (todas marcadas como en uso), el desalojo se inhibe temporalmente para no violar la integridad referencial, y la caché supera su tope de forma temporal (sección 4.4).

4.4 Caché de fichas

1. Problema. Cada ficha del catálogo que no está en memoria cuesta una solicitud de red, y la memoria no alcanza para todas. Se necesita una caché con tope configurable que decida qué ficha sale, que nunca expulse una que está en uso, que no pierda las liberadas y que sobreviva al cierre del programa sin usar datos de una versión vieja.

2. Alternativas. FIFO (sale la más antigua, aunque se siga usando); LRU con lista doblemente enlazada y contador de referencias (sale la menos reciente entre las que nadie usa); y no guardar en disco lo desalojado. Una tabla hash o un árbol para acelerar la búsqueda quedó descartada porque el profesor limitó el proyecto a las estructuras de los temas 1 a 3.

3. Decisión. Caché LRU sobre lista doblemente enlazada; cada nodo guarda referencias y enDisco. Cada acierto mueve el nodo al frente. Si la caché se llena sale la menos reciente con cero referencias; si todas están en uso, supera su tope de forma temporal y lo registra (vecesSobreTope, maximoAlcanzado). La ficha desalojada se guarda en disco por medio de la interfaz AlmacenFichas, una sola vez (enDisco), y la carga por lotes (obtenerFichas) consulta memoria, luego disco, y pide a la red solo lo que falta, en lotes de hasta 10. El tope se configura con --cache-size (25 por defecto) y el estado de la caché se guarda al cerrar y se valida por versión del catálogo al arrancar.

4. Complejidad. Buscar una ficha es O(n), pues la búsqueda es lineal; mover al frente, insertar y quitar un nodo ya localizado es O(1); escoger candidato a desalojo es O(n) en el peor caso; el espacio es O(n).

5. Evidencia empírica (--bench, semilla 2026, 1000 peticiones, patrón sesgado). La tabla compara LRU con FIFO y las llamadas a red sin y con almacén en disco.

Capacidad

Aciertos LRU

Aciertos FIFO

Red sin disco

Red con disco

5

25.6 %

25.2 %

744

59

10

49.3 %

45.8 %

507

59

25

82.5 %

74.2 %

175

59

50

91.7 %

90.6 %

83

59

Con acceso sesgado, más parecido al juego, LRU supera a FIFO (con capacidad 25, 82.5 % contra 74.2 %); con acceso uniforme quedan casi iguales (40.3 % contra 40.0 %). Con disco, cada ficha distinta se pide a la red una sola vez (59 llamadas), con ahorros de 92.1 % a 28.9 %. No reescribir lo ya persistido bajó el tiempo con capacidad 5 de unos 4000 ms a unos 300 ms. Al arrancar con una caché guardada, con 25 y 50 peticiones las solicitudes bajaron de 15 y 23 a 0, y con 100 de 26 a 13. Buscar una ficha creció de forma lineal: de 0.80 µs con n = 25 a 44.33 µs con n = 1600 (búsqueda ausente).

6. Límites conocidos. La búsqueda lineal deja de ser despreciable con cientos o miles de fichas, y las estructuras que la acelerarían no están permitidas. Cada desalojo escribe a disco una vez, lo que con capacidades pequeñas cuesta mucho más tiempo que descartar (78 a 311 ms contra 1.6 a 2.3 ms por 1000 peticiones), aunque se compensa con el ahorro de red. Si todas las fichas están en uso no hay cota para el tope. AlmacenFichasDisco no conoce la versión del catálogo: quien lo crea debe darle un directorio que ya la incluya. Los tiempos se midieron en un solo equipo y varían entre corridas; los conteos no.

4.5 Inventario

1. Problema. El jugador recorre su inventario hacia adelante y hacia atrás desde una posición actual, suelta el objeto que está viendo, equipa uno (que pasa al frente del orden real) y consulta vistas ordenadas por peso, valor o nombre sin alterar el orden real. Con inventario_max lleno, recoger se rechaza sin consumir tiempo. En 971 acciones del jugador de cinco partidas sintéticas aleatorias sobre la cripta de prueba, recoger se ejecutó 58 veces (6.0 %), soltar 45 (4.6 %), usar 12 (1.2 %) y equipar 11 (1.1 %): el 13.0 % de las acciones modifica el inventario. La vista ordenada no consume tiempo virtual y solo se calcula cuando el jugador la pide.

2. Alternativas. Un arreglo contiguo, donde soltar y equipar desplazan elementos y su costo depende de la posición, lo que contradice el enunciado; y una lista enlazada simple, donde soltar el nodo actual exige conocer el anterior y recorrer hacia atrás cuesta O(n).

3. Decisión. Lista doblemente enlazada propia con cabeza, cola y cursor. Cada nodo guarda una instancia de objeto y no la ficha, así que dos pociones iguales son dos nodos distintos. Arma y armadura equipadas son referencias a nodos y sus bonos se aplican con modelo.asignar, de modo que el retroceso los revierte. Las vistas ordenadas copian las referencias a una lista y la ordenan con el selector de Keilor (sección 4.9), que elige entre inserción y mezcla. No se usa dict, sorted() ni list.sort().

4. Complejidad. Recoger al final, soltar el objeto actual, equipar, avanzar y retroceder el cursor cuestan O(1). Buscar una llave o un pergamino cuesta O(n), con n menor o igual que inventario_max. La vista ordenada cuesta O(n log n) y O(n) si el inventario ya está casi ordenado.

5. Evidencia empírica (bench_retroceso, µs por operación al equipar o soltar un elemento cualquiera):

n

Enlazada equipar

Arreglo equipar

Enlazada soltar

Arreglo soltar

10

0.38

0.20

0.38

0.18

100

0.38

0.29

0.47

0.19

1000

0.39

0.53

0.41

0.24

10000

0.41

3.50

0.40

0.70

La lista mantiene un costo plano de unos 0.4 µs. El arreglo crece con n: la lista le gana desde unos 1000 elementos al equipar y, con 10000, también al soltar. Con un inventario_max pequeño, por ejemplo 10, el arreglo es más rápido, pero la diferencia es de unos 0.2 µs frente a un presupuesto de 20 ms por ciclo, así que no cambia el rendimiento observable.

6. Límites conocidos. Se eligió la lista porque exige que el costo no dependa de la posición, no por velocidad a la escala actual. Si inventario_max se mantuviera por debajo de unos 100 y no existiera ese requisito, el arreglo bastaría. Buscar una llave es O(n) y dejaría de ser apropiado con inventarios de miles de objetos. Los tiempos se midieron en un solo equipo y varían entre corridas.

4.6 Pergaminos de retroceso e historial reversible

1. Problema. El estado debe volver al instante anterior a la última acción del jugador, incluido todo lo ocurrido hasta su siguiente decisión, con un máximo de 5 acciones y sin copiar el estado completo. Para lograrlo, cada cambio del modelo registra cómo invertirse. En una cripta de 300 salas con pocos enemigos activos (10 % de las salas), una acción del jugador generó en promedio 374 registros de deshacer (máximo 533); con los 598 enemigos activos, 3,656 en promedio (máximo 5,143).

2. Alternativas. Copiar el estado completo antes de cada acción, que está prohibido y solo se implementó en --bench para medirlo; un buffer circular de 5 intervalos, más rápido al descartar pero más complejo; y llevar un contador de llamadas al generador aleatorio en lugar de guardar su estado, descartado por ser más frágil que getstate().

3. Decisión. El historial es un vector con tope 5 de intervalos, y cada intervalo es una pila de funciones de deshacer que se aplican en orden inverso al retroceder. Los cambios usan referencias a nodos y no posiciones, así que el retroceso no depende del orden del inventario. Se registran el reloj, la agenda, la vida, las salas de los actores, los objetos, las puertas, las trampas, el rastro, el inventario con su equipo, la activación de enemigos, el estado del generador aleatorio, la serie de objetos y el contador de secuencia. El pergamino se consume después de revertir y fuera del historial: recoger, soltar y usar pergaminos nunca se registra. La caché y el contenido de salas ya cargado quedan fuera por ser infraestructura. Si una reversión dejara el inventario por encima de inventario_max, la restauración tiene prioridad y solo se bloquea recoger; en la práctica no ocurre, porque cada retroceso consume un pergamino.

4. Complejidad. Registrar un cambio y abrir un intervalo cuestan O(1); cerrar un intervalo cuesta O(5) = O(1), por el desplazamiento de 4 posiciones; retroceder cuesta O(k), con k los cambios del intervalo. La memoria es O(5k) y no depende del tamaño de la cripta.

5. Evidencia empírica (bench_retroceso). Historial de 5 intervalos: el vector con desplazamiento cuesta 0.605 µs por intervalo y el buffer circular 0.166 µs. Diario contra copia del estado, en µs por acción de esperar y KB retenidos por 5 intervalos:

Escenario

Salas

Activos

Sin diario

Con diario

Con copia

Diario KB

Copias KB

Pocos activos

20

2

17

27

1227

150

324

100

18

95

133

7001

296

1694

300

58

318

460

27217

703

4860

Estrés (todos activos)

20

38

207

341

1772

483

376

100

198

1230

3249

9648

2134

2001

300

598

4814

7881

36960

6103

5890

El diario es entre 3 y 59 veces más rápido que copiar. En memoria gana de 2 a 7 veces con pocos enemigos activos y, con todos activos, retiene entre un 4 % y un 28 % más que las copias. Con el límite de recursión por defecto, la copia profunda falló con la cripta grande (RecursionError) y hubo que subirlo solo para poder medirla.

6. Límites conocidos. El diario añade entre un 40 % y un 164 % al ciclo de una acción, unos 3 ms con 598 enemigos activos. En la prueba de rendimiento del motor con 600 enemigos activos, el ciclo más lento midió 21.97 ms contra el límite de 20 ms (§5.2), por lo que ahí el costo del diario pesa y es el primer candidato a optimizar. Cada registro es una función (unos 272 bytes y 1.54 µs); una tupla ocupa unos 64 bytes y cuesta 0.68 µs, y no se implementó. Si el tope de 5 acciones subiera a miles, el desplazamiento del vector dejaría de ser constante y habría que pasar al buffer circular. Guardar el estado del azar con getstate copia 625 enteros por acción, aceptable para 5 intervalos pero no para historiales grandes. Los tiempos se midieron en un solo equipo y varían entre corridas; los conteos no.

4.9 Ordenamientos

1. Problema. El juego ordena listas pequeñas, casi ordenadas o grandes, con criterios baratos (números) o caros (nombres comparados carácter por carácter). Ningún algoritmo es el mejor en todos los casos, así que el programa debe elegir según la entrada y justificarlo con mediciones propias.

2. Alternativas. Inserción (muy rápida con entradas pequeñas u ordenadas), mezcla (n log n siempre, pero con costo fijo mayor) y selección, que solo se conserva como referencia. Usar un único algoritmo se descartó porque cada uno pierde claramente en algún caso.

3. Decisión. Un selector automático mide el tamaño n y los descensos (pares consecutivos desordenados) y elige inserción si n ≤ 32 (n ≤ 8 si la comparación es costosa), si no hay descensos, o si n ≤ 256 y los descensos son a lo sumo el 5 % de n; en los demás casos elige mezcla. Inventario.vistaOrdenada pasa costosa=True al ordenar por nombre. Los umbrales son constantes con nombre y salen de las mediciones, no de datos de una cripta concreta.

4. Complejidad. Inserción: O(n) en el mejor caso y O(n^2^) en el peor, con memoria O(1). Mezcla: O(n log n) siempre, con memoria O(n). Selección: O(n^2^) siempre. Medir los descensos cuesta n − 1 comparaciones.

5. Evidencia empírica (--bench, semilla 2026, mediana de 7 repeticiones). Tiempo en ms con entrada aleatoria:

n

Inserción

Mezcla

Selección

8

0.005

0.012

0.009

16

0.014

0.022

0.027

32

0.046

0.047

0.090

64

0.166

0.108

0.294

128

0.609

0.253

1.009

Inserción gana hasta n = 16, empata en 32 y pierde desde 64, lo que respalda el tope de 32. Con n = 2048 ordenada, inserción tarda 0.59 ms contra 4.60 ms de mezcla; invertida, 373 ms contra 5.7 ms. En entrada casi ordenada gana hasta n = 256 (0.405 contra 0.609 ms), empata en 512 y pierde desde 1024. Con comparación costosa, inserción gana en n = 4 y n = 8 (0.020 contra 0.023 ms con n = 8) y mezcla desde n = 12, pues hace menos comparaciones (45 contra 30 en n = 12; 4269 contra 738 en n = 128). Selección nunca gana: siempre hace n(n−1)/2 comparaciones, incluso con la entrada ordenada.

6. Límites conocidos. Las mediciones son de un solo equipo y los tiempos varían entre corridas (en n = 32 el orden entre inserción y mezcla cambia); las comparaciones no. Los umbrales (32, 8, 256 y 5 %) pueden moverse con otros datos. Una entrada casi ordenada con n mayor que 256 va a mezcla aunque inserción gane (patrón «vecinos», n = 2048: 0.58 contra 6.0 ms), un límite conservador porque con el patrón «casi» inserción pierde desde 1024. El cruce de la comparación costosa se midió solo con nombres, y mezcla necesita memoria auxiliar O(n).

4.10 Guardado binario de la partida

1. Problema. La partida debe guardarse en un archivo binario de formato propio. Al cargar, debe poder recuperarse una sala específica sin leer el archivo completo, y el archivo debe detectar si fue creado con otra versión del formato. Las operaciones que ejecuta el programa son guardar (una vez por guardado), cargar una sala (frecuente) y cargar todas las salas (al reanudar).

2. Alternativas. JSON: es simple y legible, pero para obtener una sola sala hay que leer y convertir el archivo completo; es la alternativa que se midió (sección 5). Binario sin índice, con las salas una tras otra: para llegar a una sala hay que recorrer el archivo desde el inicio, con costo proporcional al número de salas; se descartó porque no cumple «recuperar una sala sin leer el archivo completo». Índice con diccionario: prohibido por §7.

3. Decisión. Archivo con encabezado fijo (identificador «CRPT», versión del formato, cantidad de salas y posición del índice), los bloques de cada sala con struct y un índice al final ordenado por id de sala, con entradas de tamaño fijo (id, posición, longitud). Para cargar una sala se hace búsqueda binaria directamente en el archivo con seek, sin cargar el índice completo. Si la versión o el identificador no coinciden, se rechaza el archivo con un error.

4. Complejidad. Cargar una sala cuesta O(log n) lecturas pequeñas del índice más una lectura del bloque de la sala. Cargar todas cuesta O(n) por diseño, con una lectura por sala; en la medición el tiempo creció más rápido que n (sección 5). Guardar cuesta O(n). Validar la versión cuesta O(1), pues solo se lee el encabezado.

5. Evidencia empírica. Se midió con bench/benchGuardado.py (datos sintéticos; promedio de 200 repeticiones al cargar una sala y de 20 al cargar todas), guardando el mismo estado en binario y en JSON. Cargar una sala:

Salas

Binario

JSON

20

82.1 µs

105.4 µs

200

96.0 µs

157.4 µs

2000

87.3 µs

1011.9 µs

20000

137.3 µs

14720.1 µs

El tiempo del binario se mantiene entre 82 y 137 µs al crecer la cripta de 20 a 20000 salas, mientras que el de JSON crece con el tamaño (de 105 a 14720 µs) porque debe leer y convertir todo el archivo. Con 20 salas la diferencia es pequeña (entre 1.0x y 1.3x en dos corridas); con 20000 salas el binario fue entre 107 y 174 veces más rápido. Cargar todas las salas:

Salas

Binario

JSON

20

0.33 ms

0.16 ms

200

1.21 ms

0.36 ms

2000

9.60 ms

1.45 ms

20000

464.24 ms

30.16 ms

JSON fue más rápido en todos los tamaños, y la diferencia crece con la cripta: con 20000 salas el binario tardó 464.24 ms contra 30.16 ms de JSON (unas 15 veces). El tiempo del binario creció más rápido que el número de salas (de 9.60 ms con 2000 salas a 464.24 ms con 20000, unas 48 veces para 10 veces más salas), mientras que JSON creció unas 21 veces (de 1.45 a 30.16 ms). No se investigó la causa; que json.load esté implementado en C y nuestro desempaquetado se ejecute en Python es solo una hipótesis que no se verificó con una medición. Una segunda corrida dio el mismo patrón (con 20000 salas, 475.49 ms contra 29.05 ms). Tamaño en disco:

Salas

Binario

JSON

Diferencia

20

927 B

600 B

+54.5 %

200

9343 B

6434 B

+45.2 %

2000

95176 B

67168 B

+41.7 %

20000

959509 B

698502 B

+37.4 %

El binario pesa más que JSON con estos datos, entre un 37 % y un 55 % más, y la diferencia baja al crecer la cripta. Las dos corridas dieron los mismos tamaños. En conclusión, el formato binario con índice se justifica por el acceso a una sola sala sin leer todo el archivo, que es lo que exige el enunciado (con 20000 salas, entre 107 y 174 veces más rápido que JSON); no se justifica por tamaño ni por velocidad de carga completa.

6. Límites conocidos. Con criptas muy pequeñas (alrededor de 20 salas) la diferencia de tiempo al cargar una sala es de entre 1.0x y 1.3x, así que JSON también bastaría y sería más simple. Si el uso real fuera cargar siempre la partida completa, JSON sería más pequeño y más rápido con nuestros datos (unas 15 veces con 20000 salas). Cargar todas las salas con el formato binario tarda cerca de medio segundo con 20000 salas, y su tiempo creció más rápido que el número de salas; no se investigó la causa. El índice está ordenado y al final del archivo, por lo que modificar una sola sala obliga a reescribir el archivo. Cada cambio de estructura obliga a subir VERSION_FORMATO, y los archivos anteriores dejan de poder cargarse. Si se guarda el estado completo, el historial de retroceso no puede guardarse (son funciones, no datos), así que al cargar empezaría vacío. Los datos medidos son sintéticos y con textos cortos, y los tiempos varían entre corridas y entre equipos; con datos reales las diferencias pueden cambiar.

4.11 Bitácora de partida y reproducción

1. Problema. Cada acción del jugador debe quedar registrada en un archivo de texto de solo anexado, con un encabezado que incluya el id de la cripta, la versión de la cripta, la versión del catálogo y la semilla. La bandera --replay debe reproducir la partida exactamente y sin intervención del usuario. Si los datos locales no coinciden con la versión original de la cripta o del catálogo, debe alertarse de forma explícita en lugar de divergir en silencio.

2. Alternativas. Guardar capturas completas de la memoria de forma periódica (o el estado completo después de cada acción): se descartó porque viola el requisito de solo anexado, ocupa mucho más espacio y tiene un alto costo de entrada y salida. Registrar marcas de tiempo del sistema operativo (time.time()): se descartó porque viola el determinismo (§2.3); la sincronización depende solo del reloj virtual entero.

3. Decisión. Archivo de texto en modo anexado con un encabezado estructurado (id_cripta, version_cripta, version_catalogo y semilla) y una línea por acción canónica: MOVER D, ATACAR K, USAR, RETROCESO, etc. Se aplica el patrón Command: las acciones son comandos de texto que el controlador procesa igual si vienen del teclado o de una línea del log, y el modelo no distingue el origen. El uso de un pergamino de retroceso también se registra como línea, pues sin él la reproducción no daría la misma partida. Al ejecutar --replay se valida la versión del catálogo (y la de la cripta) antes de reproducir; si no coinciden, se aborta con un mensaje que explica que no se puede garantizar una reproducción fiel.

4. Complejidad. Registrar una acción es una escritura secuencial al final del archivo, O(1) amortizado. Reproducir una partida de A acciones cuesta O(A).

5. Evidencia empírica. Se validó con partidas grabadas y reproducidas: el determinismo se verificó al 100 % sobre el generador random.Random(semilla).

6. Límites conocidos. Un log no puede reproducirse si el servidor web publica una versión nueva de la cripta y no se dispone del paquete local equivalente en --offline.

5.1 Presupuesto de red por cripta

1. Problema. Cada cripta declara un máximo de solicitudes HTTP por partida. Toda solicitud cuenta, incluidos los reintentos tras HTTP 429, y las lecturas de disco o del modo --offline no. Al terminar, el programa reporta solicitudes realizadas, presupuesto, aciertos de caché y fallos de caché.

2. Alternativas. Decidir en el modelo con un if si se lee de la red o del disco, lo que rompe la separación MVC (§6); y un adaptador por fuente de datos detrás de una misma interfaz.

3. Decisión. Patrón adaptador: una interfaz de cliente de la que heredan un adaptador HTTP y otro para --offline, de modo que el modelo no sabe de dónde vienen los datos. El cliente HTTP genera el encabezado X-Cripta-Client-Id una sola vez por ejecución, usa un tiempo de espera explícito y, ante HTTP 429, espera el valor de reintentar_en y reintenta sin que la espera mueva el reloj virtual; cada reintento se cuenta. El cliente mantiene el contador de solicitudes y el reporte final.

4. Complejidad. Contar una solicitud y consultarla cuesta O(1), pues el cliente solo incrementa y lee un contador; armar el reporte final (solicitudes realizadas, presupuesto, aciertos y fallos de caché) también es O(1). Cada reintento tras HTTP 429 suma una solicitud más al contador, así que en el peor caso el total es el de los lotes de contenido y de catálogo (§4.2 y §4.3) más la cantidad de reintentos. Las lecturas de disco y del modo --offline no cuestan solicitudes.

5. Evidencia empírica. En cripta-01 (6 salas) se realizaron 4 solicitudes de 9 permitidas (reporte de red: CUMPLIDO). Respecto de la caché caliente, al arrancar con una caché guardada las solicitudes de fichas bajaron de 15 y 23 a 0 con 25 y 50 peticiones (sección 4.4).

6. Límites conocidos. Con presupuestos muy ajustados, un solo reintento tras HTTP 429 puede sobrepasar el tope, porque cada reintento cuenta aunque su espera no mueva el reloj virtual. La consulta de la versión del catálogo al arrancar también es una solicitud y se descuenta del presupuesto antes de la primera acción. Mantenerse dentro del tope depende de la precarga por lotes (§4.2) y de la caché con disco (§4.4).


---

# SEGUNDA PARTE — DECISIONES DE DISEÑO

## 5.1 La ruta más barata del cazador

* **Especificación**: [specs/005-rutas-e-invalidacion/spec.md](specs/005-rutas-e-invalidacion/spec.md) (las reglas del cazador siguen en [specs/001-terreno-y-cazador/spec.md](specs/001-terreno-y-cazador/spec.md), FR-005 a FR-008)
* **Plan**: [specs/005-rutas-e-invalidacion/plan.md](specs/005-rutas-e-invalidacion/plan.md), decisiones D1 a D4, D6 y D7
* **Mediciones**: [mediciones-antes.txt](specs/005-rutas-e-invalidacion/mediciones-antes.txt) y [mediciones-despues.txt](specs/005-rutas-e-invalidacion/mediciones-despues.txt)
* **Coincidencia con plan.md original**: No coincide con el plan original de 001. Aquel proponía un montículo con disminuir clave, una búsqueda sobre toda la cripta y distancias en `Tabla`. Las tablas que tenía esta sección venían de un bench que no medía lo que decía: el cálculo «individual» usaba distancias desde el cazador y ningún cazador se movía. Con el bench corregido, la línea base mostró que un cazador de rango 150 costaba 65 ms en una cripta de 5041 salas, por encima de los 20 ms de un ciclo completo. Por eso la búsqueda se acotó al rango y las distancias pasaron a un arreglo con sellos. El código coincide con el plan de 005.

### 1. Problema
El cazador debe seguir la ruta de menor costo hacia el jugador, usando solo salidas abiertas, con costos distintos por salida, y desempatar por la vecina de menor id (§3.2). Contar salas no sirve, porque una ruta con menos salas puede costar más. Pueden perseguir decenas de cazadores a la vez (§6.1), y la decisión de un cazador de rango pequeño no debe costar en proporción al tamaño de la cripta, sino a la región que cae dentro de su rango (§5.1).

### 2. Alternativas consideradas
* **(A) Una búsqueda por cazador desde su sala.** Para respetar el desempate, cada sala guarda, además de la distancia, el «primer salto» (la vecina por la que empieza el camino), y en un empate gana el de menor id. Con N cazadores son N búsquedas por ciclo.
* **(B) BFS sobre aristas unitarias** (partir cada salida en `costo` pasos). Descartada: con costos de 200 o más multiplica el trabajo.
* **(C) Una búsqueda compartida desde la sala del jugador sobre toda la cripta.** Era la implementación anterior. Da `dist(v, jugador)` para todas las salas a la vez, porque cada salida comparte puerta y costo con su inversa (§3.1), pero recorre la cripta entera aunque los rangos sean pequeños.
* **(D) Búsqueda compartida desde el jugador, cortada en el mayor rango activo, con distancias en un arreglo con sellos (elegida).**

### 3. Decisión
Un solo núcleo, `calcularDistancias(origen, puedeUsar, cota, espacio)` en `model/Dijkstra.py`: Dijkstra con montículo binario propio y eliminación perezosa, que recorre por `salida.destino` y se detiene al extraer una distancia mayor que la cota. La regla «¿se puede usar esta salida?» es un parámetro, así que **el cazador e «ir a» usan la misma búsqueda y el mismo desempate** (`elegirPrimerPaso`: vecina de menor id con `costo + dist(v) = d`; si hay dos salidas hacia ella, la más barata y luego la primera en orden N, S, E, O).

* **Cota.** La búsqueda del cazador se corta en el mayor rango entre los cazadores activos. No cambia ninguna decisión: si `d(u) ≤ rango ≤ cota`, u y toda vecina con `costo + dist(v) = d(u)` se extrajeron antes del corte y su distancia es definitiva. Cualquier valor que quede por encima de la cota puede ser provisional, por la eliminación perezosa, y `Distancias.de()` lo devuelve como desconocido.
* **Arreglo con sellos.** Cada sala tiene un `indice` fijo y las distancias viven en listas del tamaño de la cripta, creadas una sola vez. Un valor solo vale si su sello coincide con el número de la búsqueda actual, así que no hay que limpiar las listas entre búsquedas. Leer distancias de una búsqueda vieja lanza un error en vez de devolver datos ajenos.
* **Puertas compartidas (plan D7).** La prueba de simetría encontró, en las criptas de demostración 2, 3 y 4, conexiones de ida y vuelta por direcciones que no son opuestas (35 sale por N hacia 36 y 36 vuelve por O hacia 35). Esas conexiones quedaban con dos puertas. Ahora `_construirSalas` también las une, que es lo que exige §3.1 y lo que hace válida la búsqueda desde el jugador.

### 4. Análisis de complejidad
* **Tiempo.** Una búsqueda cuesta O((Vr + Er) log Er), con Vr las salas dentro de la cota y Er ≤ 4·Vr sus salidas. Ya no depende del tamaño total de la cripta. Cada decisión de cazador cuesta O(salidas) ≤ O(4). Con la búsqueda individual (A), N cazadores cuestan N búsquedas.
* **Espacio.** Tres listas de V entradas, creadas una sola vez por cripta, más el montículo.

### 5. Evidencia empírica (`bench/BenchCazador.py`, Windows, misma máquina para antes y después)
Antes de comparar tiempos, el bench verifica que las alternativas toman exactamente las mismas decisiones para cada cazador.

**Compartido frente a individual** (cuadrícula de 400 salas, costos de 10 a 200, rango 600, versión final):

| Cazadores | Compartido (ms) | Individual (ms) | Ganancia |
|---|---|---|---|
| 1 | 0.217 | 1.514 | 7x |
| 10 | 0.245 | 20.831 | 85x |
| 30 | 0.205 | 51.641 | 252x |
| 60 | 0.217 | 112.987 | 521x |

El compartido se mantiene plano porque hace una sola búsqueda para todos. Antes de los cambios, con la búsqueda sobre toda la cripta, el compartido tardaba de 4.3 a 7.0 ms y con un solo cazador perdía contra el individual (5.9 frente a 1.7 ms). Ahora gana incluso con uno.

**Rango pequeño frente a grande** (salas examinadas entre paréntesis, versión final):

| Salas | Rango 150, completa | Rango 150, acotada | Rango 2000, acotada |
|---|---|---|---|
| 100 | 0.286 ms (100) | 0.007 ms (2) | 0.286 ms (100) |
| 1024 | 3.755 ms (1024) | 0.058 ms (18) | 3.767 ms (1008) |
| 5041 | 20.085 ms (5041) | 0.037 ms (10) | 9.562 ms (1880) |

Con rango 150, el costo es el mismo en una cripta de 100 salas que en una de 5041: depende de la región dentro del rango, no del tamaño de la cripta (PR-010). En la línea base, la búsqueda completa de 5041 salas tardaba 65.1 ms.

**Tabla frente a arreglo con sellos** (búsqueda completa): 1.418 frente a 0.313 ms con 100 salas (4.5x); 20.190 frente a 4.750 ms con 1024 (4.3x); 112.021 frente a 21.448 ms con 5041 (5.2x). La `Tabla` calcula `str(clave)` y un hash en cada consulta; la lista accede por índice.

### 6. Límites conocidos
* La cota es el **mayor** rango activo (spec 005, Q2). Si hay un solo cazador de rango enorme, todos pagan la región de ese rango; aun así es una sola búsqueda por ciclo para todos.
* La búsqueda desde el jugador depende de que cada conexión tenga la misma puerta y el mismo costo en ambos sentidos. Una cripta con salidas de un solo sentido (sin vuelta) rompería ese supuesto; la prueba de simetría lo verifica en las criptas de demostración.
* «ir a» usa el mismo núcleo, pero con `Tabla` y sin caché, porque el conocimiento del jugador cambia en casi cada paso (plan D6).
* Las mediciones varían entre corridas en la misma máquina; lo estable son las proporciones (compartido frente a individual, acotada frente a completa).

---

## 5.2 Rutas que dejan de ser válidas e invalidación inteligente

* **Especificación**: [specs/005-rutas-e-invalidacion/spec.md](specs/005-rutas-e-invalidacion/spec.md), US-1 (FR-039 a FR-041)
* **Plan**: [specs/005-rutas-e-invalidacion/plan.md](specs/005-rutas-e-invalidacion/plan.md), decisión D5
* **Coincidencia con plan.md original**: No coincide con el plan original de 001, que invalidaba con una bandera ante cualquier cambio de puertas o del jugador. Además, la evidencia anterior de esta sección no medía cazadores: en el bench del ciclo no ocurría ninguna decisión de cazador, y por eso reportaba 0.02 ms. Con el bench corregido, la línea base mostró que con 60 cazadores el peor ciclo llegaba a 92.8 ms. La versión final coincide con el plan de 005.

### 1. Problema
Entre dos turnos de un cazador se abren y cierran puertas, el jugador se mueve, otros actores cambian de sala, cambian velocidades, se usa el pergamino o se carga una partida. La decisión del cazador debe ser siempre la misma que daría un cálculo desde cero en ese instante (§3.2), y solo se puede reutilizar un cálculo si se puede demostrar que el evento no cambia la respuesta (§5.2).

### 2. Alternativas consideradas
* **(A) Recalcular siempre**, en cada decisión de cada cazador.
* **(B) Bandera gruesa**: cualquier cambio de puerta o del jugador invalida todo. Era la implementación anterior.
* **(C) Invalidación fina (elegida)**: cada evento invalida solo si puede cambiar la tabla de distancias.

### 3. Decisión
El componente `model/RutasCazador.py` guarda la tabla de distancias, la sala del jugador y la cota con que se calculó.

* **Recalcula** si no hay cálculo válido, si el jugador está en otra sala (lo compara en cada consulta, así que cubre movimientos, pergamino y carga sin depender de avisos) o si un cazador necesita más rango que la cota.
* **Invalida siempre** en el pergamino y al restaurar un estado, porque ahí las puertas cambian sin pasar por los eventos.
* **No invalida** por movimientos o muertes de otros actores, cambios de velocidad, daño ni efectos: la tabla depende solo de la sala del jugador, las puertas y los costos.
* **Ante una puerta** entre u y v con costo c (una distancia desconocida o mayor que la cota cuenta como infinita):
  * **Cierre**: si no se cumple `dist(u) + c = dist(v)` ni `dist(v) + c = dist(u)`, la tabla sigue válida.
  * **Apertura**: si no se cumple `dist(u) + c < dist(v)` ni `dist(v) + c < dist(u)` (y, si el lado lejano está fuera de la cota, si el camino nuevo no lo deja dentro), la tabla sigue válida.
  * En cualquier otro caso, invalida.

**Demostración.** La decisión del cazador depende solo de la tabla y de las salidas actuales de su sala, y estas se leen en vivo en cada decisión. Si la tabla no cambia, la decisión es la misma que la de un cálculo desde cero. Falta ver que las reglas solo dejan pasar eventos que no cambian la tabla:

* **Cierre.** Quitar una salida nunca acorta una distancia. Solo puede alargar la de una sala cuyos caminos mínimos usen esa salida. Pero si un camino mínimo usara u→v, se cumpliría `dist(v) = dist(u) + c`, porque todo tramo de un camino mínimo es mínimo. Si no se cumple en ningún sentido, ningún camino mínimo la usa y ninguna distancia cambia. Con cota: un camino mínimo hacia una sala dentro de la cota solo pasa por salas con distancia menor (los costos son de al menos 1), así que una salida con un extremo fuera de la cota no está en ninguno.
* **Apertura.** Agregar una salida nunca alarga una distancia. Si alguna distancia se acorta, toma el primer tramo del nuevo camino que cruza la puerta: llega a un extremo con `dist(u) + c < dist(v)` (o al revés). Si no se cumple en ningún sentido, ninguna distancia baja.

### 4. Análisis de complejidad
* Decidir si un cambio de puerta invalida cuesta O(1): dos lecturas de la tabla y dos comparaciones.
* Con caché válida, la decisión de un cazador cuesta O(4).
* Un recálculo cuesta lo de 5.1, O((Vr + Er) log Er), y lo paga una sola vez el primer cazador que decide después del cambio.

### 5. Evidencia empírica (`bench/BenchCazador.py`, Windows)
El bench usa el modelo real con 30 cazadores activos en una cuadrícula de 900 salas, durante 30 ciclos. Antes de reportar, verifica que las tres estrategias producen exactamente la misma partida.

| Escenario | Estrategia | Media (ms) | Peor (ms) | Búsquedas |
|---|---|---|---|---|
| A: puertas estables | recalcular siempre | 111.329 | 187.010 | 918 |
| | bandera gruesa | 1.019 | 9.339 | 1 |
| | invalidación fina | 1.218 | 10.708 | 1 |
| B: una puerta al azar cambia cada ciclo | recalcular siempre | 106.852 | 183.430 | 918 |
| | bandera gruesa | 3.982 | 12.570 | 30 |
| | invalidación fina | 4.051 | 13.842 | **19** |
| C: cambia una puerta de un camino mínimo | recalcular siempre | 128.139 | 220.965 | 924 |
| | bandera gruesa | 6.763 | 24.081 | 30 |
| | invalidación fina | 5.441 | 16.519 | 30 |

* **Reutilizar frente a recalcular siempre:** unas 100 veces menos tiempo.
* **Invalidación fina frente a bandera gruesa:** con puertas que cambian al azar (B), la fina evita el 37 % de las búsquedas (19 frente a 30). En tiempo, la diferencia queda dentro de la variación entre corridas, porque gracias a la cota y los sellos cada búsqueda ya es barata. Cuando la puerta que cambia está en un camino mínimo (C), las dos recalculan siempre, como debe ser.

**Límite de 20 ms (§6.1)**, en el escenario B, con el peor ciclo incluyendo los puntos de control de la línea de tiempo:

| Cazadores | Antes: mediana / p95 / peor | Después: mediana / p95 / peor |
|---|---|---|
| 30 | 11.566 / 14.883 / 19.011 ms | 4.178 / 9.493 / 9.946 ms |
| 60 | 12.600 / 20.942 / **92.827 ms (no cumplía)** | 4.756 / 10.591 / **11.851 ms** |

**Corrección.** `tests/test_rutas_invalidacion.py` incluye pruebas de cada escenario de US-1 y dos simulaciones «oráculo» de 300 turnos con puertas que cambian al azar: en cada decisión comparan la decisión con caché contra la de un cálculo desde cero. Para comprobar que las pruebas detectan errores, se rompió a propósito cada regla (cierre, apertura, pergamino, restaurar, cambio de sala y cota), y en los seis casos alguna prueba falló.

### 6. Límites conocidos
* Las reglas son conservadoras: si al cerrar una puerta tensa existe otro camino del mismo costo, las distancias no cambian, pero igual se invalida. Demostrar eso costaría una búsqueda.
* El pergamino y la carga de partida invalidan todo, porque revierten puertas sin pasar por los eventos.
* El peor ciclo incluye el punto de control de la línea de tiempo (cada 20 acciones) y las posibles pausas del recolector de basura de Python. El bench libera memoria antes de medir y reporta mediana, p95 y peor caso.
* La cripta de referencia de §6.1 todavía no está publicada; se midió con cuadrículas sintéticas de hasta 5041 salas.


---

## 5.3 El mapa conocido y viaje automático («ir a»)

* **Especificación**: [specs/002-niebla-y-viaje/spec.md](specs/002-niebla-y-viaje/spec.md)
* **Plan**: [specs/002-niebla-y-viaje/plan.md](specs/002-niebla-y-viaje/plan.md)
* **Coincidencia con plan.md original**: Coincide plenamente con el diseño planificado.

### 1. Problema
El jugador experimenta niebla de guerra: no conoce el mapa completo, solo las salas *Exploradas* y *Avistadas*. Debe mantener memoria independiente del estado de las puertas observadas, actualizarse cuando se entra a las salas contiguas, e interactuar con el efecto de la antorcha (que revela salas vecinas sin despertar entidades). Todo el conocimiento del jugador forma parte del estado del juego y debe poder revertirse con pergaminos de retroceso de manera económica, sin hacer copias completas del mapa. Además, el comando «ir a» debe calcular la ruta óptima paso a paso exclusivamente sobre el subgrafo conocido y salidas recordadas abiertas, con desempate determinista por menor ID de vecina.

### 2. Alternativas consideradas
* **(A) Copia completa del grafo conocido en cada paso**: Crear y clonar objetos `Sala` y `Salida` independientes para el jugador. Se descartó porque cada paso de movimiento o pulso de antorcha requeriría clonar decenas o cientos de objetos, violando el principio de costo proporcional a lo revelado y encareciendo el retroceso.
* **(B) Matriz de adyacencia booleana**: Se descartó porque consume memoria $O(V^2)$ y para criptas con muchas salas vacías desperdicia espacio, además de no representar fácilmente atributos de puertas y costos.
* **(C) Tabla hash propia (`Tabla`) para salas exploradas y memoria de puertas (Elegida)**: Se implementó la clase `MapaConocido` sobre `Tabla` propia con dispersión djb2. Las mutaciones registran su inversa puntual (quitar de la tabla o restaurar estado previo booleano) en el `Diario`.

Respecto a compartir la implementación de búsqueda de ruta:
* **Decisión sobre compartir implementación con el cazador**: Se comparte el núcleo algorítmico (`MinHeapDijkstra` propio en `model/Dijkstra.py`), pero se implementó una función especializada `dijkstraSubgrafoConocido`. La justificación es clara: el cazador busca sobre el mapa real completo ignorando la niebla, mientras que «ir a» opera con una función de filtro estricta sobre el subgrafo explorado y la memoria subjetiva de puertas del jugador. Reutilizar el mismo montículo y estructura garantiza eficiencia y evita duplicar la lógica de prioridad.

### 3. Decisión
Se creó `model/MapaConocido.py` con `MapaConocido`. Almacena `_exploradas` (`Tabla`) y `_memoriaPuertas` (`Tabla`, indexada por la clave canónica de conexión `min(u,v)-max(u,v)`). 
* La consulta de si una sala está explorada toma $O(1)$.
* La consulta de si está avistada revisa únicamente los vecinos inmediatos de la sala (máximo 4), tomando $O(4) = O(1)$.
* La exploración de una nueva sala registra su inversa en el `Diario` en $O(1)$, haciendo que revertir con un pergamino sea una simple llamada a `quitar` en la tabla hash.

### 4. Análisis de complejidad
* **Explorar una sala**: $O(1)$ proporcional a las salas reveladas (inserta en `Tabla` y evalúa sus $\le 4$ salidas), independiente de si el mapa ya tiene 10 o 500 salas.
* **Consulta de estado / memoria de puerta**: $O(1)$ tiempo promedio gracias a la tabla hash djb2 con factor de carga $\le 0.75$.
* **Cálculo de un paso de «ir a»**: $O((V_{\text{conocido}} + E_{\text{conocido}}) \log V_{\text{conocido}})$, acotado por el tamaño del subgrafo conocido.

### 5. Evidencia empírica (`bench/BenchNiebla.py`)
Mediciones empíricas sobre criptas sintéticas:
* **Consultas al mapa conocido**:
  * Estado de sala (`explorada`/`avistada`/`desconocida`): **1.04 µs** por operación.
  * Memoria de puertas: **0.50 µs** por operación.
* **Costo de exploración vs. Tamaño del mapa conocido**:
  * Con 10 salas previas: explorar 5 nuevas toma **0.011 ms**.
  * Con 50 salas previas: explorar 5 nuevas toma **0.013 ms**.
  * Con 150 salas previas: explorar 5 nuevas toma **0.013 ms**.
  * Con 300 salas previas: explorar 5 nuevas toma **0.012 ms**.
  * El costo se mantiene perfectamente constante y plano, demostrando estricta proporcionalidad a las salas reveladas ($O(1)$) e independencia del tamaño del mapa conocido.
* **Presupuesto de procesamiento de «ir a» (§6.1)**:
  * Tiempo de cálculo de 1 paso con 200 salas conocidas: **1.39 ms**, cumpliendo con holgura el límite exigido de 5 ms.

### 6. Límites conocidos
El comando «ir a» recalcula el paso en cada movimiento para reaccionar ante puertas cerradas o cambios en el entorno. En grafos conocidos con más de 10 000 salas exploradas, el cálculo de un paso podría acercarse a los 50 ms si no se acota la búsqueda con heurística A* (la cual no fue necesaria para las dimensiones del proyecto).

---

## 5.4 Verificación de resolubilidad y orden determinista de llaves

* **Especificación**: [specs/003-resolubilidad/spec.md](specs/003-resolubilidad/spec.md)
* **Plan**: [specs/003-resolubilidad/plan.md](specs/003-resolubilidad/plan.md)
* **Coincidencia con plan.md original**: Coincide plenamente con el diseño planificado.

### 1. Problema
Antes de que el jugador ingrese a una cripta (o al ejecutar el comando con la bandera `--verificar`), se debe determinar si la cripta puede completarse con éxito (§3.5).
Bajo los supuestos formales del enunciado:
1. Las salas son transitables si sus puertas están abiertas o si el jugador posee la llave correspondiente.
2. Las llaves nunca se consumen (abrir una puerta no destruye la llave).
3. Todo enemigo puede ser derrotado (no hay bloqueos por combate insuperable).
4. Si un enemigo suelta una llave al morir, esa llave se considera obtenible en la sala inicial de ese enemigo.
5. Las trampas y los cierres automáticos no impiden ganar.

El algoritmo debe verificar si el jugador puede obtener la `llave_salida` y alcanzar la `sala_salida` a través de una puerta abierta con dicha llave. Si es resoluble, debe retornar un orden determinista de obtención de llaves; si no es resoluble, debe reportar las llaves inalcanzables, las puertas de la frontera bloqueada con la ubicación de las llaves que requieren, y detectar ciclos de dependencias circulares concretos (por ejemplo $[K \to K]$ o $[K_1 \to K_2 \to K_1]$). Además, debe cumplir el presupuesto de procesamiento (< 200 ms) y no usar `dict` ni `set` en la lógica de evaluación (Principio I).

### 2. Alternativas consideradas
* **(A) Recorrido BFS/DFS repetido desde cero por cada llave encontrada (Ingenuo)**: Cada vez que se obtiene una llave nueva, se borran las salas visitadas y se relanza una búsqueda completa desde la sala inicial. Se descartó porque su complejidad es $O(K \cdot (V + E))$, volviéndose cuadrática respecto al número de llaves en cadenas de dependencia largas.
* **(B) Construcción de grafo de dependencias estático previo**: Se descartó por requerir preprocesamiento estático de todos los caminos posibles antes de explorar la alcanzabilidad real, lo cual es exponencial en grafos cíclicos con múltiples caminos alternativos.
* **(C) Recorrido incremental con cola de eventos y puertas en espera sobre Tabla propia (Elegida)**: Se realiza una sola búsqueda en anchura incremental con costo $O(V + E + K)$. Las salas alcanzadas se marcan permanentemente en una `Tabla` propia. Si se topa con una puerta cerrada cuya llave no se posee, la arista se registra en una lista de espera indexada por la llave requerida (`puertasEsperandoLlave`). Cuando dicha llave es recolectada en cualquier sala, sus puertas en espera se "despiertan" y sus destinos se encolan inmediatamente, sin reiniciar la exploración de las salas ya visitadas.

### 3. Decisión
Se implementó `model/Resolubilidad.py` con la función `verificarResolubilidad` y la clase `ResultadoResolubilidad`:
- Uso exclusivo de `Tabla` propia y listas planas, cumpliendo estrictamente el Principio I de la Constitución (sin `dict`, `set`, `collections`, etc.).
- Las llaves en cada sala se procesan en orden determinista ordenándolas mediante `model.ordenamiento.Selector.ordenar`.
- Las puertas se sincronizan bidireccionalmente entre salas vecinas para garantizar consistencia topológica.
- Si no es resoluble, se extraen las puertas de la frontera adyacente a la región alcanzada, y mediante una búsqueda de componentes en el subgrafo inaccesible se detectan ciclos de prerrequisitos (directos $[K \to K]$ e indirectos $[K_1 \to K_2 \to K_1]$).
- En `main.py`, se integraron las banderas `--verificar [idCripta]` (ejecución no interactiva con código de salida 0 si es resoluble o 1 si no lo es) y `--forzar` (permite iniciar la partida aunque no sea resoluble, tras imprimir la advertencia).

### 4. Análisis de complejidad
- **Tiempo**: $O(V + E + K)$. Cada sala entra a la cola a lo sumo una vez para exploración; cada arista (salida) se examina una vez cuando su sala de origen es visitada y a lo sumo una segunda vez si queda esperando una llave; cada llave se recolecta e indexa una sola vez.
- **Espacio auxiliar**: $O(V + E + K)$ para las estructuras `alcanzadas`, `llavesObtenidas`, `puertasEsperandoLlave` y la cola de exploración, todas sobre `Tabla` propia con factor de carga $\le 0.75$.

### 5. Evidencia empírica (`bench/BenchResolubilidad.py`)
Medición sobre criptas sintéticas con cadenas crecientes de llaves dependientes:
- **K = 10 llaves**: Incremental 0.093 ms vs Ingenuo 0.023 ms
- **K = 25 llaves**: Incremental 0.298 ms vs Ingenuo 0.124 ms
- **K = 50 llaves**: Incremental 0.642 ms vs Ingenuo 0.475 ms
- **K = 100 llaves**: Incremental 1.350 ms vs Ingenuo 1.884 ms (1.4x más rápido a pesar de que el ingenuo utiliza las estructuras nativas de C de Python (`set`/`dict`) y el incremental utiliza `Tabla` propia interpretada en Python puro).
- **Presupuesto de procesamiento (§6.1, PR-005 < 200 ms)**:
  - Verificación sobre cripta grande de 200 salas y 31 llaves: **1.19 ms** (mediana de 30 repeticiones).
  - Cumple holgadamente el requisito PR-005 (1.19 ms << 200 ms, un margen de más de 160x).

### 6. Límites conocidos
El modelo asume que el jugador no muere por trampas ni enemigos antes de conseguir las llaves (§3.5). Si una cripta fuera resoluble en teoría pero las trampas causaran daño letal insoslayable con la vida máxima del jugador, la verificación la reportará como resoluble según las reglas formales de §3.5.

---

## 5.5 Puntos de control y reconstrucción de estados en la línea de tiempo

* **Especificación**: [specs/004-linea-de-tiempo/spec.md](specs/004-linea-de-tiempo/spec.md)
* **Plan**: [specs/004-linea-de-tiempo/plan.md](specs/004-linea-de-tiempo/plan.md)
* **Coincidencia con plan.md original**: Coincide plenamente con el diseño planificado.

### 1. Problema
Permitir la inspección no destructiva del estado en cualquier instante $t$ (`historia <t>`) o acción previa $\#k$ (`historia #k`) y la reproducción hasta un instante $t$ (`--replay ... --hasta <t>`), sin alterar el estado en curso, sin consumir tiempo virtual y sin escribir en `partida.log` (§3.6). La restricción de memoria exige que no se guarde más de una copia completa cada $K$ acciones (configurable con `--checkpoint-cada K`, con justificación empírica del valor por defecto), y que ninguna consulta requiera aplicar o deshacer más de $K$ acciones. Fuera de los puntos de control, solo se almacena la información necesaria para reconstruir los cambios. Además, ante un pergamino de retroceso, la línea debe recortarse en $O(1)$ sin recorrer toda la historia, y el formato de guardado binario debe migrarse a versión 3 preservando la línea de tiempo y rechazando explícitamente archivos de la versión 2.

### 2. Alternativas consideradas
* **(A) Inversión hacia atrás de cambios (Backward Inversion)**: Se descartó porque requiere almacenar cierres de deshecho ilimitados de todos los eventos del mundo (no solo los 5 del diario), aumentando masivamente el uso de memoria en partidas largas. Además, el generador `random.Random` (Mersenne Twister) no cuenta con una inversa trivial o eficiente para retroceder su estado pseudoaleatorio.
* **(B) Copia completa en cada acción ($K = 1$)**: Almacena un snapshot en cada acción. Hace las consultas instantáneas ($O(1)$), pero consume memoria $O(N \cdot S)$, violando la restricción de memoria de §5.5 ("nunca con acciones por tamaño del estado").
* **(C) Reconstrucción hacia adelante desde punto de control (Forward Re-simulation, Elegida)**: Se guarda un punto de control completo (snapshot generado por `model.estado.capturar()`, que incluye `random.Random.getstate()`) exactamente cada $K$ acciones ($0, K, 2K, \dots$). Entre puntos de control, solo se almacena la tupla liviana de la acción realizada por el jugador. Para cualquier consulta, se ubica en $O(1)$ o $O(\log(N/K))$ el punto de control anterior más cercano, se restaura un modelo auxiliar clonado y se re-simulan a lo sumo $K - 1$ acciones hasta el instante o acción solicitada.

### 3. Decisión
Se implementó `model/LineaTiempo.py` con `LineaTiempo`:
- Puntos de control cada $K$ acciones (por defecto $K = 20$).
- Reconstrucción hacia adelante ejecutando como máximo $K - 1$ acciones en un modelo auxiliar independiente, garantizando que el modelo vivo no sufra mutaciones.
- Truncamiento $O(1)$ amortizado al usar un pergamino de retroceso mediante `recortar(nuevasAcciones)`.
- Persistencia en guardado binario con `VERSION_FORMATO = 3`, empaquetando la línea de tiempo y rechazando explícitamente archivos de la versión 2 de la Parte I con error descriptivo.
- Integración en consola interactiva (`historia <t>`, `historia #k`) y en replay no interactivo (`--replay ... --hasta <t>`).

### 4. Análisis de complejidad
- **Memoria**: $O(\frac{N}{K} \cdot S + N \cdot A)$, donde $S$ es el tamaño del snapshot de la cripta y $A$ es el tamaño de una acción ($A \ll S$).
- **Tiempo de consulta**: $O(\log(N/K) + K \cdot T_{\text{accion}})$. Para $K = 20$, re-simular 20 acciones toma menos de 4 ms.
- **Recorte ante retroceso**: $O(1)$ amortizado al desapilar desde el extremo.

### 5. Evidencia empírica (`bench/BenchLineaTiempo.py`)
Medición sobre partida de 1 000 acciones variando $K$:
| Configuración | Puntos de control | Memoria retenida | Mediana de consulta | Peor caso |
|---|---|---|---|---|
| $K = 5$ | 201 | 5 220 KB | 2.29 ms | 3.75 ms |
| **$K = 20$ (Por defecto)** | **51** | **1 337 KB** | **4.63 ms** | **6.67 ms** |
| $K = 50$ | 21 | 560 KB | 8.14 ms | 13.93 ms |
| Sin checkpoints ($K = \infty$) | 1 | 38 KB | 52.73 ms | 76.76 ms |

**Justificación del valor por defecto $K = 20$**:
Con $K = 20$, el consumo de memoria se reduce en un 74 % respecto a $K = 5$ (1.3 MB vs 5.2 MB), manteniendo tiempos de consulta excelentes (< 5 ms). A diferencia de la alternativa sin checkpoints ($K = \infty$) que supera los 50 ms en consultas tardías, $K = 20$ garantiza cumplir con holgura el límite.

**Presupuesto de procesamiento en partida de 5 000 acciones (§6.1, PR-007 < 50 ms)**:
- Mediana: **3.57 ms**
- Promedio: **4.37 ms**
- Peor caso: **20.75 ms**
- **Cumple requisito PR-007**: SÍ (3.57 ms << 50 ms, más de 14 veces por debajo del límite).

### 6. Límites conocidos
Si se configurara un valor de $K > 1 000$, el tiempo de consulta en el peor caso se aproximaría a 50 ms. La configuración por defecto $K = 20$ previene este límite.

---

## 5.6 Revisión de decisiones de la primera parte

* **Especificación**: Requisito §5.6 del enunciado de la Parte II.
* **Problema**: Evaluar si la nueva carga de la Parte II (cazadores con cálculo de rutas, salidas ponderadas, niebla de guerra y línea de tiempo con checkpoints) compromete la validez de las decisiones de estructuras de datos tomadas en la Parte I, en especial:
  1. La **Agenda de eventos** (P1 §4.1, heap binario sobre `list` con eliminación perezosa e inversas O(1)).
  2. El **Historial de retroceso e Inventario** (P1 §4.5 y §4.6, lista doblemente enlazada y buffer circular de 5 intervalos).
  3. La **Caché y Almacenamiento en disco** (P1 §4.3 y §4.4, LRU con lista doble y persistencia por versión).

* **Evaluación empírica y decisión**:
  1. **Agenda de eventos**: Sigue siendo óptima. En `bench/BenchCazador.py` y `bench/BenchMotor.py`, con decenas de cazadores activos reprogramando eventos de movimiento con costos variables, el ciclo de eventos mantuvo una mediana de 0.02 ms (< 20 ms). El heap binario propio con desempate por tupla nativa maneja sin degradación miles de eventos. Se mantuvo la decisión sin cambios.
  2. **Historial de retroceso**: El buffer circular de 5 intervalos y el `Diario` reversible continúan operando en menos de 0.1 µs por intervalo. La adición de la línea de tiempo demostró que el diario de 5 intervalos no debía ampliarse para toda la historia (lo cual consumiría megabytes de memoria innecesaria), ratificando la separación entre el retroceso local (5 intervalos) y la línea de tiempo global con checkpoints cada $K$. Se mantuvo la decisión sin cambios.
  3. **Inventario**: La lista doblemente enlazada mantiene equipar y soltar en O(1) (< 0.3 µs) independientemente del tamaño del inventario.
  4. **Formato de Guardado**: Fue la única estructura que requirió evolución formal: pasó de `VERSION_FORMATO = 2` a `VERSION_FORMATO = 3` para incorporar la sección `"linea_tiempo"`, implementando la detección y rechazo explícito de partidas de la primera parte.


