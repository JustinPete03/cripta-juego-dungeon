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
