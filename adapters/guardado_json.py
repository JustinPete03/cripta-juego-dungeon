import json

class GuardadoJSON:
    def guardar(self, ruta, salas):
        with open(ruta, "w" ,encoding="utf-8") as f:
            json.dump(salas, f)

    def cargar_sala(self, ruta, sala_id):
        with open(ruta, encoding="utf-8") as f:
            salas = json.load(f)
        for s in salas:
            if s[0]==sala_id:
                return (s[0], [tuple(e) for e in s[1]], s[2])
            return None

    def cargar_todo(self, ruta):
        with open(ruta, encoding="utf-8") as f:
            salas = json.load(f)
        return [(s[0], [tuple(e) for e in s[1]], s[2]) for s in salas]