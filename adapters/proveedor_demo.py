# Fuente de datos de demostración para la interfaz gráfica: cumple ProveedorDatos sin tocar la red.
#
# Amplía las fichas de la fuente de prueba con las clases del catálogo (sección 2.7) que la interfaz
# necesita poder ejercitar: pergamino de retroceso, armadura, antorcha, antídoto y la trampa
# envenenada (el campo "veneno" es el daño por pulso que contagia efectosTrampa).

from tests.FuentePrueba import FuentePrueba, FICHAS

FICHAS_DEMO = (
    {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos envenenados",
     "daño": 4, "veneno": 3, "rearme": 300},
    {"id": "itm_pergamino", "clase": "pergamino_retroceso", "nombre": "Pergamino de retroceso",
     "peso": 1, "valor": 40},
    {"id": "itm_coraza", "clase": "armadura", "nombre": "Coraza oxidada",
     "peso": 6, "valor": 35, "defensa_bonus": 2},
    {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha",
     "peso": 1, "valor": 5, "duracion": 2000},
    {"id": "itm_antidoto", "clase": "antidoto", "nombre": "Antídoto", "peso": 1, "valor": 12},
    {"id": "itm_escama", "clase": "arma", "nombre": "Hacha mellada",
     "peso": 7, "valor": 28, "ataque_bonus": 5},
)

# Configuraciones de partida para la pantalla de selección: son parámetros del generador,
# no datos de una cripta concreta del servicio.
CRIPTAS_DEMO = (
    ("Osario menor", {"ancho": 4, "alto": 3, "enemigosPorSala": 1, "vidaJugador": 34}),
    ("Bóvedas negras", {"ancho": 5, "alto": 4, "enemigosPorSala": 1, "vidaJugador": 30}),
    ("Laberinto de urnas", {"ancho": 6, "alto": 5, "enemigosPorSala": 2, "vidaJugador": 26}),
)


class ProveedorDemo(FuentePrueba):
    def __init__(self, **parametros):
        FuentePrueba.__init__(self, **parametros)
        self.contenidos[0]["objetos"].extend(["itm_pergamino", "itm_coraza", "itm_antorcha"])
        self._repartir("itm_pergamino", 2)
        self._repartir("itm_antidoto", 2)
        self._repartir("itm_escama", 1)
        self._repartir("itm_pocion", 3)

    def _repartir(self, tipoId, cantidad):
        """Coloca `cantidad` unidades repartidas desde la segunda mitad de la cripta."""
        total = len(self.contenidos)
        puestas = 0
        i = total // 2
        while puestas < cantidad and i < total:
            sala = self.contenidos[i]
            if len(sala["objetos"]) < 3:
                sala["objetos"].append(tipoId)
                puestas += 1
            i += 1

    def ficha(self, tipoId):
        for ficha in FICHAS_DEMO:
            if ficha["id"] == tipoId:
                return ficha
        return FuentePrueba.ficha(self, tipoId)
