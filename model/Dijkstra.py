# Algoritmo de Dijkstra propio para cálculo de rutas de costo mínimo (§3.2, §5.1).
# Cumple con el Principio I de la Constitución: no utiliza heapq, dict, set ni bibliotecas externas.

from model.Tabla import Tabla


class MinHeapDijkstra:
    """Montículo binario de mínimos propio sobre list de Python.
    
    Almacena tuplas (distancia, idSala).
    """

    def __init__(self):
        self._heap = []

    def __len__(self):
        return len(self._heap)

    def estaVacio(self):
        return len(self._heap) == 0

    def empujar(self, distancia, idSala):
        self._heap.append((distancia, idSala))
        self._subir(len(self._heap) - 1)

    def extraerMin(self):
        if not self._heap:
            return None
        raiz = self._heap[0]
        ultimo = self._heap.pop()
        if self._heap:
            self._heap[0] = ultimo
            self._bajar(0)
        return raiz

    def _subir(self, i):
        heap = self._heap
        item = heap[i]
        while i > 0:
            padre = (i - 1) // 2
            if item < heap[padre]:
                heap[i] = heap[padre]
                i = padre
            else:
                break
        heap[i] = item

    def _bajar(self, i):
        heap = self._heap
        n = len(heap)
        item = heap[i]
        while True:
            izq = 2 * i + 1
            if izq >= n:
                break
            hijo = heap[izq]
            idxHijo = izq
            der = izq + 1
            if der < n and heap[der] < hijo:
                hijo = heap[der]
                idxHijo = der
            if hijo >= item:
                break
            heap[i] = hijo
            i = idxHijo
        heap[i] = item


# ============================================================================================
# Núcleo único de búsqueda de rutas (spec 005; plan 005, D1 a D4; tareas T006 y T007).
#
# Lo usan el cazador (desde la sala del jugador, con salidas realmente abiertas y cota = mayor
# rango activo) y «ir a» (desde el destino, con el conocimiento del jugador y sin cota). Las
# funciones anteriores (dijkstraDesde, dijkstraSubgrafoConocido) se mantienen hasta que nadie
# las use (T020).
# ============================================================================================

def puertaAbierta(sala, salida):
    """Regla del cazador para `puedeUsar`: solo salidas abiertas en este instante (FR-043)."""
    return not salida.puerta.cerrada


class EspacioBusqueda:
    """Arreglos reutilizables para las distancias de una cripta (plan 005, D3; tarea T005).

    Se crean una sola vez, del tamaño de la cripta, indexados por `Sala.indice`. Cada búsqueda
    usa un número de generación nuevo («sello»): el valor de una sala solo vale si su sello es el
    de la búsqueda actual. Así no hay que reinicializar los arreglos y el costo de una búsqueda
    sigue siendo proporcional a las salas que examina (PR-010).

    Un espacio sirve a un solo dueño: la búsqueda siguiente deja obsoletas las Distancias
    anteriores del mismo espacio.
    """

    def __init__(self, cantidadSalas):
        self.valor = [0] * cantidadSalas
        self.sello = [0] * cantidadSalas
        self.sala = [None] * cantidadSalas
        self.generacion = 0


class Distancias:
    """Resultado de una búsqueda: costo mínimo de cada sala al origen (plan 005, D2 y D3).

    Guarda los valores en un EspacioBusqueda (arreglos con sellos) o, si no se le da uno, en una
    Tabla (criptas armadas a mano en pruebas, «ir a»). Toda lectura pasa por `de()`.
    """

    def __init__(self, cota=None, espacio=None):
        self.cota = cota
        self.salasExaminadas = 0       # salas extraídas y expandidas (para medir PR-010)
        self.registradas = 0           # salas con algún valor (definitivo o provisional)
        self._espacio = espacio
        self._generacion = espacio.generacion if espacio is not None else None
        self._valores = Tabla() if espacio is None else None

    @classmethod
    def desdeTabla(cls, tabla):
        """Envuelve una Tabla id -> distancia sin cota (compatibilidad con dijkstraDesde)."""
        distancias = cls()
        distancias._valores = tabla
        distancias.registradas = len(tabla)
        return distancias

    def de(self, sala):
        """Distancia de `sala` al origen, o None si es desconocida.

        Un valor mayor que la cota también es desconocido: por la eliminación perezosa, al
        cortar la búsqueda pueden quedar valores provisionales que no son la distancia real.
        """
        if self._espacio is None:
            valor = self._valores.obtener(sala.id)
        else:
            espacio = self._espacio
            if espacio.generacion != self._generacion:
                raise RuntimeError("Distancias obsoletas: su espacio ya se usó en otra búsqueda.")
            i = sala.indice
            if espacio.sello[i] != self._generacion:
                return None
            valor = espacio.valor[i]
        if valor is None:
            return None
        if self.cota is not None and valor > self.cota:
            return None
        return valor

    def deId(self, idSala):
        """Como `de`, pero por id. Solo para distancias guardadas en Tabla: cubre salidas sin
        `destino` enlazado en criptas armadas a mano en pruebas."""
        if self._espacio is not None:
            raise RuntimeError("deId solo está disponible para distancias guardadas en Tabla.")
        valor = self._valores.obtener(idSala)
        if valor is None or (self.cota is not None and valor > self.cota):
            return None
        return valor

    def __len__(self):
        return self.registradas


