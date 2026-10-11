#Merge sort O(n log n)

def merge_sort(entrada, clave=None, descendente=False, contador=None):
    if clave is None:
        clave = lambda x: x

    datos = [(clave(elemento), elemento) for elemento in entrada]

    def va_antes(a,b):
        if contador is not None:
            contador.incrementar()
        return a > b if descendente else a < b

    buffer = [None] * len(datos)

    def fusionar(inicio,medio,fin):
        i = inicio
        j = medio
        k = inicio

        while i < medio and j < fin:

            if va_antes(datos[j][0], datos[i][0]):
                buffer[k] = datos[j]
                j += 1
            else:
                buffer[k] = datos[i]
                i += 1
            k += 1
        while i < medio:
            buffer[k] = datos[i]
            i+=1
            k+=1
        while j < fin:
            buffer[k] = datos[j]
            j+=1
            k+=1
        datos[inicio:fin] = buffer[inicio:fin]

    def ordenar_rango(inicio,fin):
        if fin - inicio <= 1:
            return
        medio = (inicio + fin) // 2
        ordenar_rango(inicio,medio)
        ordenar_rango(medio,fin)
        fusionar(inicio,medio,fin)

    ordenar_rango(0,len(datos))
    return [par[1] for par in datos]