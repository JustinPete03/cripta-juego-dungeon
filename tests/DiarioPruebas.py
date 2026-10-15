#Diario de prueba: guarda TODOS los intervalos (sin tope de 5) para verificar la reversibilidad.
from model.Interfaces import DiarioBase, Resultado


class DiarioPrueba(DiarioBase):
    activo = True

    def __init__(self):
        self.intervalos = []
        self.actual = None

    def abrirIntervalo(self):
        self.actual = []

    def registrar(self, deshacer):
        self.actual.append(deshacer)

    def cerrarIntervalo(self):
        self.intervalos.append(self.actual)
        self.actual = None

    def retroceder(self, modelo):
        if len(self.intervalos) == 0:
            return Resultado(False, "Nada que retroceder.")
        intervalo = self.intervalos.pop()
        i = len(intervalo) - 1
        while i >= 0:
            intervalo[i]()
            i -= 1
        return Resultado(True)
