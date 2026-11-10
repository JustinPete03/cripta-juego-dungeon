# Lógica de comportamiento del enemigo Cazador (§3.2).
# Desempate determinista por menor ID de sala vecina, con el auxiliar común de la spec 005
# (elegirPrimerPaso), el mismo que usa «ir a».

from model.Dijkstra import Distancias, elegirPrimerPaso, puertaAbierta


def elegirPasoCazador(cazador, salaJugador, distancias):
    """Aplica las reglas del cazador (§3.2):

    1. Si comparte sala con el jugador, no se mueve (la regla de ataque decide; devuelve (None, 0)).
    2. Si no existe ruta o d > rango, espera con costo 100 (devuelve (None, 100)).
    3. Si existe ruta y d <= rango, va a la vecina de menor id entre las que cumplen
       costo(u, v) + dist(v, jugador) == d. Devuelve (salidaElegida, costoSalida).

    `distancias` es un objeto Distancias (de RutasCazador o calcularDistancias). También acepta
    una Tabla id -> distancia (la que devuelve dijkstraDesde) por compatibilidad.
    """
    if cazador.sala is salaJugador:
        return (None, 0)
    if not isinstance(distancias, Distancias):
        distancias = Distancias.desdeTabla(distancias)

    u = cazador.sala
    d = distancias.de(u)
    if d is None or d > cazador.rango:
        return (None, 100)

    salida = elegirPrimerPaso(u, distancias, puertaAbierta)
    if salida is None:
        return (None, 100)
    return (salida, salida.costo)
