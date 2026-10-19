import json


def _aTupla(sala):
    return (sala[0], [tuple(enemigo) for enemigo in sala[1]], sala[2],
            [tuple(trampa) for trampa in sala[3]])


class guardadoJson:
    def guardar(self, ruta, salas):
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(salas, archivo)

    def cargarSala(self, ruta, salaId):
        with open(ruta, encoding="utf-8") as archivo:
            salas = json.load(archivo)
        for sala in salas:
            if sala[0] == salaId:
                return _aTupla(sala)
        return None

    def cargarTodo(self, ruta):
        with open(ruta, encoding="utf-8") as archivo:
            salas = json.load(archivo)
        return [_aTupla(sala) for sala in salas]