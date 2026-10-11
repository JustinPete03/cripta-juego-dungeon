# Ordenamiento por inserción

def insertion_sort(entrada, clave=None, descendente=False, contador=None):
    if clave is None:
        clave = lambda x: x

    datos = [(clave(elemento), elemento) for elemento in entrada]

    def va_antes(a,b):
        if contador is not None:
            contador.incrementar()
        return a > b if descendente else a < b

    for i in range(1,len(datos)):
        actual = datos[i]
        j = i - 1
        while j >= 0 and va_antes(actual[0], datos[j][0]):
            datos[j+1] = datos[j]
            j -= 1
        datos[j+1] = actual
    return [par[1] for par in datos]
