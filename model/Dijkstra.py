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


def dijkstraDesde(salaOrigen, salasIndice, rangoMax=None):
    """Calcula distancias mínimas desde salaOrigen hacia todas las salas alcanzables
    a través de salidas abiertas.
    
    Utiliza Tabla propia para almacenar las distancias (Principio I: prohibido dict).
    Devuelve Tabla(idSala -> distanciaMinima).
    """
    distancias = Tabla()
    distancias.guardar(salaOrigen.id, 0)

    heap = MinHeapDijkstra()
    heap.empujar(0, salaOrigen.id)

    while not heap.estaVacio():
        distanciaActual, uId = heap.extraerMin()

        # Si ya encontramos un camino más corto a uId, descartamos este elemento perezosamente
        mejorConocida = distancias.obtener(uId)
        if mejorConocida is not None and distanciaActual > mejorConocida:
            continue

        if rangoMax is not None and distanciaActual > rangoMax:
            # Los elementos restantes en el montículo tendrán distancia >= distanciaActual
            break

        salaU = salasIndice.buscar(uId)
        if salaU is None:
            continue

        for salida in salaU.salidas:
            if salida.puerta.cerrada:
                continue
            vId = salida.destinoId
            nuevaDist = distanciaActual + salida.costo

            distV = distancias.obtener(vId)
            if distV is None or nuevaDist < distV:
                distancias.guardar(vId, nuevaDist)
                heap.empujar(nuevaDist, vId)

    return distancias


def dijkstraSubgrafoConocido(salaDestino, salasIndice, mapaConocido):
    """Calcula distancias mínimas hacia salaDestino utilizando EXCLUSIVAMENTE
    salas exploradas y salidas recordadas como abiertas por el jugador (§3.4, §5.3).
    """
    if not mapaConocido.estaExplorada(salaDestino.id):
        return None

    distancias = Tabla()
    distancias.guardar(salaDestino.id, 0)

    heap = MinHeapDijkstra()
    heap.empujar(0, salaDestino.id)

    while not heap.estaVacio():
        distanciaActual, uId = heap.extraerMin()

        mejorConocida = distancias.obtener(uId)
        if mejorConocida is not None and distanciaActual > mejorConocida:
            continue

        salaU = salasIndice.buscar(uId)
        if salaU is None:
            continue

        for salida in salaU.salidas:
            vId = salida.destinoId
            # La sala destino de la salida debe estar explorada
            if not mapaConocido.estaExplorada(vId):
                continue
            # La puerta debe ser recordada como abierta
            if not mapaConocido.puertaRecordadaAbierta(uId, vId, salida.puerta):
                continue

            nuevaDist = distanciaActual + salida.costo
            distV = distancias.obtener(vId)
            if distV is None or nuevaDist < distV:
                distancias.guardar(vId, nuevaDist)
                heap.empujar(nuevaDist, vId)

    return distancias


def elegirPasoViajeAutomatico(salaActual, salaDestino, salasIndice, mapaConocido):
    """Calcula el siguiente paso para el comando 'ir a' (§3.4).
    
    Devuelve (salidaElegida, costoSalida).
    Si ya está en destino, devuelve (None, 0).
    Si no hay ruta conocida abierta hacia el destino, devuelve (None, None).
    """
    if salaActual.id == salaDestino.id:
        return (None, 0)

    distancias = dijkstraSubgrafoConocido(salaDestino, salasIndice, mapaConocido)
    if distancias is None:
        return (None, None)

    d = distancias.obtener(salaActual.id)
    if d is None:
        return (None, None)

    mejorSalida = None
    mejorIdDestino = None

    for salida in salaActual.salidas:
        vId = salida.destinoId
        if not mapaConocido.estaExplorada(vId):
            continue
        if not mapaConocido.puertaRecordadaAbierta(salaActual.id, vId, salida.puerta):
            continue

        distV = distancias.obtener(vId)
        if distV is not None and (salida.costo + distV == d):
            if mejorIdDestino is None or vId < mejorIdDestino:
                mejorIdDestino = vId
                mejorSalida = salida

    if mejorSalida is not None:
        return (mejorSalida, mejorSalida.costo)

    return (None, None)


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


class Distancias:
    """Resultado de una búsqueda: costo mínimo de cada sala al origen (plan 005, D2 y D3).

    Por ahora guarda las distancias en una Tabla; el arreglo con sellos (T005) la reemplaza por
    dentro sin cambiar esta interfaz. Toda lectura pasa por `de()`.
    """

    def __init__(self, cota=None):
        self._valores = Tabla()
        self.cota = cota
        self.salasExaminadas = 0       # salas extraídas y expandidas (para medir PR-010)

    def de(self, sala):
        """Distancia de `sala` al origen, o None si es desconocida.

        Un valor mayor que la cota también es desconocido: por la eliminación perezosa, al
        cortar la búsqueda pueden quedar valores provisionales que no son la distancia real.
        """
        valor = self._valores.obtener(sala.id)
        if valor is None:
            return None
        if self.cota is not None and valor > self.cota:
            return None
        return valor

    def __len__(self):
        """Salas con algún valor registrado (definitivo o provisional)."""
        return len(self._valores)


def calcularDistancias(origen, puedeUsar, cota=None, cantidadSalas=None):
    """Dijkstra con montículo propio y eliminación perezosa (plan 005, D1).

    origen: Sala desde la que se mide.
    puedeUsar(sala, salida) -> bool: decide si la búsqueda puede usar esa salida.
    cota: si no es None, la búsqueda se detiene al extraer una distancia mayor (D2, PR-010).
    cantidadSalas: reservado para el arreglo con sellos (T005); hoy no se usa.

    Recorre con `salida.destino`, sin buscar salas por id en el índice. Complejidad
    O((V + E) log E) sobre las V salas y E salidas que quedan dentro de la cota.
    """
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
    return distancias


def elegirPrimerPaso(sala, distancias, puedeUsar):
    d = distancias.de(sala)
    if d is None:
        return None
    mejor = None
    for salida in sala.salidas:
        if not puedeUsar(sala, salida):
            continue
        v = salida.destino
        if v is None:
            continue
        dv = distancias.de(v)
        if dv is None or salida.costo + dv != d:
            continue
        # Se reemplaza solo si es estrictamente mejor, así gana la primera en orden N, S, E, O
        if (mejor is None or v.id < mejor.destino.id
                or (v.id == mejor.destino.id and salida.costo < mejor.costo)):
            mejor = salida
    return mejor
