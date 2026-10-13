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
