"""Inventario (§4.5): lista doblemente enlazada propia. Sin dict, sin list.sort()."""


class Nodo:
    __slots__ = ("item", "ant", "sig", "enlazado")

    def __init__(self, item):
        self.item = item      # instancia de objeto; item.ficha apunta a la ficha del catálogo
        self.ant = None
        self.sig = None
        self.enlazado = False


def _es_pergamino(item):
    return getattr(item.ficha, "clase", None) == "pergamino_retroceso"


def ordenar_insercion(lista, clave):
    """Provisional. Sustituir por el selector de ordenamientos de Keilor (§4.9)."""
    for i in range(1, len(lista)):
        x = lista[i]
        kx = clave(x)
        j = i - 1
        while j >= 0 and clave(lista[j]) > kx:
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = x


# ---------- registros de deshacer (cada uno sabe invertirse) ----------

class RegistroRecoger:
    def __init__(self, inv, nodo):
        self.inv, self.nodo = inv, nodo

    def deshacer(self, modelo=None):
        self.inv._desenlazar(self.nodo)


class RegistroSoltar:
    def __init__(self, inv, nodo, ant, arma, armadura):
        self.inv, self.nodo, self.ant = inv, nodo, ant
        self.arma, self.armadura = arma, armadura

    def deshacer(self, modelo=None):
        inv = self.inv
        inv._enlazar_despues(self.nodo, self.ant)   # puede exceder capacidad (ver regla)
        inv.arma, inv.armadura = self.arma, self.armadura
        inv.cursor = self.nodo


class RegistroEquipar:
    def __init__(self, inv, nodo, ant, arma, armadura):
        self.inv, self.nodo, self.ant = inv, nodo, ant
        self.arma, self.armadura = arma, armadura

    def deshacer(self, modelo=None):
        inv = self.inv
        inv._desenlazar(self.nodo)
        inv._enlazar_despues(self.nodo, self.ant)
        inv.arma, inv.armadura = self.arma, self.armadura


class Inventario:
    def __init__(self, capacidad, registrar=None):
        self.capacidad = capacidad
        self.registrar = registrar     # función(registro) del historial, o None
        self.cabeza = None
        self.cola = None
        self.cursor = None
        self.tamano = 0
        self.arma = None               # Nodo equipado
        self.armadura = None           # Nodo equipado

    # ---- enlaces de bajo nivel, O(1) ----
    def _enlazar_despues(self, nodo, ant):
        """Inserta nodo después de ant; si ant es None o ya no está enlazado, al frente."""
        if ant is None or not ant.enlazado:
            nodo.ant, nodo.sig = None, self.cabeza
            if self.cabeza:
                self.cabeza.ant = nodo
            else:
                self.cola = nodo
            self.cabeza = nodo
        else:
            nodo.ant, nodo.sig = ant, ant.sig
            if ant.sig:
                ant.sig.ant = nodo
            else:
                self.cola = nodo
            ant.sig = nodo
        nodo.enlazado = True
        self.tamano += 1
        if self.cursor is None:
            self.cursor = nodo

    def _desenlazar(self, nodo):
        if nodo.ant:
            nodo.ant.sig = nodo.sig
        else:
            self.cabeza = nodo.sig
        if nodo.sig:
            nodo.sig.ant = nodo.ant
        else:
            self.cola = nodo.ant
        if self.cursor is nodo:
            self.cursor = nodo.sig or nodo.ant
        if self.arma is nodo:
            self.arma = None
        if self.armadura is nodo:
            self.armadura = None
        nodo.ant = nodo.sig = None
        nodo.enlazado = False
        self.tamano -= 1

    def _reg(self, item, registro):
        # Los pergaminos de retroceso quedan fuera del historial (§2.11)
        if self.registrar and not _es_pergamino(item):
            self.registrar(registro)

    # ---- operaciones del juego ----
    def lleno(self):
        return self.tamano >= self.capacidad

    def recoger(self, item):
        """False si está lleno: no ejecuta ni consume tiempo (Apéndice B)."""
        if self.lleno():
            return False
        nodo = Nodo(item)
        self._enlazar_despues(nodo, self.cola)
        self._reg(item, RegistroRecoger(self, nodo))
        return True

    def soltar_actual(self):
        """Suelta el objeto bajo el cursor. O(1). Devuelve el item o None."""
        nodo = self.cursor
        if nodo is None:
            return None
        reg = RegistroSoltar(self, nodo, nodo.ant, self.arma, self.armadura)
        self._desenlazar(nodo)
        self._reg(nodo.item, reg)
        return nodo.item

    def equipar_actual(self):
        """Mueve al frente y equipa. Solo arma o armadura. O(1)."""
        nodo = self.cursor
        if nodo is None:
            return False
        clase = getattr(nodo.item.ficha, "clase", None)
        if clase not in ("arma", "armadura"):
            return False
        reg = RegistroEquipar(self, nodo, nodo.ant, self.arma, self.armadura)
        self._desenlazar(nodo)
        self._enlazar_despues(nodo, None)
        if clase == "arma":
            self.arma = nodo
        else:
            self.armadura = nodo
        self._reg(nodo.item, reg)
        return True

    def siguiente(self):
        if self.cursor and self.cursor.sig:
            self.cursor = self.cursor.sig

    def anterior(self):
        if self.cursor and self.cursor.ant:
            self.cursor = self.cursor.ant

    def ataque_bonus(self):
        return getattr(self.arma.item.ficha, "ataque_bonus", 0) if self.arma else 0

    def defensa_bonus(self):
        return getattr(self.armadura.item.ficha, "defensa_bonus", 0) if self.armadura else 0

    # ---- vistas ----
    def items(self):
        n, out = self.cabeza, []
        while n:
            out.append(n.item)
            n = n.sig
        return out

    def vista_ordenada(self, clave, ordenar=ordenar_insercion):
        lista = self.items()
        ordenar(lista, lambda it: clave(it.ficha))
        return lista