# Guardado de la partida completa (sección 4.12).
#
# Formato binario propio, con la misma familia que el guardado por salas de Jurnier: los bloques
# van primero y al final del archivo se escribe un índice que los localiza por nombre. Cada bloque
# es JSON comprimido, así que agregar una sección nueva no cambia el encabezado.
#
# El archivo se guarda la identidad de la cripta (id, versión de cripta, versión de catálogo y
# semilla) igual que la bitácora de reproducción: cargar contra datos de otra versión produciría
# una partida falsa, así que se rechaza y se informa en lugar de intentarlo.

import json
import struct
import zlib

MAGIC = b"CRPS"
VERSION_FORMATO = 1
ENCABEZADO = struct.Struct("<4sHIQ")   # magic, versión, cantidad de secciones, posición del índice
LARGO_NOMBRE = struct.Struct("<H")     # los nombres son ASCII, su longitud manda la lectura
BLOQUE = struct.Struct("<QI")          # posición del bloque, longitud comprimida

SECCIONES = ("cripta", "esqueleto", "contenido", "estado")


class FuenteEmbebida:
    """Sirve desde el archivo el esqueleto y el contenido ya cargado.

    Las fichas siguen viniendo del proveedor real: el catálogo ya se persiste por versión en
    .cache_cripta/cat_<versionCatalogo>/, y la validación de la cabecera garantiza que es el mismo.
    """

    def __init__(self, real, esqueleto, contenido):
        self._real = real
        self._esqueleto = esqueleto
        self._contenido = contenido

    def datosGenerales(self):
        return self._real.datosGenerales()

    def esqueleto(self):
        return self._esqueleto

    def contenidoSala(self, salaId):
        bloque = self._contenido.get(salaId)
        if bloque is None:
            return self._real.contenidoSala(salaId)
        return bloque

    def ficha(self, tipoId):
        return self._real.ficha(tipoId)

    def anticipar(self, salaId):
        pass

    def fijarPredicadoEnUso(self, predicado):
        self._real.fijarPredicadoEnUso(predicado)


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
        with open(ruta, "wb") as archivo:
            archivo.write(b"\0" * ENCABEZADO.size)
            indice = []
            for nombre in SECCIONES:
                comprimido = _empacar(secciones[nombre])
                indice.append((nombre, archivo.tell(), len(comprimido)))
                archivo.write(comprimido)
            posicionIndice = archivo.tell()
            for nombre, posicion, largo in indice:
                crudo = nombre.encode("ascii")
                archivo.write(LARGO_NOMBRE.pack(len(crudo)) + crudo + BLOQUE.pack(posicion, largo))
            archivo.seek(0)
            archivo.write(ENCABEZADO.pack(MAGIC, VERSION_FORMATO, len(indice), posicionIndice))
        return ruta

    def _secciones(self, modelo):
        contenido = []
        for i in range(modelo.salas.cantidad()):
            sala = modelo.salas.enPosicion(i)
            if sala.contenidoIncorporado:
                contenido.append([sala.id, modelo.proveedor.contenidoSala(sala.id)])
        return {"cripta": self.identidad(modelo),
                "esqueleto": list(modelo.proveedor.esqueleto()),
                "contenido": contenido,
                "estado": modelo.capturarEstado()}

    # ------------------------------------------------------------------ cargar
    def cargar(self, modelo, ruta):
        secciones = self._leer(ruta)
        self._validarVersion(secciones["cripta"])
        contenido = {}
        for salaId, bloque in secciones["contenido"]:
            contenido[salaId] = bloque

        real = modelo.proveedor
        modelo.reiniciar()
        modelo.proveedor = FuenteEmbebida(real, secciones["esqueleto"], contenido)
        try:
            modelo.iniciarPartida()
        finally:
            modelo.proveedor = real
        modelo.restaurarEstado(secciones["estado"])
        return ruta

    def _leer(self, ruta):
        with open(ruta, "rb") as archivo:
            crudo = archivo.read()
        magic, version, cantidad, posicionIndice = self._leerEncabezado(crudo)
        secciones = {}
        pos = posicionIndice
        for _ in range(cantidad):
            (largoNombre,) = LARGO_NOMBRE.unpack_from(crudo, pos)
            pos += LARGO_NOMBRE.size
            nombre = crudo[pos:pos + largoNombre].decode("ascii")
            pos += largoNombre
            posicion, largo = BLOQUE.unpack_from(crudo, pos)
            pos += BLOQUE.size
            secciones[nombre] = _desempacar(crudo[posicion:posicion + largo])
        faltan = [nombre for nombre in SECCIONES if nombre not in secciones]
        if len(faltan) > 0:
            raise ValueError("El archivo de guardado no tiene la sección %s." % faltan[0])
        return secciones

    def _leerEncabezado(self, crudo):
        if len(crudo) < ENCABEZADO.size:
            raise ValueError("Archivo de guardado incompleto.")
        magic, version, cantidad, posicionIndice = ENCABEZADO.unpack_from(crudo, 0)
        if magic != MAGIC:
            raise ValueError("El archivo no es una partida de CRIPTA.")
        if version != VERSION_FORMATO:
            raise ValueError("Versión de formato incompatible: %d" % version)
        return magic, version, cantidad, posicionIndice

    def _validarVersion(self, cripta):
        esperado = {"idCripta": self.idCripta, "versionCripta": self.versionCripta,
                    "versionCatalogo": self.versionCatalogo}
        if self.idCripta is None:
            return                      # sin identidad conocida: se confía en el proveedor activo
        for clave, valor in esperado.items():
            if valor is None:
                continue
            if cripta.get(clave) != valor:
                raise ValueError(
                    "La partida guardada es de otra cripta (%s: %s, ahora: %s)."
                    % (clave, cripta.get(clave), valor))


def _empacar(datos):
    return zlib.compress(json.dumps(datos, separators=(",", ":"), ensure_ascii=False)
                         .encode("utf-8"), 9)


def _desempacar(comprimido):
    return json.loads(zlib.decompress(comprimido).decode("utf-8"))
