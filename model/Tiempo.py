def intervaloAccion(costo, velocidad):
    return max(1, costo * 100 // velocidad)


def tiempoTrasCambioVelocidad(tiempoSiguiente, t, velocidadAnterior, velocidadNueva):
    #Devuelve el nuevo tiempoSiguiente de una acción ya programada.
    restante = max(1, (tiempoSiguiente - t) * velocidadAnterior // velocidadNueva)
    return t + restante
