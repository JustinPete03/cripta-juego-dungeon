#Bitácora en pantalla: arreglo circular de tamaño fijo. Memoria constante.


class BitacoraCircular:
    def __init__(self, capacidad=20):
        self._capacidad = capacidad
        self._mensajes = [None] * capacidad
        self._siguiente = 0
        self._cantidad = 0

    def agregar(self, mensaje):
        self._mensajes[self._siguiente] = mensaje
        self._siguiente = (self._siguiente + 1) % self._capacidad
        if self._cantidad < self._capacidad:
            self._cantidad += 1

    def ultimos(self):
       #Del más antiguo al más reciente.
        resultado = []
        inicio = (self._siguiente - self._cantidad) % self._capacidad
        for i in range(self._cantidad):
            resultado.append(self._mensajes[(inicio + i) % self._capacidad])
        return resultado
