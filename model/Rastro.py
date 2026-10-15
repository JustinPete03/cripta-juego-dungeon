#Rastreador (2.9 y 4.7). Costo proporcional al número de salidas de la sala (máx. 4).
from model.Constantes import VENTANA_RASTRO


def elegirDestinoRastreador(sala, reloj):
    #Devuelve la Sala vecina con el rastro fresco más reciente, o None (esperar).
    #La caducidad se detecta al consultar: no hay eventos de limpieza ni recorridos globales.

    mejor = None
    for salida in sala.salidas:
        if salida.puerta.cerrada:
            continue
        vecina = salida.destino
        rastro = vecina.rastro
        if rastro < 0:
            continue
        if reloj - rastro >= VENTANA_RASTRO:
            continue
        if mejor is None or rastro > mejor.rastro or (rastro == mejor.rastro and vecina.id < mejor.id):
            mejor = vecina
    return mejor
