# Formato binario propio de guardado (sección 4.10).
#
# Contenedor: los bloques van primero y al final quedan dos índices, uno por nombre para las
# secciones y otro ordenado por id de sala. Cada entrada es (posición, largo), así que cargar UNA
# sala cuesta leer el encabezado, ~log2(n) entradas del índice y ese único bloque: nunca el
# archivo completo.
#
# Los payloads usan codBinary (tag + cuerpo), no JSON ni compresores: el tamaño de cada bloque se
# conoce al escribirlo y se puede decodificar de forma aislada.
#
# guardadoPartida (la partida completa) vive sobre este mismo Contenedor, así que lo que mide el
# bench es exactamente lo que se envía en el juego.

import struct

from adapters.codBinary import codificar, decodificar

MAGIC = b"CRPT"
VERSION_FORMATO = 2

# magic, versión, n secciones, n salas, posición del índice de secciones, posición de la tabla de salas
ENCABEZADO = struct.Struct("<4sHHIQQ")
ENTRADA_SALA = struct.Struct("<IQI")     # salaId, posición, largo
LARGO_NOMBRE = struct.Struct("<H")       # los nombres de sección son ASCII
ENTRADA_SECCION = struct.Struct("<QI")   # posición, largo


def ordenarPorId(entradas):
    # Los ids ya vienen casi ordenados, así que inserción con búsqueda del hueco queda en O(n)
    # en la práctica y evita usar sorted() en el camino del guardado.
    orden = []
    for entrada in entradas:
        idLeido = entrada[0]
        pos = len(orden)
        while pos > 0 and orden[pos - 1][0] > idLeido:
            pos -= 1
        orden.insert(pos, entrada)
    return orden


