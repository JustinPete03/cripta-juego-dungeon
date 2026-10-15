#Índice de salas por id: arreglo ordenado con búsqueda binaria.

class IndiceOrdenado:
    def __init__(self):
        self._claves = []
        self._valores = []

    def _posicion(self, clave):
        bajo = 0
        alto = len(self._claves)
        while bajo < alto:
            medio = (bajo + alto) // 2
            if self._claves[medio] < clave:
                bajo = medio + 1
            else:
                alto = medio
        return bajo

    def insertar(self, clave, valor):
        pos = self._posicion(clave)
        if pos < len(self._claves) and self._claves[pos] == clave:
            raise ValueError("Id duplicado en el esqueleto: %s" % (clave,))
        self._claves.insert(pos, clave)
        self._valores.insert(pos, valor)

    def buscar(self, clave):
        pos = self._posicion(clave)
        if pos < len(self._claves) and self._claves[pos] == clave:
            return self._valores[pos]
        return None

    def cantidad(self):
        return len(self._claves)

    def enPosicion(self, i):
        return self._valores[i]
