#Proveedor en memoria SOLO para pruebas. Genera criptas sintéticas con el mismo contrato JSON.
import random

FICHAS = [
    {"id": "ent_rata", "clase": "enemigo", "nombre": "Rata gigante", "vida_max": 12, "ataque": 5,
     "defensa": 1, "velocidad": 150, "comportamiento": "rastreador", "suelta": ["itm_pocion"]},
    {"id": "ent_guardian", "clase": "enemigo", "nombre": "Esqueleto", "vida_max": 20, "ataque": 6,
     "defensa": 2, "velocidad": 100, "comportamiento": "guardian", "suelta": []},
    {"id": "ent_errante", "clase": "enemigo", "nombre": "Murciélago", "vida_max": 8, "ataque": 4,
     "defensa": 0, "velocidad": 120, "comportamiento": "errante", "suelta": []},
    {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "peso": 2, "valor": 15, "ataque_bonus": 3},
    {"id": "itm_pocion", "clase": "pocion", "nombre": "Poción", "peso": 1, "valor": 5, "cura": 5},
    {"id": "itm_llave_a", "clase": "llave", "nombre": "Llave A", "peso": 1, "valor": 1, "abre": "x"},
    {"id": "itm_llave_salida", "clase": "llave", "nombre": "Llave negra", "peso": 1, "valor": 1, "abre": "y"},
    {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos", "daño": 4, "rearme": 300},
]


class FuentePrueba:
    def __init__(self, ancho=5, alto=4, semillaCripta=7, enemigosPorSala=1,
                 vidaJugador=30, trampas=True):
        azar = random.Random(semillaCripta)
        self.ancho = ancho
        self.alto = alto
        self.vidaJugador = vidaJugador
        self.salas = []
        self.contenidos = []
        total = ancho * alto
        self.total = total
        nEnemigo = 100
        nTrampa = 1
        tipos = ["ent_rata", "ent_guardian", "ent_errante"]
        for y in range(alto):
            for x in range(ancho):
                idSala = y * ancho + x + 1
                salidas = {}
                if y > 0:
                    salidas["N"] = {"sala": idSala - ancho}
                if y < alto - 1:
                    salidas["S"] = {"sala": idSala + ancho}
                if x < ancho - 1:
                    salidas["E"] = {"sala": idSala + 1}
                if x > 0:
                    salidas["O"] = {"sala": idSala - 1}
                self.salas.append({"id": idSala, "nombre": "Sala %d" % idSala, "salidas": salidas})
                enemigos = []
                trampasSala = []
                objetos = []
                if idSala != 1:
                    for _ in range(enemigosPorSala):
                        nEnemigo += 1
                        enemigos.append({"instancia": "e-%d" % nEnemigo,
                                         "tipo": tipos[azar.randrange(3)], "vida": 8 + azar.randrange(5)})
                    if trampas and azar.randrange(4) == 0 and idSala != total:
                        trampasSala.append({"instancia": "t-%d" % nTrampa, "tipo": "trp_dardos"})
                        nTrampa += 1
                self.contenidos.append({"sala": idSala, "enemigos": enemigos,
                                        "objetos": objetos, "trampas": trampasSala})
        # llave en la sala inicial y puerta cerrada hacia la sala de salida
        self.contenidos[0]["objetos"].extend(["itm_llave_salida", "itm_daga"])
        anterior = total - 1
        self._cerrar(anterior, total, "itm_llave_salida", None)
        # una puerta con cierre automático (solo declarada en un lado, para probar la fusión)
        if total > 4:
            self._cerrar(2, 3, "itm_llave_a", 500, unLado=True)
            self.contenidos[0]["objetos"].append("itm_llave_a")

    def _sala(self, idSala):
        return self.salas[idSala - 1]

    def _cerrar(self, a, b, llave, cierre, unLado=False):
        for origen, destino in ((a, b), (b, a)):
            if unLado and origen == b:
                continue
            for direccion in self._sala(origen)["salidas"]:
                info = self._sala(origen)["salidas"][direccion]
                if info["sala"] == destino:
                    info["cerrada"] = True
                    info["llave"] = llave
                    if cierre is not None:
                        info["cierre_automatico"] = cierre

    # contrato ProveedorDatos
    def datosGenerales(self):
        return {"id": "cripta-prueba", "version": "v1", "sala_inicial": 1, "sala_salida": self.total,
                "llave_salida": "itm_llave_salida", "presupuesto_solicitudes": 9, "inventario_max": 10,
                "jugador": {"vida_max": self.vidaJugador, "ataque": 6, "defensa": 2, "velocidad": 100}}

    def esqueleto(self):
        return self.salas

    def contenidoSala(self, salaId):
        c = self.contenidos[salaId - 1]
        return {"sala": c["sala"], "enemigos": list(c["enemigos"]),
                "objetos": list(c["objetos"]), "trampas": list(c["trampas"])}

    def ficha(self, tipoId):
        for f in FICHAS:
            if f["id"] == tipoId:
                return f
        raise KeyError(tipoId)

    def anticipar(self, salaId):
        pass

    def asegurarFichas(self, tipoIds):
        pass    # todo el catálogo de prueba ya está en memoria

    def fijarFichasEnUso(self, productor):
        self.productor = productor