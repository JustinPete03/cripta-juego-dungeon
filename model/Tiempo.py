def intervaloAccion(costo, velocidad):
    return max(1, costo * 100 // velocidad)


def tiempoTrasCambioVelocidad(tiempo_siguiente, t, velocidad_anterior, velocidad_nueva):
    #Devuelve el nuevo tiempo_siguiente de una acción ya programada.
    restante_nuevo = max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)
    return t + restante_nuevo
