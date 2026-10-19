# Guardado de la partida completa (sección 4.12).
#
# Formato binario propio. Distribución del archivo:
#
#   [encabezado][secciones cripta, esqueleto y estado][bloques de sala][índice de secciones]
#   [índice de salas]
#
# - Las secciones son JSON comprimido: se leen siempre completas al cargar.
# - El contenido de cada sala va en un bloque struct, el mismo de guardadoBinario, con un índice
#   de tamaño fijo ordenado por id. Una sala específica se recupera con búsqueda binaria sobre
#   el archivo, sin leer el resto (4.10).
#
# El archivo guarda la identidad de la cripta (id, versión de cripta, versión de catálogo y
# semilla) igual que la bitácora de reproducción: cargar contra datos de otra versión produciría
# una partida falsa, así que se rechaza y se informa en lugar de intentarlo.

import json
import struct
import zlib

from adapters.guardadoBinario import ENTRADA, buscarSala, escribirSalas

MAGIC = b"CRPS"
VERSION_FORMATO = 2
# magic, versión, cantidad de salas, posición del índice de salas, posición del índice de secciones
ENCABEZADO = struct.Struct("<4sHIQQ")
CANTIDAD = struct.Struct("<H")         # cantidad de secciones, al inicio del índice de secciones
LARGO_NOMBRE = struct.Struct("<H")     # los nombres son ASCII, su longitud manda la lectura
BLOQUE = struct.Struct("<QI")          # posición de la sección, longitud comprimida

SECCIONES = ("cripta", "esqueleto", "estado")


def _aContenido(sala):
    """Tupla (id, enemigos, objetos, trampas) -> el mismo diccionario que sirve el proveedor."""
    salaId, enemigos, objetos, trampas = sala
    return {"sala": salaId,
            "enemigos": [{"instancia": i, "tipo": t, "vida": v} for i, t, v in enemigos],
            "objetos": list(objetos),
            "trampas": [{"instancia": i, "tipo": t} for i, t in trampas]}


def _aTupla(contenido):
    enemigos = [(e["instancia"], e["tipo"], e["vida"]) for e in contenido["enemigos"]]
    trampas = [(t["instancia"], t["tipo"]) for t in contenido["trampas"]]
    return (contenido["sala"], enemigos, list(contenido["objetos"]), trampas)


class FuenteEmbebida:
    """Sirve desde el archivo el esqueleto y el contenido de las salas, sin tocar la red.

    El contenido se lee sala por sala con búsqueda binaria en el archivo. Las fichas siguen
    viniendo del proveedor real: el catálogo ya se persiste por versión en
    .cache_cripta/cat_<versionCatalogo>/, y la validación de la cabecera garantiza que es el mismo.
    """

    def __init__(self, real, esqueleto, ruta, guardado):
        self._real = real
        self._esqueleto = esqueleto
        self._ruta = ruta
        self._guardado = guardado

    def datosGenerales(self):
        return self._real.datosGenerales()

    def esqueleto(self):
        return self._esqueleto

    def contenidoSala(self, salaId):
        bloque = self._guardado.leerSala(self._ruta, salaId)
        if bloque is None:
            return self._real.contenidoSala(salaId)
        return bloque

    def ficha(self, tipoId):
        return self._real.ficha(tipoId)

    def anticipar(self, salaId):
        pass

    def asegurarFichas(self, tipoIds):
        self._real.asegurarFichas(tipoIds)

    def fijarFichasEnUso(self, productor):
        self._real.fijarFichasEnUso(productor)


