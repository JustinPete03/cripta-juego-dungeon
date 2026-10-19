# Guardado binario por salas (sección 4.10).
#
# Cada sala se escribe como un bloque con struct y al final del archivo va un índice de tamaño
# fijo, ordenado por id de sala. Así una sala específica se recupera con búsqueda binaria sobre
# el propio archivo (O(log n) lecturas pequeñas) sin leer el resto.
#
# Una sala es la tupla (id, enemigos, objetos, trampas):
#   enemigos: [(instancia, tipo, vida)]   objetos: [tipo]   trampas: [(instancia, tipo)]
#
# guardadoPartida reutiliza los mismos bloques e índice para el contenido de las salas.

import struct

MAGIC = b"CRPT"
VERSION_FORMATO = 2
ENCABEZADO = struct.Struct("<4sHIQ")  # magic, versión, cantidad de salas, posición del índice
ENTRADA = struct.Struct("<IQI")       # salaId, posición, longitud


def empacarTexto(texto):
    datos = texto.encode("utf-8")
    return struct.pack("<H", len(datos)) + datos


def leerTexto(datos, pos):
    (largo,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    return datos[pos:pos + largo].decode("utf-8"), pos + largo


def empacarSala(sala):
    _, enemigos, objetos, trampas = sala
    salida = struct.pack("<H", len(enemigos))
    for instancia, tipo, vida in enemigos:
        salida += empacarTexto(instancia) + empacarTexto(tipo) + struct.pack("<i", vida)
    salida += struct.pack("<H", len(objetos))
    for objeto in objetos:
        salida += empacarTexto(objeto)
    salida += struct.pack("<H", len(trampas))
    for instancia, tipo in trampas:
        salida += empacarTexto(instancia) + empacarTexto(tipo)
    return salida


def desempacarSala(salaId, datos):
    pos = 0
    (cantidadEnemigos,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    enemigos = []
    for _ in range(cantidadEnemigos):
        instancia, pos = leerTexto(datos, pos)
        tipo, pos = leerTexto(datos, pos)
        (vida,) = struct.unpack_from("<i", datos, pos)
        pos += 4
        enemigos.append((instancia, tipo, vida))
    (cantidadObjetos,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    objetos = []
    for _ in range(cantidadObjetos):
        objeto, pos = leerTexto(datos, pos)
        objetos.append(objeto)
    (cantidadTrampas,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    trampas = []
    for _ in range(cantidadTrampas):
        instancia, pos = leerTexto(datos, pos)
        tipo, pos = leerTexto(datos, pos)
        trampas.append((instancia, tipo))
    return (salaId, enemigos, objetos, trampas)


def escribirSalas(archivo, salas):
    """Escribe los bloques de sala y su índice ordenado a partir de la posición actual.

    salas: lista de (id, enemigos, objetos, trampas), ya ordenada por id.
    Devuelve la posición donde quedó el índice."""
    indice = []
    for sala in salas:
        datos = empacarSala(sala)
        indice.append((sala[0], archivo.tell(), len(datos)))
        archivo.write(datos)
    posicionIndice = archivo.tell()
    for entrada in indice:
        archivo.write(ENTRADA.pack(*entrada))
    return posicionIndice


def buscarSala(archivo, cantidad, posicionIndice, salaId):
    """Búsqueda binaria sobre el índice del archivo: lee sólo las entradas que visita."""
    bajo, alto = 0, cantidad - 1
    while bajo <= alto:
        medio = (bajo + alto) // 2
        archivo.seek(posicionIndice + medio * ENTRADA.size)
        idLeido, posicion, largo = ENTRADA.unpack(archivo.read(ENTRADA.size))
        if idLeido == salaId:
            archivo.seek(posicion)
            return desempacarSala(idLeido, archivo.read(largo))
        if idLeido < salaId:
            bajo = medio + 1
        else:
            alto = medio - 1
    return None


class guardadoBinario:
    def guardar(self, ruta, salas):
        """salas: lista de (id, enemigos, objetos, trampas), ya ordenada por id."""
        with open(ruta, "wb") as archivo:
            archivo.write(b"\0" * ENCABEZADO.size)
            posicionIndice = escribirSalas(archivo, salas)
            archivo.seek(0)
            archivo.write(ENCABEZADO.pack(MAGIC, VERSION_FORMATO, len(salas), posicionIndice))

    def _leerEncabezado(self, archivo):
        crudo = archivo.read(ENCABEZADO.size)
        if len(crudo) < ENCABEZADO.size:
            raise ValueError("Archivo de guardado inválido")
        magic, version, cantidad, posicionIndice = ENCABEZADO.unpack(crudo)
        if magic != MAGIC:
            raise ValueError("Archivo de guardado inválido")
        if version != VERSION_FORMATO:
            raise ValueError(f"Versión de formato incompatible: {version}")
        return cantidad, posicionIndice

    def cargarSala(self, ruta, salaId):
        with open(ruta, "rb") as archivo:
            cantidad, posicionIndice = self._leerEncabezado(archivo)
            return buscarSala(archivo, cantidad, posicionIndice, salaId)

    def cargarTodo(self, ruta):
        salas = []
        with open(ruta, "rb") as archivo:
            cantidad, posicionIndice = self._leerEncabezado(archivo)
            archivo.seek(posicionIndice)
            entradas = [ENTRADA.unpack(archivo.read(ENTRADA.size)) for _ in range(cantidad)]
            for idLeido, posicion, largo in entradas:
                archivo.seek(posicion)
                salas.append(desempacarSala(idLeido, archivo.read(largo)))
        return salas