class Contenedor:
    def __init__(self, magic=MAGIC, versionFormato=VERSION_FORMATO):
        self.magic = magic
        self.versionFormato = versionFormato

    # ------------------------------------------------------------------ escribir
    def guardar(self, ruta, secciones, salas):
        """secciones: [(nombre, datos)]; salas: [(salaId, datos)]. Devuelve el índice de salas."""
        with open(ruta, "wb") as archivo:
            archivo.write(b"\0" * ENCABEZADO.size)
            indiceSecciones = []
            for nombre, datos in secciones:
                bloque = codificar(datos)
                indiceSecciones.append((nombre, archivo.tell(), len(bloque)))
                archivo.write(bloque)
            indiceSalas = []
            for salaId, datos in salas:
                bloque = codificar(datos)
                indiceSalas.append((salaId, archivo.tell(), len(bloque)))
                archivo.write(bloque)

            posicionSecciones = archivo.tell()
            for nombre, posicion, largo in indiceSecciones:
                crudo = nombre.encode("ascii")
                archivo.write(LARGO_NOMBRE.pack(len(crudo)) + crudo
                              + ENTRADA_SECCION.pack(posicion, largo))
            orden = ordenarPorId(indiceSalas)
            posicionSalas = archivo.tell()
            for entrada in orden:
                archivo.write(ENTRADA_SALA.pack(*entrada))

            archivo.seek(0)
            archivo.write(ENCABEZADO.pack(self.magic, self.versionFormato, len(indiceSecciones),
                                          len(orden), posicionSecciones, posicionSalas))
        return orden

    # ------------------------------------------------------------------ leer
    def _encabezado(self, archivo):
        crudo = archivo.read(ENCABEZADO.size)
        if len(crudo) < ENCABEZADO.size:
            raise ValueError("Archivo de guardado incompleto.")
        magic, version, nSecciones, nSalas, posicionSecciones, posicionSalas = \
            ENCABEZADO.unpack(crudo)
        if magic != self.magic:
            raise ValueError("El archivo no es un guardado de CRIPTA.")
        if version != self.versionFormato:
            raise ValueError("Versi\u00f3n de formato incompatible: %d" % version)
        return nSecciones, nSalas, posicionSecciones, posicionSalas

    def _bytes(self, archivo, posicion, largo):
        archivo.seek(posicion)
        return archivo.read(largo)

    def _buscaSala(self, archivo, nSalas, posicionSalas, salaId):
        """Busqueda binaria sobre la tabla de salas: solo se leen las entradas visitadas."""
        bajo, alto = 0, nSalas - 1
        while bajo <= alto:
            medio = (bajo + alto) // 2
            idLeido, posicion, largo = ENTRADA_SALA.unpack(
                self._bytes(archivo, posicionSalas + medio * ENTRADA_SALA.size, ENTRADA_SALA.size))
            if idLeido == salaId:
                return posicion, largo
            if idLeido < salaId:
                bajo = medio + 1
            else:
                alto = medio - 1
        return None

    def cargarSala(self, ruta, salaId):
        with open(ruta, "rb") as archivo:
            nSecciones, nSalas, posicionSecciones, posicionSalas = self._encabezado(archivo)
            if nSalas == 0:
                return None
            encontrada = self._buscaSala(archivo, nSalas, posicionSalas, salaId)
            if encontrada is None:
                return None
            return decodificar(self._bytes(archivo, encontrada[0], encontrada[1]))[0]

    def cargarSalas(self, ruta):
        with open(ruta, "rb") as archivo:
            nSecciones, nSalas, posicionSecciones, posicionSalas = self._encabezado(archivo)
            salida = []
            for i in range(nSalas):
                idLeido, posicion, largo = ENTRADA_SALA.unpack(
                    self._bytes(archivo, posicionSalas + i * ENTRADA_SALA.size, ENTRADA_SALA.size))
                salida.append((idLeido, decodificar(self._bytes(archivo, posicion, largo))[0]))
            return salida

    def secciones(self, ruta):
        """[(nombre, datos)] en el orden en que se escribieron; se usa para cargar todo."""
        with open(ruta, "rb") as archivo:
            nSecciones, nSalas, posicionSecciones, posicionSalas = self._encabezado(archivo)
            pos = posicionSecciones
            salida = []
            for _ in range(nSecciones):
                (largoNombre,) = LARGO_NOMBRE.unpack(
                    self._bytes(archivo, pos, LARGO_NOMBRE.size))
                pos += LARGO_NOMBRE.size
                nombre = self._bytes(archivo, pos, largoNombre).decode("ascii")
                pos += largoNombre
                posicion, largo = ENTRADA_SECCION.unpack(
                    self._bytes(archivo, pos, ENTRADA_SECCION.size))
                pos += ENTRADA_SECCION.size
                salida.append((nombre, decodificar(self._bytes(archivo, posicion, largo))[0]))
            return salida

    def leerSeccion(self, ruta, nombre):
        with open(ruta, "rb") as archivo:
            nSecciones, nSalas, posicionSecciones, posicionSalas = self._encabezado(archivo)
            pos = posicionSecciones
            for _ in range(nSecciones):
                (largoNombre,) = LARGO_NOMBRE.unpack(self._bytes(archivo, pos, LARGO_NOMBRE.size))
                pos += LARGO_NOMBRE.size
                leido = self._bytes(archivo, pos, largoNombre).decode("ascii")
                pos += largoNombre
                posicion, largo = ENTRADA_SECCION.unpack(
                    self._bytes(archivo, pos, ENTRADA_SECCION.size))
                pos += ENTRADA_SECCION.size
                if leido == nombre:
                    return decodificar(self._bytes(archivo, posicion, largo))[0]
        raise ValueError("El archivo de guardado no tiene la secci\u00f3n %s." % nombre)


class guardadoBinario:
    """API de lista de salas (bench y pruebas): cada sala es (id, enemigos, objetos)."""

    def __init__(self):
        self.contenedor = Contenedor()

    def guardar(self, ruta, salas):
        self.contenedor.guardar(ruta, [], [(sala[0], sala) for sala in salas])

    def cargarSala(self, ruta, salaId):
        datos = self.contenedor.cargarSala(ruta, salaId)
        return _normaliza(datos) if datos is not None else None

    def cargarTodo(self, ruta):
        return [_normaliza(sala) for _, sala in self.contenedor.cargarSalas(ruta)]


def _normaliza(datos):
    salaId, enemigos, objetos = datos
    return (salaId, [tuple(enemigo) for enemigo in enemigos], list(objetos))
