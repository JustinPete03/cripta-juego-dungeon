from model.Interfaces import DiarioBase, Resultado


class Diario(DiarioBase):
    activo = True
    CAPACIDAD = 5

    def __init__(self):
        self.intervalos = []
        self.actual = None

    def abrirIntervalo(self):
        self.actual = []

    def registrar(self, deshacer):
        if self.actual is not None:
            self.actual.append(deshacer)

    def cerrarIntervalo(self):
        if self.actual is None:
            return
        if len(self.intervalos) == self.CAPACIDAD:
            for i in range(1, self.CAPACIDAD):
                self.intervalos[i - 1] = self.intervalos[i]
            self.intervalos.pop()
        self.intervalos.append(self.actual)
        self.actual = None

    def retroceder(self, modelo):
        if len(self.intervalos) == 0:
            return Resultado(False, "No hay acciones que retroceder.")
        pergamino = modelo.inventario.buscarPergamino()
        if pergamino is None:
            return Resultado(False, "No tienes un pergamino de retroceso.")
        intervalo = self.intervalos.pop()
        while len(intervalo) > 0:
            intervalo.pop()()
        modelo.inventario.consumirPergamino(pergamino)
        return Resultado(True)