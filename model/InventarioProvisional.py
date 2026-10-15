# Inventario PROVISIONAL, solo para poder probar el motor. Jorge lo reemplaza por el suyo
# (4.5) respetando modelo/interfaces.py: mutar solo con modelo.asignar/agregarA/quitarDe.
from model.Constantes import ACC_RECOGER, ACC_SOLTAR
from model.Interfaces import InventarioBase, Resultado


class InventarioProvisional(InventarioBase):
    def __init__(self):
        self.capacidad = 0
        self.lista = []
        self.cursor = 0

    def configurar(self, capacidad):
        self.capacidad = capacidad

    def objetos(self):
        return self.lista

    def actual(self):
        if len(self.lista) == 0:
            return None
        return self.lista[self.cursor]

    def avanzar(self):
        if len(self.lista) > 0:
            self.cursor = (self.cursor + 1) % len(self.lista)

    def retroceder(self):
        if len(self.lista) > 0:
            self.cursor = (self.cursor - 1) % len(self.lista)

    def tieneLlave(self, llaveId):
        for objeto in self.lista:
            if objeto.tipoId == llaveId:
                return True
        return False

    def validar(self, modelo, accion):
        if accion.tipo == ACC_RECOGER:
            sala = modelo.jugador.sala
            if accion.argumento < 0 or accion.argumento >= len(sala.objetos):
                return Resultado(False, "No hay ese objeto en el suelo.")
            if len(self.lista) >= self.capacidad:
                return Resultado(False, "Inventario lleno: suelta algo primero.")
            return Resultado(True)
        if accion.tipo == ACC_SOLTAR:
            if len(self.lista) == 0:
                return Resultado(False, "No tienes objetos.")
            return Resultado(True)
        return Resultado(False, "Esa acción la implementa el inventario de Jorge.")

    def aplicar(self, modelo, accion):
        sala = modelo.jugador.sala
        if accion.tipo == ACC_RECOGER:
            objeto = sala.objetos[accion.argumento]
            modelo.quitarDe(sala.objetos, objeto)
            modelo.agregarA(self.lista, objeto)
            modelo.mensaje("Recoges: %s." % modelo.nombreDe(objeto.tipoId))
        elif accion.tipo == ACC_SOLTAR:
            objeto = self.lista[self.cursor]
            modelo.quitarDe(self.lista, objeto)
            modelo.agregarA(sala.objetos, objeto)
            nuevo = min(self.cursor, max(0, len(self.lista) - 1))
            modelo.asignar(self, "cursor", nuevo)
            modelo.mensaje("Sueltas: %s." % modelo.nombreDe(objeto.tipoId))