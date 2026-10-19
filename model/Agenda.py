#Agenda de eventos: heap binario propio sobre list, con eliminación perezosa.

#Orden total: (tiempo, seq). Cancelar es O(1). Cada operación que cambia la agenda
#informa su inversa al registrador, de modo que el retroceso no necesita copias.
#
#El montículo guarda tuplas (tiempo, seq, serie, evento) en lugar de objetos: comparar tuplas de
#enteros resuelve en C y, con cientos de enemigos activos, estas comparaciones se hacen miles de
#veces por ciclo (sección 5.2). La serie es única por empujón y desempata cuando el retroceso
#reutiliza un seq: sin ella la comparación caería sobre los objetos Evento y no tienen orden.
#Las closures de la inversa solo se crean cuando hay registrador: crearlas siempre costaba más que
#el trabajo de la propia agenda.


class Evento:
    __slots__ = ("tiempo", "seq", "tipo", "propietario", "datos", "cancelado")

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
        self._serie = 0                # desempate único por empujón; el retroceso no lo rewinda
        self._registrador = registrador   # deshacer o None

    #  heap
    def _subir(self, i):
        heap = self._heap
        entrada = heap[i]
        while i > 0:
            padre = (i - 1) // 2
            if entrada < heap[padre]:
                heap[i] = heap[padre]
                i = padre
            else:
                break
        heap[i] = entrada

    def _bajar(self, i):
        heap = self._heap
        n = len(heap)
        entrada = heap[i]
        while True:
            izq = 2 * i + 1
            if izq >= n:
                break
            hijo = heap[izq]
            der = izq + 1
            if der < n and heap[der] < hijo:
                hijo = heap[der]
                izq = der
            if hijo >= entrada:
                break
            heap[i] = hijo
            i = izq
        heap[i] = entrada

    def _empujar(self, entrada):
        self._heap.append(entrada)
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

    #operaciones
    def programar(self, tiempo, tipo, propietario, datos=None):
        #Crea un evento con número de secuencia nuevo.
        evento = Evento(tiempo, tipo, propietario, datos)
        seq = self._siguienteSeq
        evento.seq = seq
        self._siguienteSeq = seq + 1
        self._serie += 1
        self._empujar((tiempo, seq, self._serie, evento))

        if self._registrador is not None:
            def deshacer():
                evento.cancelado = True   # queda en el heap y se descarta al salir
            self._registrar(deshacer)
        return evento

    def cancelar(self, evento):
        #O(1): solo marca. Cancelar un evento ya cancelado no hace nada.
        if evento.cancelado:
            return
        evento.cancelado = True

        if self._registrador is not None:
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
            entrada = self._sacarRaiz()
            if self._registrador is not None:
                def deshacer(entrada=entrada):
                    self._empujar(entrada)
                self._registrar(deshacer)
            evento = entrada[-1]
            if evento.cancelado:
                continue
            return evento
        return None

    def secuencia(self):
        return self._siguienteSeq

    def reconstruir(self, eventos, secuencia):
        #Rearma el heap desde cero al cargar una partida. No informa inversas: no hay nada
        #que deshacer, el estado anterior se descarta entero.
        self._heap = []
        for evento in eventos:
            self._serie += 1
            self._empujar((evento.tiempo, evento.seq, self._serie, evento))
        self._siguienteSeq = secuencia

    def restaurarSecuencia(self, valor):
        # Solo lo usa el retroceso
        self._siguienteSeq = valor

    # consultas
    def tamano(self):
        return len(self._heap)

    def pendientesValidos(self):
        resultado = []
        for entrada in self._heap:
            evento = entrada[-1]
            if not evento.cancelado:
                resultado.append(evento)
        return resultado
