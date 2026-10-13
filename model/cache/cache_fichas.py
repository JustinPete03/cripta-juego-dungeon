from model.cache.lista_doble import ListaDoble

class CacheFichas:

    def __init__(self, capacidad=25):
        self.capacidad = capacidad
        self.lista = ListaDoble()
        self.indice = [] #arreglo para búsqueda binaria

        #contadores de metricas:
        self.hits = 0
        self.misses = 0
        self.desalojos = 0

    def buscar_posicion_indice(self, idFicha): #Para buscar la posicion en un indice contiguo
        inicio = 0
        fin = len(self.indice) - 1
        while inicio <= fin:
            mitad = (inicio + fin) // 2
            actual_id = self.indice[mitad][0]
            if actual_id == idFicha:
                return True, mitad
            elif actual_id < idFicha:
                inicio = mitad + 1
            else:
                fin = mitad - 1
        return False, inicio

    def consultar_ficha(self, idFicha): #para extraer la ficha de la cache
        encontrado, pos = self.busqueda_binaria(idFicha)
        if not encontrado:
            self.misses += 1
            return None
        else:
            self.hits += 1
            nodo = self.indice[pos][1]
            self.lista.mover_al_frente(nodo)
            return nodo.ficha

    def guardar_ficha(self, idFicha): #guarda en la cache


