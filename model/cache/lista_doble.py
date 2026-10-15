from model.cache import nodo


class ListaDoble:
    def __init__(self):
        self.primero = None
        self.ultimo = None
        self.tamanio = 0

    def agregar_al_frente(self,nodo):
        nodo.anterior = None
        nodo.siguiente = self.primero
        if self.primero is not None:
            self.primero.anterior = nodo
        else:
            self.ultimo = nodo
        self.primero = nodo
        self.tamanio += 1

    def quitar(self,nodo):
        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente
        else:
            self.primero = nodo.siguiente
        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior
        else:
            self.ultimo = nodo.anterior
        nodo.anterior = None
        nodo.siguiente = None
        self.tamanio -= 1

    def mover_al_frente(self,nodo):
        if nodo is self.primero:
            return
        self.quitar(nodo)
        self.agregar_al_frente(nodo)

