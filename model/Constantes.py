#Constantes del contrato del juego (enunciado 2). Sin datos de ninguna cripta concreta.

# Direcciones, en orden canónico
DIRECCIONES = ["N", "S", "E", "O"]


def direccionOpuesta(direccion):
    if direccion == "N":
        return "S"
    if direccion == "S":
        return "N"
    if direccion == "E":
        return "O"
    return "E"


# Estado de la partida
EN_CURSO = 0
VICTORIA = 1
DERROTA = 2

# Tipos de evento de la agenda.
EV_JUGADOR = 0
EV_ENEMIGO = 1
EV_CIERRE_PUERTA = 2
EV_REARME_TRAMPA = 3
EV_VENENO = 4
EV_FIN_VENENO = 5
EV_REGENERACION = 6
EV_FIN_ANTORCHA = 7
EV_FIN_VELOCIDAD = 8
CANTIDAD_TIPOS_EVENTO = 16

# Tipos de acción del jugador
ACC_MOVER = 0
ACC_ABRIR = 1
ACC_ATACAR = 2
ACC_ESPERAR = 3
ACC_RECOGER = 4
ACC_USAR = 5
ACC_EQUIPAR = 6
ACC_SOLTAR = 7
ACC_RETROCESO = 8   # no consume tiempo, no es acción del jugador (2.11)
ACC_SIGUIENTE = 9   # navegación del inventario: no consume tiempo
ACC_ANTERIOR = 10

# Costo base por tipo de acción (2.3)*
COSTOS = [100, 50, 100, 100, 25, 50, 50, 25, 0, 0, 0]
COSTO_ACCION_ENEMIGO = 100

VENTANA_RASTRO = 400          # 2.9
REARME_POR_DEFECTO = 300      # 2.10
CAPACIDAD_BITACORA = 20       # 4.8
