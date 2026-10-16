import struct

MAGIC = b"CRPT"
VERSION_FORMATO = 1
ENCABEZADO = struct.Struct("<4sHIQ")  # magic, versión, n_salas, offset_índice
ENTRADA = struct.Struct("<IQI")       # sala_id, offset, longitud


def _empacar_texto(t):
    b = t.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def _leer_texto(datos, pos):
    (n,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    return datos[pos:pos + n].decode("utf-8"), pos + n


def _empacar_sala(sala):
    _, enemigos, objetos = sala
    out = struct.pack("<H", len(enemigos))
    for inst, tipo, vida in enemigos:
        out += _empacar_texto(inst) + _empacar_texto(tipo) + struct.pack("<i", vida)
    out += struct.pack("<H", len(objetos))
    for o in objetos:
        out += _empacar_texto(o)
    return out


def _desempacar_sala(sala_id, datos):
    pos = 0
    (n_enem,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    enemigos = []
    for _ in range(n_enem):
        inst, pos = _leer_texto(datos, pos)
        tipo, pos = _leer_texto(datos, pos)
        (vida,) = struct.unpack_from("<i", datos, pos)
        pos += 4
        enemigos.append((inst, tipo, vida))
    (n_obj,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    objetos = []
    for _ in range(n_obj):
        o, pos = _leer_texto(datos, pos)
        objetos.append(o)
    return (sala_id, enemigos, objetos)


class GuardadoBinario:
    def guardar(self, ruta, salas):
        """salas: lista de (id, enemigos, objetos), ya ordenada por id."""
        with open(ruta, "wb") as f:
            f.write(b"\0" * ENCABEZADO.size)
            indice = []
            for sala in salas:
                datos = _empacar_sala(sala)
                indice.append((sala[0], f.tell(), len(datos)))
                f.write(datos)
            offset_indice = f.tell()
            for entrada in indice:
                f.write(ENTRADA.pack(*entrada))
            f.seek(0)
            f.write(ENCABEZADO.pack(MAGIC, VERSION_FORMATO, len(salas), offset_indice))

    def cargar_sala(self, ruta, sala_id):
        with open(ruta, "rb") as f:
            magic, version, n, off_ind = ENCABEZADO.unpack(f.read(ENCABEZADO.size))
            if magic != MAGIC:
                raise ValueError("Archivo de guardado inválido")
            if version != VERSION_FORMATO:
                raise ValueError(f"Versión de formato incompatible: {version}")
            bajo, alto = 0, n - 1
            while bajo <= alto:
                medio = (bajo + alto) // 2
                f.seek(off_ind + medio * ENTRADA.size)
                sid, off, largo = ENTRADA.unpack(f.read(ENTRADA.size))
                if sid == sala_id:
                    f.seek(off)
                    return _desempacar_sala(sid, f.read(largo))
                if sid < sala_id:
                    bajo = medio + 1
                else:
                    alto = medio - 1
        return None

    def cargar_todo(self, ruta):
        salas = []
        with open(ruta, "rb") as f:
            magic, version, n, off_ind = ENCABEZADO.unpack(f.read(ENCABEZADO.size))
            if magic != MAGIC:
                raise ValueError("Archivo de guardado inválido")
            if version != VERSION_FORMATO:
                raise ValueError(f"Versión de formato incompatible: {version}")
            f.seek(off_ind)
            entradas = [ENTRADA.unpack(f.read(ENTRADA.size)) for _ in range(n)]
            for sid, off, largo in entradas:
                f.seek(off)
                salas.append(_desempacar_sala(sid, f.read(largo)))
        return salas