#Bitácora en pantalla: arreglo circular de tamaño fijo. Memoria constante.


class BitacoraCircular:
    def __init__(self, capacidad=20):
        self._capacidad = capacidad
        self._mensajes = [None] * capacidad
        self._siguiente = 0
        self._cantidad = 0
        self._total = 0

    def agregar(self, mensaje):
        self._mensajes[self._siguiente] = mensaje
        self._siguiente = (self._siguiente + 1) % self._capacidad
        if self._cantidad < self._capacidad:
            self._cantidad += 1
        self._total += 1

    def total(self):
        """Mensajes acumulados desde el inicio de la partida (la ventana circular pierde los antiguos)."""
        return self._total

    def reponerTotal(self, valor):
        #Al cargar una partida se reconstruye la ventana y el contador viene en el archivo.
        self._total = valor

    def capacidad(self):
        return self._capacidad

    def ultimos(self):
       #Del más antiguo al más reciente.
        resultado = []
        inicio = (self._siguiente - self._cantidad) % self._capacidad
        for i in range(self._cantidad):
            resultado.append(self._mensajes[(inicio + i) % self._capacidad])
        return resultado
