"""Historial de retroceso (§4.6): pila de intervalos (tope 5), cada uno con una pila de registros."""


class RegistroAtributo:
    """Sirve para vida, reloj, rastro, estado de puerta/trampa, sala, etc.
    Guarda el valor ANTERIOR de objeto.nombre."""
    def __init__(self, objeto, nombre, valor_anterior):
        self.objeto, self.nombre, self.valor = objeto, nombre, valor_anterior

    def deshacer(self, modelo):
        setattr(self.objeto, self.nombre, self.valor)


class Intervalo:
    def __init__(self):
        self.registros = []            # list usada como pila

    def registrar(self, registro):
        self.registros.append(registro)

    def revertir(self, modelo):
        while self.registros:
            self.registros.pop().deshacer(modelo)   # orden inverso (LIFO)


class Historial:
    CAP = 5

    def __init__(self):
        self.intervalos = []

    def abrir(self):
        """Llamar cuando el jugador CONFIRMA una acción que consume tiempo."""
        if len(self.intervalos) == self.CAP:
            for i in range(1, self.CAP):                # descarta el más antiguo
                self.intervalos[i - 1] = self.intervalos[i]
            self.intervalos.pop()
        self.intervalos.append(Intervalo())

    def registrar(self, registro):
        """Todas las mutaciones del modelo pasan por aquí."""
        if self.intervalos:
            self.intervalos[-1].registrar(registro)

    def puede_deshacer(self):
        return len(self.intervalos) > 0

    def deshacer(self, modelo):
        if not self.intervalos:
            return False
        self.intervalos.pop().revertir(modelo)
        return True