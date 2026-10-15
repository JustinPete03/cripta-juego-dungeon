#Agenda de eventos: heap binario propio sobre list, con eliminación perezosa.

#Orden total: (tiempo, seq). Cancelar es O(1). Cada operación que cambia la agenda
#informa su inversa al registrador, de modo que el retroceso no necesita copias.


class Evento:
    def __init__(self, tiempo, tipo, propietario, datos=None):
        self.tiempo = tiempo
        self.seq = -1
        self.tipo = tipo
        self.propietario = propietario
        self.datos = datos
        self.cancelado = False


class Agenda:
    def __init__(self, registrador=None):
        self._heap = []
        self._siguienteSeq = 0
        self._registrador = registrador   # desacer o  None

    #  heap
    def _menor(self, a, b):
        if a.tiempo != b.tiempo:
            return a.tiempo < b.tiempo
        return a.seq < b.seq

    def _subir(self, i):
        heap = self._heap
        while i > 0:
            padre = (i - 1) // 2
            if self._menor(heap[i], heap[padre]):
                heap[i], heap[padre] = heap[padre], heap[i]
                i = padre
            else:
                break

    def _bajar(self, i):
        heap = self._heap
        n = len(heap)
        while True:
            izq = 2 * i + 1
            der = 2 * i + 2
            menor = i
            if izq < n and self._menor(heap[izq], heap[menor]):
                menor = izq
            if der < n and self._menor(heap[der], heap[menor]):
                menor = der
            if menor == i:
                break
            heap[i], heap[menor] = heap[menor], heap[i]
            i = menor

    def _empujar(self, evento):
        self._heap.append(evento)
        self._subir(len(self._heap) - 1)

    def _sacarRaiz(self):
        heap = self._heap
        raiz = heap[0]
        ultimo = heap.pop()
        if len(heap) > 0:
            heap[0] = ultimo
            self._bajar(0)
        return raiz

    #registro de inversas
    def _registrar(self, deshacer):
        if self._registrador is not None:
            self._registrador(deshacer)

    def _registrarReinsercion(self, evento):
        def deshacer():
            self._empujar(evento)
        self._registrar(deshacer)

    #operaciones
    def programar(self, tiempo, tipo, propietario, datos=None):
        #Crea un evento con número de secuencia nuevo.
        evento = Evento(tiempo, tipo, propietario, datos)
        evento.seq = self._siguienteSeq
        self._siguienteSeq += 1
        self._empujar(evento)

        def deshacer():
            evento.cancelado = True   # queda en el heap y se descarta al salir
        self._registrar(deshacer)
        return evento

    def cancelar(self, evento):
        #O(1): solo marca. Cancelar un evento ya cancelado no hace nada.
        if evento.cancelado:
            return

        evento.cancelado = True

        def deshacer():
            evento.cancelado = False
        self._registrar(deshacer)

    def reprogramar(self, evento, nuevoTiempo):
        #Cancela el evento y crea otro con seq nuevo. Devuelve el nuevo.
        self.cancelar(evento)
        return self.programar(nuevoTiempo, evento.tipo, evento.propietario, evento.datos)

    def proximo(self):
        #Saca y devuelve el siguiente evento válido, o None. Descarta cancelados.
        while len(self._heap) > 0:
            evento = self._sacarRaiz()
            self._registrarReinsercion(evento)
            if evento.cancelado:
                continue
            return evento
        return None
    def secuencia(self):
        return self._siguienteSeq

    def restaurarSecuencia(self, valor):
        # Solo lo usa el retroceso
        self._siguienteSeq = valor
    # consultas
    def tamano(self):
        return len(self._heap)

    def pendientesValidos(self):
        resultado = []
        for evento in self._heap:
            if not evento.cancelado:
                resultado.append(evento)
        return resultado