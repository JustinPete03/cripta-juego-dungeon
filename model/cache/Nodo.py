class Nodo:
    def __init__(self, idFicha, ficha):
        self.idFicha = idFicha
        self.ficha = ficha
        self.referencias = 0
        self.anterior = None
        self.siguiente = None
        self.enDisco = False
