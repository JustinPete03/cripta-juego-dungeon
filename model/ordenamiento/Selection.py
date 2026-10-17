# Ordenamiento por selección

def selectionSort(entrada, clave=None, descendente=False, contador=None):
    if clave is None:
        clave = lambda x: x

    datos = [(clave(elemento), elemento) for elemento in entrada]

    def vaAntes(a, b):
        if contador is not None:
            contador.incrementar()
        return a > b if descendente else a < b

    for i in range(len(datos) - 1):
        posicionExtremo = i
        for j in range(i + 1, len(datos)):
            if vaAntes(datos[j][0], datos[posicionExtremo][0]):
                posicionExtremo = j

        if posicionExtremo != i:
            datos[i], datos[posicionExtremo] = (
                datos[posicionExtremo],
                datos[i],
            )
    return [par[1] for par in datos]
