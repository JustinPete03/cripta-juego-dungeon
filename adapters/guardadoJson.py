import json

class guardadoJson:
    def guardar(self, ruta, salas):
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(salas, archivo)

    def cargarSala(self, ruta, salaId):
        # Hay que leer y convertir TODO el archivo para obtener una sala.
        with open(ruta, encoding="utf-8") as archivo:
            salas = json.load(archivo)
        for sala in salas:
            if sala[0] == salaId:
                return (sala[0], [tuple(enemigo) for enemigo in sala[1]], sala[2])
        return None

    def cargarTodo(self, ruta):
        with open(ruta, encoding="utf-8") as archivo:
            salas = json.load(archivo)
        return [(sala[0], [tuple(enemigo) for enemigo in sala[1]], sala[2]) for sala in salas]