class Nodo:
    def __init__(self, id_ficha, ficha):
        self.id_ficha = id_ficha
        self.ficha = ficha
        self.referencias = 0
        self.anterior = None
        self.siguiente = None
