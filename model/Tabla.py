# Tabla hash propia (sección 4.4 y restricción 7).
#
# El proyecto no puede usar dict como índice ni como caché, así que las búsquedas por clave del
# modelo y de los adaptadores viven aquí: cubetas con encadenamiento, factor de carga que
# redimensiona y hash djb2 sobre la representación de la clave, el mismo esquema de la caché de
# fichas para que el formato de las claves sea idéntico en los dos sitios.

CUBETAS_INICIALES = 31
FACTOR_DE_CARGA = 0.75


def _hash(clave):
    crudo = str(clave)
    valor = 5381
    for caracter in crudo:
        valor = ((valor * 33) + ord(caracter)) & 0x7FFFFFFF
    return valor


class _Nodo:
    __slots__ = ("clave", "valor", "siguiente")

    def __init__(self, clave, valor, siguiente):
        self.clave = clave
        self.valor = valor
        self.siguiente = siguiente


class Tabla:
    def __init__(self, cubetas=CUBETAS_INICIALES):
        self._cubetas = [None] * cubetas
        self._cantidad = 0

    def __len__(self):
        return self._cantidad

    def _posicion(self, clave):
        return _hash(clave) % len(self._cubetas)

    def _buscar(self, clave):
        nodo = self._cubetas[self._posicion(clave)]
        while nodo is not None:
            if nodo.clave == clave:
                return nodo
            nodo = nodo.siguiente
        return None

    def guardar(self, clave, valor):
        pos = self._posicion(clave)
        nodo = self._cubetas[pos]
        while nodo is not None:
            if nodo.clave == clave:
                nodo.valor = valor
                return
            nodo = nodo.siguiente
        self._cubetas[pos] = _Nodo(clave, valor, self._cubetas[pos])
        self._cantidad += 1
        if self._cantidad > len(self._cubetas) * FACTOR_DE_CARGA:
            self._redimensionar()

    def obtener(self, clave, porDefecto=None):
        nodo = self._buscar(clave)
        return porDefecto if nodo is None else nodo.valor

    def contiene(self, clave):
        return self._buscar(clave) is not None

    def quitar(self, clave):
        pos = self._posicion(clave)
        anterior = None
        nodo = self._cubetas[pos]
        while nodo is not None:
            if nodo.clave == clave:
                if anterior is None:
                    self._cubetas[pos] = nodo.siguiente
                else:
                    anterior.siguiente = nodo.siguiente
                self._cantidad -= 1
                return nodo.valor
            anterior = nodo
            nodo = nodo.siguiente
        return None

    def claves(self):
        salida = []
        for cabeza in self._cubetas:
            nodo = cabeza
            while nodo is not None:
                salida.append(nodo.clave)
                nodo = nodo.siguiente
        return salida

    def items(self):
        salida = []
        for cabeza in self._cubetas:
            nodo = cabeza
            while nodo is not None:
                salida.append((nodo.clave, nodo.valor))
                nodo = nodo.siguiente
        return salida

    def _redimensionar(self):
        viejas = self._cubetas
        self._cubetas = [None] * (2 * len(viejas) + 1)
        self._cantidad = 0
        for cabeza in viejas:
            nodo = cabeza
            while nodo is not None:
                siguiente = nodo.siguiente
                self.guardar(nodo.clave, nodo.valor)
                nodo = siguiente


class Conjunto:
    """Conjunto propio sobre la misma tabla: sirve para '¿ya vi esta puerta?'."""

    def __init__(self):
        self._tabla = Tabla()

    def __len__(self):
        return len(self._tabla)

    def agregar(self, clave):
        self._tabla.guardar(clave, True)

    def contiene(self, clave):
        return self._tabla.contiene(clave)