def calcularDistancias(origen, puedeUsar, cota=None, espacio=None):
    """Dijkstra con montículo propio y eliminación perezosa (plan 005, D1).

    origen: Sala desde la que se mide.
    puedeUsar(sala, salida) -> bool: decide si la búsqueda puede usar esa salida.
    cota: si no es None, la búsqueda se detiene al extraer una distancia mayor (D2, PR-010).
    espacio: EspacioBusqueda de la cripta (requiere Sala.indice). Sin él se usa una Tabla.

    Recorre con `salida.destino`, sin buscar salas por id en el índice. Complejidad
    O((V + E) log E) sobre las V salas y E salidas que quedan dentro de la cota.
    """
    if espacio is not None:
        return _calcularConEspacio(origen, puedeUsar, cota, espacio)
    distancias = Distancias(cota)
    valores = distancias._valores
    salaPorId = Tabla()                # id -> Sala, para recuperar la sala al extraer del montículo
    valores.guardar(origen.id, 0)
    salaPorId.guardar(origen.id, origen)
    heap = MinHeapDijkstra()
    heap.empujar(0, origen.id)

    while not heap.estaVacio():
        d, uId = heap.extraerMin()
        if d > valores.obtener(uId):
            continue                   # entrada vieja: ya se encontró un camino más corto
        if cota is not None and d > cota:
            break                      # todo lo que queda en el montículo es aún más caro
        distancias.salasExaminadas += 1
        u = salaPorId.obtener(uId)
        for salida in u.salidas:
            if not puedeUsar(u, salida):
                continue
            v = salida.destino
            if v is None:
                continue
            nueva = d + salida.costo
            actual = valores.obtener(v.id)
            if actual is None or nueva < actual:
                valores.guardar(v.id, nueva)
                salaPorId.guardar(v.id, v)
                heap.empujar(nueva, v.id)
    distancias.registradas = len(valores)
    return distancias


def _calcularConEspacio(origen, puedeUsar, cota, espacio):
    """Mismo algoritmo que calcularDistancias, sobre los arreglos con sellos del espacio.

    El montículo guarda (distancia, índice de sala); el índice solo sirve para ubicar la sala:
    el desempate de la regla lo hace elegirPrimerPaso, no el orden del montículo.
    """
    espacio.generacion += 1
    g = espacio.generacion
    valor = espacio.valor
    sello = espacio.sello
    salaEn = espacio.sala
    distancias = Distancias(cota, espacio)
    registradas = 1
    examinadas = 0

    i0 = origen.indice
    valor[i0] = 0
    sello[i0] = g
    salaEn[i0] = origen
    heap = MinHeapDijkstra()
    heap.empujar(0, i0)

    while not heap.estaVacio():
        d, i = heap.extraerMin()
        if d > valor[i]:
            continue                   # entrada vieja
        if cota is not None and d > cota:
            break
        examinadas += 1
        u = salaEn[i]
        for salida in u.salidas:
            if not puedeUsar(u, salida):
                continue
            v = salida.destino
            if v is None:
                continue
            j = v.indice
            nueva = d + salida.costo
            if sello[j] != g:
                sello[j] = g
                valor[j] = nueva
                salaEn[j] = v
                registradas += 1
                heap.empujar(nueva, j)
            elif nueva < valor[j]:
                valor[j] = nueva
                heap.empujar(nueva, j)
    distancias.salasExaminadas = examinadas
    distancias.registradas = registradas
    return distancias