class guardadoPartida:
    def __init__(self, idCripta=None, versionCripta=None, versionCatalogo=None):
        self.idCripta = idCripta
        self.versionCripta = versionCripta
        self.versionCatalogo = versionCatalogo

    def identidad(self, modelo):
        return {"idCripta": self.idCripta, "versionCripta": self.versionCripta,
                "versionCatalogo": self.versionCatalogo, "semilla": modelo.semilla}

    # ------------------------------------------------------------------ guardar
    def guardar(self, modelo, ruta):
        secciones = self._secciones(modelo)
        salas = self._salas(modelo)
        with open(ruta, "wb") as archivo:
            archivo.write(b"\0" * ENCABEZADO.size)
            indice = []
            for nombre, datos in secciones:
                comprimido = _empacar(datos)
                indice.append((nombre, archivo.tell(), len(comprimido)))
                archivo.write(comprimido)
            posicionSalas = escribirSalas(archivo, salas)
            posicionSecciones = archivo.tell()
            archivo.write(CANTIDAD.pack(len(indice)))
            for nombre, posicion, largo in indice:
                crudo = nombre.encode("ascii")
                archivo.write(LARGO_NOMBRE.pack(len(crudo)) + crudo + BLOQUE.pack(posicion, largo))
            archivo.seek(0)
            archivo.write(ENCABEZADO.pack(MAGIC, VERSION_FORMATO, len(salas),
                                          posicionSalas, posicionSecciones))
        return ruta

    def _secciones(self, modelo):
        return [("cripta", self.identidad(modelo)),
                ("esqueleto", list(modelo.proveedor.esqueleto())),
                ("estado", modelo.capturarEstado())]

    def _salas(self, modelo):
        """Contenido de las salas ya incorporadas, ordenado por id (las salas ya lo están)."""
        salas = []
        for i in range(modelo.salas.cantidad()):
            sala = modelo.salas.enPosicion(i)
            if sala.contenidoIncorporado:
                salas.append(_aTupla(modelo.proveedor.contenidoSala(sala.id)))
        return salas

    # ------------------------------------------------------------------ cargar
    def cargar(self, modelo, ruta):
        secciones = self._leerSecciones(ruta)
        self._validarVersion(_seccion(secciones, "cripta"))
        real = modelo.proveedor
        modelo.reiniciar()
        modelo.proveedor = FuenteEmbebida(real, _seccion(secciones, "esqueleto"), ruta, self)
        try:
            modelo.iniciarPartida()
            # Restaurar con la fuente del archivo activa: las salas ya visitadas se leen de
            # aquí y no se vuelven a pedir a la red.
            modelo.restaurarEstado(_seccion(secciones, "estado"))
        finally:
            modelo.proveedor = real
        return ruta

    def leerSala(self, ruta, salaId):
        """Contenido de una sala leyendo sólo lo necesario del archivo; None si no está."""
        with open(ruta, "rb") as archivo:
            _, cantidad, posicionSalas, _ = self._leerEncabezado(archivo)
            sala = buscarSala(archivo, cantidad, posicionSalas, salaId)
        if sala is None:
            return None
        return _aContenido(sala)

    def _leerSecciones(self, ruta):
        secciones = []
        with open(ruta, "rb") as archivo:
            _, _, _, posicionSecciones = self._leerEncabezado(archivo)
            archivo.seek(posicionSecciones)
            (cantidad,) = CANTIDAD.unpack(archivo.read(CANTIDAD.size))
            indice = []
            for _ in range(cantidad):
                (largoNombre,) = LARGO_NOMBRE.unpack(archivo.read(LARGO_NOMBRE.size))
                nombre = archivo.read(largoNombre).decode("ascii")
                posicion, largo = BLOQUE.unpack(archivo.read(BLOQUE.size))
                indice.append((nombre, posicion, largo))
            for nombre, posicion, largo in indice:
                archivo.seek(posicion)
                secciones.append((nombre, _desempacar(archivo.read(largo))))
        for nombre in SECCIONES:
            _seccion(secciones, nombre)         # falla con ValueError si falta alguna
        return secciones

    def _leerEncabezado(self, archivo):
        crudo = archivo.read(ENCABEZADO.size)
        if len(crudo) < ENCABEZADO.size:
            raise ValueError("Archivo de guardado incompleto.")
        magic, version, cantidad, posicionSalas, posicionSecciones = ENCABEZADO.unpack(crudo)
        if magic != MAGIC:
            raise ValueError("El archivo no es una partida de CRIPTA.")
        if version != VERSION_FORMATO:
            raise ValueError("Versión de formato incompatible: %d" % version)
        return version, cantidad, posicionSalas, posicionSecciones

    def _validarVersion(self, cripta):
        esperado = (("idCripta", self.idCripta), ("versionCripta", self.versionCripta),
                    ("versionCatalogo", self.versionCatalogo))
        if self.idCripta is None:
            return                      # sin identidad conocida: se confía en el proveedor activo
        for clave, valor in esperado:
            if valor is None:
                continue
            if cripta.get(clave) != valor:
                raise ValueError(
                    "La partida guardada es de otra cripta (%s: %s, ahora: %s)."
                    % (clave, cripta.get(clave), valor))


def _seccion(secciones, nombre):
    """Busca una sección por nombre en la lista [(nombre, datos)]; son sólo tres."""
    for clave, datos in secciones:
        if clave == nombre:
            return datos
    raise ValueError("El archivo de guardado no tiene la sección %s." % nombre)


def _empacar(datos):
    return zlib.compress(json.dumps(datos, separators=(",", ":"), ensure_ascii=False)
                         .encode("utf-8"), 9)


def _desempacar(comprimido):
    return json.loads(zlib.decompress(comprimido).decode("utf-8"))