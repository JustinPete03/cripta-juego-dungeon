from model.Constantes import ACC_RECOGER, ACC_USAR, ACC_EQUIPAR, ACC_SOLTAR
from model.Interfaces import InventarioBase, Resultado

CLASE_PERGAMINO = "pergamino_retroceso"


class Nodo:
    __slots__ = ("objeto", "ant", "sig", "enlazado")

    def __init__(self, objeto):
        self.objeto = objeto
        self.ant = None
        self.sig = None
        self.enlazado = False


def ordenarInsercion(lista, clave):
    for i in range(1, len(lista)):
        x = lista[i]
        kx = clave(x)
        j = i - 1
        while j >= 0 and clave(lista[j]) > kx:
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = x


class Inventario(InventarioBase):
    def __init__(self, proveedor, ordenar=None):
        self.proveedor = proveedor
        self._ordenar = ordenar if ordenar is not None else ordenarInsercion
        self.capacidad = 0
        self.cabeza = None
        self.cola = None
        self.cursor = None
        self.tamano = 0
        self.arma = None
        self.armadura = None

    def configurar(self, capacidad):
        self.capacidad = capacidad

    def _enlazarDespues(self, nodo, ant):
        if ant is None or not ant.enlazado:
            nodo.ant = None
            nodo.sig = self.cabeza
            if self.cabeza is not None:
                self.cabeza.ant = nodo
            else:
                self.cola = nodo
            self.cabeza = nodo
        else:
            nodo.ant = ant
            nodo.sig = ant.sig
            if ant.sig is not None:
                ant.sig.ant = nodo
            else:
                self.cola = nodo
            ant.sig = nodo
        nodo.enlazado = True
        self.tamano += 1
        if self.cursor is None:
            self.cursor = nodo

    def _desenlazar(self, nodo):
        if nodo.ant is not None:
            nodo.ant.sig = nodo.sig
        else:
            self.cabeza = nodo.sig
        if nodo.sig is not None:
            nodo.sig.ant = nodo.ant
        else:
            self.cola = nodo.ant
        if self.cursor is nodo:
            self.cursor = nodo.sig if nodo.sig is not None else nodo.ant
        nodo.ant = None
        nodo.sig = None
        nodo.enlazado = False
        self.tamano -= 1

    def _ficha(self, objeto):
        return self.proveedor.ficha(objeto.tipoId)

    def _esPergamino(self, objeto):
        return self._ficha(objeto).get("clase") == CLASE_PERGAMINO

    def _quitarRegistrando(self, modelo, nodo):
        ant = nodo.ant
        self._desenlazar(nodo)

        def deshacer():
            self._enlazarDespues(nodo, ant)
            self.cursor = nodo

        modelo.diario.registrar(deshacer)

    def objetos(self):
        resultado = []
        nodo = self.cabeza
        while nodo is not None:
            resultado.append(nodo.objeto)
            nodo = nodo.sig
        return resultado

    def actual(self):
        return self.cursor.objeto if self.cursor is not None else None

    def avanzar(self):
        if self.cursor is not None:
            self.cursor = self.cursor.sig if self.cursor.sig is not None else self.cabeza

    def retroceder(self):
        if self.cursor is not None:
            self.cursor = self.cursor.ant if self.cursor.ant is not None else self.cola

    def tieneLlave(self, llaveId):
        nodo = self.cabeza
        while nodo is not None:
            if nodo.objeto.tipoId == llaveId:
                return True
            nodo = nodo.sig
        return False

    def validar(self, modelo, accion):
        tipo = accion.tipo
        if tipo == ACC_RECOGER:
            sala = modelo.jugador.sala
            if accion.argumento < 0 or accion.argumento >= len(sala.objetos):
                return Resultado(False, "No hay ese objeto en el suelo.")
            if self.tamano >= self.capacidad:
                return Resultado(False, "Inventario lleno: suelta algo primero.")
            return Resultado(True)
        if self.cursor is None:
            return Resultado(False, "No tienes objetos.")
        if tipo == ACC_SOLTAR:
            return Resultado(True)
        clase = self._ficha(self.cursor.objeto).get("clase")
        if tipo == ACC_EQUIPAR:
            if clase in ("arma", "armadura"):
                return Resultado(True)
            return Resultado(False, "Ese objeto no se puede equipar.")
        if tipo == ACC_USAR:
            if clase in ("pocion", "antidoto", "antorcha"):
                return Resultado(True)
            if clase == CLASE_PERGAMINO:
                return Resultado(False, "Para usar el pergamino escribe 'retroceso'.")
            if clase == "llave":
                return Resultado(False, "La llave se usa al abrir una puerta.")
            return Resultado(False, "Ese objeto se equipa con 'equipar'.")
        return Resultado(False, "Acción de inventario desconocida.")

    def aplicar(self, modelo, accion):
        if accion.tipo == ACC_RECOGER:
            self._recoger(modelo, accion.argumento)
        elif accion.tipo == ACC_SOLTAR:
            self._soltar(modelo)
        elif accion.tipo == ACC_EQUIPAR:
            self._equipar(modelo)
        elif accion.tipo == ACC_USAR:
            self._usar(modelo)

    def _recoger(self, modelo, indice):
        sala = modelo.jugador.sala
        objeto = sala.objetos[indice]
        nodo = Nodo(objeto)
        if self._esPergamino(objeto):
            del sala.objetos[indice]
            self._enlazarDespues(nodo, self.cola)
        else:
            modelo.quitarDe(sala.objetos, objeto)
            self._enlazarDespues(nodo, self.cola)

            def deshacer():
                self._desenlazar(nodo)

            modelo.diario.registrar(deshacer)
        modelo.mensaje("Recoges: %s." % modelo.nombreDe(objeto.tipoId))

    def _soltar(self, modelo):
        nodo = self.cursor
        objeto = nodo.objeto
        sala = modelo.jugador.sala
        if self._esPergamino(objeto):
            self._desenlazar(nodo)
            sala.objetos.append(objeto)
        else:
            self._desequipar(modelo, nodo)
            self._quitarRegistrando(modelo, nodo)
            modelo.agregarA(sala.objetos, objeto)
        modelo.mensaje("Sueltas: %s." % modelo.nombreDe(objeto.tipoId))

    def _desequipar(self, modelo, nodo):
        if nodo is self.arma:
            modelo.asignar(self, "arma", None)
            modelo.asignar(modelo.jugador, "bonoAtaque", 0)
        if nodo is self.armadura:
            modelo.asignar(self, "armadura", None)
            modelo.asignar(modelo.jugador, "bonoDefensa", 0)

    def _equipar(self, modelo):
        nodo = self.cursor
        ficha = self._ficha(nodo.objeto)
        ant = nodo.ant
        if ficha["clase"] == "arma":
            modelo.asignar(self, "arma", nodo)
            modelo.asignar(modelo.jugador, "bonoAtaque", ficha.get("ataque_bonus", 0))
        else:
            modelo.asignar(self, "armadura", nodo)
            modelo.asignar(modelo.jugador, "bonoDefensa", ficha.get("defensa_bonus", 0))
        self._desenlazar(nodo)
        self._enlazarDespues(nodo, None)
        self.cursor = nodo

        def deshacer():
            self._desenlazar(nodo)
            self._enlazarDespues(nodo, ant)
            self.cursor = nodo

        modelo.diario.registrar(deshacer)
        modelo.mensaje("Equipas: %s." % modelo.nombreDe(nodo.objeto.tipoId))

    def _usar(self, modelo):
        nodo = self.cursor
        ficha = self._ficha(nodo.objeto)
        if ficha["clase"] == "pocion" and "cura" in ficha:
            modelo.curar(modelo.jugador, ficha["cura"])
        modelo.efectos.alUsarObjeto(modelo, ficha)
        self._quitarRegistrando(modelo, nodo)
        modelo.mensaje("Usas: %s." % ficha["nombre"])

    def buscarPergamino(self):
        nodo = self.cabeza
        while nodo is not None:
            if self._esPergamino(nodo.objeto):
                return nodo
            nodo = nodo.sig
        return None

    def consumirPergamino(self, nodo):
        self._desenlazar(nodo)

    def vistaOrdenada(self, criterio):
        if criterio not in ("peso", "valor", "nombre"):
            raise ValueError("Criterio desconocido: %r (usa peso, valor o nombre)." % (criterio,))
        pares = []
        for objeto in self.objetos():
            ficha = self._ficha(objeto)
            clave = ficha["nombre"].lower() if criterio == "nombre" else ficha.get(criterio, 0)
            pares.append((clave, objeto))
        self._ordenar(pares, lambda par: par[0])
        resultado = []
        for _, objeto in pares:
            resultado.append(objeto)
        return resultado

    vista_ordenada = vistaOrdenada