def elegirPrimerPaso(sala, distancias, puedeUsar):
    """Primer paso de una ruta de costo mínimo desde `sala` hacia el origen de `distancias`.

    Regla común del cazador y de «ir a» (§3.2, §3.4; plan 005, D4):
      - candidatas: salidas que `puedeUsar` acepta con costo + dist(destino) = dist(sala);
      - gana la vecina de menor id (FR-042);
      - hacia esa vecina, la salida más barata; si empatan, la primera en orden N, S, E, O
        (spec Q4). Las salidas de una sala ya están en ese orden.
    Devuelve la Salida elegida, o None si no hay ruta (o si `sala` es el origen).
    """
    d = distancias.de(sala)
    if d is None:
        return None
    mejor = None
    mejorId = None
    for salida in sala.salidas:
        if not puedeUsar(sala, salida):
            continue
        v = salida.destino
        vId = salida.destinoId
        dv = distancias.de(v) if v is not None else distancias.deId(vId)
        if dv is None or salida.costo + dv != d:
            continue
        # Se reemplaza solo si es estrictamente mejor, así gana la primera en orden N, S, E, O
        if (mejor is None or vId < mejorId
                or (vId == mejorId and salida.costo < mejor.costo)):
            mejor = salida
            mejorId = vId
    return mejor


# ============================================================================================
# Funciones de compatibilidad y viaje automático, construidas sobre el núcleo (T018 a T020).
# ============================================================================================

def _enlazarDestinos(salasIndice):
    """Completa `salida.destino` donde falte, como hace Juego._construirSalas.

    Las criptas del juego ya llegan enlazadas; esto solo cubre salas armadas a mano en pruebas
    que traen únicamente `destinoId`. Recorre el índice una vez: O(V + E).
    """
    if salasIndice is None:
        return
    for i in range(salasIndice.cantidad()):
        sala = salasIndice.enPosicion(i)
        for salida in sala.salidas:
            if salida.destino is None:
                salida.destino = salasIndice.buscar(salida.destinoId)


def dijkstraDesde(salaOrigen, salasIndice, rangoMax=None):
    """Envoltorio de compatibilidad: distancias desde salaOrigen por salidas abiertas.

    Desde la spec 005 la búsqueda vive en un solo lugar (calcularDistancias). Esta función se
    conserva porque la usan pruebas y benchmarks existentes; devuelve una Tabla id -> distancia,
    como antes. `salasIndice` ya no se necesita: la búsqueda recorre con `salida.destino`.
    """
    _enlazarDestinos(salasIndice)
    return calcularDistancias(salaOrigen, puertaAbierta, rangoMax)._valores


def _reglaConocimiento(mapaConocido):
    """Regla de «ir a» para `puedeUsar` (§3.4): solo salidas hacia salas exploradas cuya puerta
    el jugador recuerda abierta. Qué conoce el jugador lo define la spec 002."""
    def puedeUsar(sala, salida):
        return (mapaConocido.estaExplorada(salida.destinoId)
                and mapaConocido.puertaRecordadaAbierta(sala.id, salida.destinoId, salida.puerta))
    return puedeUsar


def dijkstraSubgrafoConocido(salaDestino, salasIndice, mapaConocido):
    """Envoltorio de compatibilidad: distancias hacia salaDestino usando solo el conocimiento
    del jugador (§3.4, §5.3). Devuelve una Tabla id -> distancia, o None si el destino no está
    explorado. La búsqueda es la misma que usa el cazador (spec 005, FR-044)."""
    if not mapaConocido.estaExplorada(salaDestino.id):
        return None
    _enlazarDestinos(salasIndice)
    return calcularDistancias(salaDestino, _reglaConocimiento(mapaConocido))._valores


def elegirPasoViajeAutomatico(salaActual, salaDestino, salasIndice, mapaConocido):
    """Calcula el siguiente paso para el comando 'ir a' (§3.4).

    Usa el núcleo común (spec 005, plan D6): búsqueda desde el destino sobre el conocimiento del
    jugador, sin cota ni caché, y el mismo desempate que el cazador (elegirPrimerPaso).
    Devuelve (salidaElegida, costoSalida).
    Si ya está en destino, devuelve (None, 0).
    Si no hay ruta conocida abierta hacia el destino, devuelve (None, None).
    """
    if salaActual.id == salaDestino.id:
        return (None, 0)
    if not mapaConocido.estaExplorada(salaDestino.id):
        return (None, None)
    puedeUsar = _reglaConocimiento(mapaConocido)
    distancias = calcularDistancias(salaDestino, puedeUsar)
    salida = elegirPrimerPaso(salaActual, distancias, puedeUsar)
    if salida is None:
        return (None, None)
    return (salida, salida.costo)
