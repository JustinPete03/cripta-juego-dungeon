#Acciones del jugador y su forma textual (la usan el controlador, el replay y la vista).
from model.Constantes import (ACC_MOVER, ACC_ABRIR, ACC_ATACAR, ACC_ESPERAR, ACC_RECOGER,
                               ACC_USAR, ACC_EQUIPAR, ACC_SOLTAR, ACC_RETROCESO,
                               ACC_SIGUIENTE, ACC_ANTERIOR)


class Accion:
    def __init__(self, tipo, argumento=None):
        self.tipo = tipo
        self.argumento = argumento    # dirección ("N") o índice base 0

    def aTexto (self):
        #Forma canónica para la bitácora de partida.
        t = self.tipo
        if t == ACC_MOVER:
            return "mover " + self.argumento
        if t == ACC_ABRIR:
            return "abrir " + self.argumento
        if t == ACC_ATACAR:
            return "atacar %d" % (self.argumento + 1)
        if t == ACC_RECOGER:
            return "recoger %d" % (self.argumento + 1)
        if t == ACC_ESPERAR:
            return "esperar"
        if t == ACC_USAR:
            return "usar"
        if t == ACC_EQUIPAR:
            return "equipar"
        if t == ACC_SOLTAR:
            return "soltar"
        if t == ACC_RETROCESO:
            return "retroceso"
        if t == ACC_SIGUIENTE:
            return "sig"
        return "ant"


def accionesDesdeTexto (texto):
   #Inversa de aTexto. Devuelve None si el texto no es una acción canónica.
    partes = texto.strip().split()
    if len(partes) == 0:
        return None
    nombre = partes[0]
    if nombre in ("mover", "abrir") and len(partes) == 2 and partes[1] in ("N", "S", "E", "O"):
        tipo = ACC_MOVER \
            if nombre == "mover" \
            else ACC_ABRIR
        return Accion(tipo, partes[1])
    if nombre in ("atacar", "recoger") and len(partes) == 2 and partes[1].isdigit():
        indice = int(partes[1]) - 1
        if indice < 0:
            return None
        return Accion(ACC_ATACAR if nombre == "atacar" else ACC_RECOGER, indice)
    if len(partes) == 1:
        if nombre == "esperar":
            return Accion(ACC_ESPERAR)
        if nombre == "usar":
            return Accion(ACC_USAR)
        if nombre == "equipar":
            return Accion(ACC_EQUIPAR)
        if nombre == "soltar":
            return Accion(ACC_SOLTAR)
        if nombre == "retroceso":
            return Accion(ACC_RETROCESO)
        if (nombre == "sig" or nombre == "siguiente"):
            return Accion(ACC_SIGUIENTE)
        if (nombre == "ant" or nombre == "anterior"):
            return Accion(ACC_ANTERIOR)
    return None
