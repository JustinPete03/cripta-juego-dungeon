# Lógica de comportamiento del enemigo Cazador (§3.2).
# Desempate determinista por menor ID de sala vecina.


def elegirPasoCazador(cazador, salaJugador, distancias):
    """Aplica las reglas del cazador (§3.2):
    
    1. Si no comparte sala, consulta la distancia mínima d al jugador.
    2. Si no existe ruta o d > rango, espera con costo 100 (devuelve (None, 100)).
    3. Si existe ruta y d <= rango, busca entre las vecinas con costo(u, v) + dist(v, jugador) == d
       y elige la de menor id.
       Devuelve (salidaElegida, costoSalida).
    """
    if cazador.sala is salaJugador:
        return (None, 0)

    u = cazador.sala
    d = distancias.obtener(u.id)
    if d is None or d > cazador.rango:
        return (None, 100)

    mejorSalida = None
    mejorIdDestino = None

    for salida in u.salidas:
        if salida.puerta.cerrada:
            continue
        vId = salida.destinoId
        distV = distancias.obtener(vId)
        if distV is not None and (salida.costo + distV == d):
            if mejorIdDestino is None or vId < mejorIdDestino:
                mejorIdDestino = vId
                mejorSalida = salida

    if mejorSalida is not None:
        return (mejorSalida, mejorSalida.costo)

    return (None, 100)
