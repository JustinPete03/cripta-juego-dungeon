# Ordenamiento por selección

def selection_sort(entrada, clave=None, descendente=False, contador=None):
    if clave is None:
        clave = lambda x: x

    datos = [(clave(elemento), elemento) for elemento in entrada]

    def va_antes(a, b):
        if contador is not None:
            contador.incrementar()
        return a > b if descendente else a < b

    for i in range(len(datos) - 1):
        posicion_extremo = i
        for j in range(i + 1, len(datos)):
            if va_antes(datos[j][0], datos[posicion_extremo][0]):
                posicion_extremo = j

        if posicion_extremo != i:
            datos[i], datos[posicion_extremo] = (
                datos[posicion_extremo],
                datos[i],
            )
    return [par[1] for par in datos]
