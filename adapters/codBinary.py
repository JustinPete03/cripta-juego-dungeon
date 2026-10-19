# Codificador binario propio (sección 4.10).
#
# Convierte los datos planos del guardado (None, bool, int, float, str, list y dict) en bytes y
# vuelta, sin pasar por JSON ni por compresores ajenos: el formato es nuestro y se puede leer
# por partes, que es justo lo que necesita el acceso aleatorio por sala.
#
# Cada valor es un tag de un byte seguido de su cuerpo. Los enteros pequeños cuestan 1 byte,
# las cadenas llevan su largo en un unsigned short, y las colecciones su cantidad de elementos.
# Así un bloque se puede localizar y decodificar sin tocar los siguientes.

import struct

NULO = 0
FALSO = 1
VERDADERO = 2
ENTERO = 3
REAL = 4
TEXTO = 5
TEXTO_LARGO = 6
LISTA = 7
LISTA_LARGA = 8
DICC = 9
DICC_LARGA = 10

LARGO_MAXIMO_CORTO = 0xFFFF
PROFUNDIDAD_MAXIMA = 64

_ENTERO_PEQUENO = struct.Struct("<b")
_ENTERO_MEDIANO = struct.Struct("<h")
_ENTERO_GRANDE = struct.Struct("<i")
_ENTERO_ENORME = struct.Struct("<q")
_REAL = struct.Struct("<d")
_LARGO_CORTO = struct.Struct("<H")
_LARGO_LARGO = struct.Struct("<I")


def codificar(datos):
    salida = bytearray()
    _codificar(datos, salida, 0)
    return bytes(salida)


def decodificar(datos, pos=0):
    """Devuelve (valor, posición siguiente). No lee más allá del valor pedido."""
    return _decodificar(datos, pos, 0)


def _codificar(datos, salida, profundidad):
    if profundidad > PROFUNDIDAD_MAXIMA:
        raise ValueError("El guardado excede la profundidad de datos soportada.")

    if datos is None:
        salida.append(NULO)
    elif datos is True:
        salida.append(VERDADERO)
    elif datos is False:
        salida.append(FALSO)
    elif isinstance(datos, int):
        salida.append(ENTERO)
        _codificarEntero(datos, salida)
    elif isinstance(datos, float):
        salida.append(REAL)
        salida += _REAL.pack(datos)
    elif isinstance(datos, str):
        _codificarTexto(datos, salida)
    elif isinstance(datos, (list, tuple)):
        _codificarColeccion(len(datos), salida, LISTA, LISTA_LARGA)
        for elemento in datos:
            _codificar(elemento, salida, profundidad + 1)
    elif isinstance(datos, dict):
        _codificarColeccion(len(datos), salida, DICC, DICC_LARGA)
        for clave, valor in datos.items():
            _codificar(str(clave), salida, profundidad + 1)
            _codificar(valor, salida, profundidad + 1)
    else:
        raise TypeError("El guardado no sabe codificar %s." % type(datos).__name__)


def _codificarColeccion(cantidad, salida, tagCorto, tagLargo):
    if cantidad <= LARGO_MAXIMO_CORTO:
        salida.append(tagCorto)
        salida += _LARGO_CORTO.pack(cantidad)
    else:
        salida.append(tagLargo)
        salida += _LARGO_LARGO.pack(cantidad)


def _codificarTexto(texto, salida):
    crudo = texto.encode("utf-8")
    if len(crudo) <= LARGO_MAXIMO_CORTO:
        salida.append(TEXTO)
        salida += _LARGO_CORTO.pack(len(crudo))
    else:
        salida.append(TEXTO_LARGO)
        salida += _LARGO_LARGO.pack(len(crudo))
    salida += crudo


def _codificarEntero(n, salida):
    if -128 <= n <= 127:
        salida.append(1)
        salida += _ENTERO_PEQUENO.pack(n)
    elif -32768 <= n <= 32767:
        salida.append(2)
        salida += _ENTERO_MEDIANO.pack(n)
    elif -(1 << 31) <= n < (1 << 31):
        salida.append(4)
        salida += _ENTERO_GRANDE.pack(n)
    else:
        salida.append(8)
        salida += _ENTERO_ENORME.pack(n)


def _decodificar(datos, pos, profundidad):
    if profundidad > PROFUNDIDAD_MAXIMA:
        raise ValueError("El archivo de guardado está corrompido (demasiada anidación).")

    tag = datos[pos]
    pos += 1
    if tag == NULO:
        return None, pos
    if tag == VERDADERO:
        return True, pos
    if tag == FALSO:
        return False, pos
    if tag == ENTERO:
        return _decodificarEntero(datos, pos)
    if tag == REAL:
        return _REAL.unpack_from(datos, pos)[0], pos + _REAL.size
    if tag == TEXTO:
        return _decodificarTexto(datos, pos, _LARGO_CORTO)
    if tag == TEXTO_LARGO:
        return _decodificarTexto(datos, pos, _LARGO_LARGO)
    if tag == LISTA:
        return _decodificarLista(datos, pos, _LARGO_CORTO, profundidad)
    if tag == LISTA_LARGA:
        return _decodificarLista(datos, pos, _LARGO_LARGO, profundidad)
    if tag == DICC:
        return _decodificarDiccionario(datos, pos, _LARGO_CORTO, profundidad)
    if tag == DICC_LARGA:
        return _decodificarDiccionario(datos, pos, _LARGO_LARGO, profundidad)
    raise ValueError("El archivo de guardado tiene un tag desconocido (%d)." % tag)


def _decodificarEntero(datos, pos):
    tamano = datos[pos]
    pos += 1
    if tamano == 1:
        return _ENTERO_PEQUENO.unpack_from(datos, pos)[0], pos + 1
    if tamano == 2:
        return _ENTERO_MEDIANO.unpack_from(datos, pos)[0], pos + 2
    if tamano == 4:
        return _ENTERO_GRANDE.unpack_from(datos, pos)[0], pos + 4
    if tamano == 8:
        return _ENTERO_ENORME.unpack_from(datos, pos)[0], pos + 8
    raise ValueError("El archivo de guardado tiene un entero de tamaño imposible.")


def _decodificarTexto(datos, pos, estructura):
    (largo,) = estructura.unpack_from(datos, pos)
    pos += estructura.size
    return datos[pos:pos + largo].decode("utf-8"), pos + largo


def _decodificarLista(datos, pos, estructura, profundidad):
    (cantidad,) = estructura.unpack_from(datos, pos)
    pos += estructura.size
    salida = []
    for _ in range(cantidad):
        elemento, pos = _decodificar(datos, pos, profundidad + 1)
        salida.append(elemento)
    return salida, pos


def _decodificarDiccionario(datos, pos, estructura, profundidad):
    (cantidad,) = estructura.unpack_from(datos, pos)
    pos += estructura.size
    salida = {}
    for _ in range(cantidad):
        clave, pos = _decodificar(datos, pos, profundidad + 1)
        valor, pos = _decodificar(datos, pos, profundidad + 1)
        salida[clave] = valor
    return salida, pos
