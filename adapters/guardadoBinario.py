import struct

MAGIC = b"CRPT"
VERSION_FORMATO = 1
ENCABEZADO = struct.Struct("<4sHIQ")  # magic, versión, cantidad de salas, posición del índice
ENTRADA = struct.Struct("<IQI")       # salaId, posición, longitud


def _empacarTexto(texto):
    datos = texto.encode("utf-8")
    return struct.pack("<H", len(datos)) + datos


def _leerTexto(datos, pos):
    (largo,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    return datos[pos:pos + largo].decode("utf-8"), pos + largo


def _empacarSala(sala):
    _, enemigos, objetos = sala
    salida = struct.pack("<H", len(enemigos))
    for instancia, tipo, vida in enemigos:
        salida += _empacarTexto(instancia) + _empacarTexto(tipo) + struct.pack("<i", vida)
    salida += struct.pack("<H", len(objetos))
    for objeto in objetos:
        salida += _empacarTexto(objeto)
    return salida


def _desempacarSala(salaId, datos):
    pos = 0
    (cantidadEnemigos,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    enemigos = []
    for _ in range(cantidadEnemigos):
        instancia, pos = _leerTexto(datos, pos)
        tipo, pos = _leerTexto(datos, pos)
        (vida,) = struct.unpack_from("<i", datos, pos)
        pos += 4
        enemigos.append((instancia, tipo, vida))
    (cantidadObjetos,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    objetos = []
    for _ in range(cantidadObjetos):
        objeto, pos = _leerTexto(datos, pos)
        objetos.append(objeto)
    return (salaId, enemigos, objetos)


class guardadoBinario:
    def guardar(self, ruta, salas):
        """salas: lista de (id, enemigos, objetos), ya ordenada por id."""
        with open(ruta, "wb") as archivo:
            archivo.write(b"\0" * ENCABEZADO.size)
            indice = []
            for sala in salas:
                datos = _empacarSala(sala)
                indice.append((sala[0], archivo.tell(), len(datos)))
                archivo.write(datos)
            posicionIndice = archivo.tell()
            for entrada in indice:
                archivo.write(ENTRADA.pack(*entrada))
            archivo.seek(0)
            archivo.write(ENCABEZADO.pack(MAGIC, VERSION_FORMATO, len(salas), posicionIndice))

    def _leerEncabezado(self, archivo):
        magic, version, cantidad, posicionIndice = ENCABEZADO.unpack(archivo.read(ENCABEZADO.size))
        if magic != MAGIC:
            raise ValueError("Archivo de guardado inválido")
        if version != VERSION_FORMATO:
            raise ValueError(f"Versión de formato incompatible: {version}")
        return cantidad, posicionIndice

    def cargarSala(self, ruta, salaId):
        with open(ruta, "rb") as archivo:
            cantidad, posicionIndice = self._leerEncabezado(archivo)
            bajo, alto = 0, cantidad - 1
            while bajo <= alto:
                medio = (bajo + alto) // 2
                archivo.seek(posicionIndice + medio * ENTRADA.size)
                idLeido, posicion, largo = ENTRADA.unpack(archivo.read(ENTRADA.size))
                if idLeido == salaId:
                    archivo.seek(posicion)
                    return _desempacarSala(idLeido, archivo.read(largo))
                if idLeido < salaId:
                    bajo = medio + 1
                else:
                    alto = medio - 1
        return None

    def cargarTodo(self, ruta):
        salas = []
        with open(ruta, "rb") as archivo:
            cantidad, posicionIndice = self._leerEncabezado(archivo)
            archivo.seek(posicionIndice)
            entradas = [ENTRADA.unpack(archivo.read(ENTRADA.size)) for _ in range(cantidad)]
            for idLeido, posicion, largo in entradas:
                archivo.seek(posicion)
                salas.append(_desempacarSala(idLeido, archivo.read(largo)))
        return salas