from model.cache.lista_doble import ListaDoble
from model.cache.nodo import Nodo

class CacheFichas:

    def __init__(self, capacidad=25):
        self.capacidad = capacidad
        self.lista = ListaDoble()
        self.indice = [] #arreglo para búsqueda binaria

        #contadores de metricas:
        self.aciertos = 0
        self.fallos = 0
        self.desalojos = 0
        self.veces_sobre_tope = 0
        self.maximo_alcanzado = 0

    def buscar_nodo(self, id_ficha): #Para buscar la posicion en un indice contiguo
        actual = self.lista.primero
        while actual is not None:
            if actual.idFicha == id_ficha:
                return actual
            actual = self.lista.siguiente
        return None

    def buscar_desalojabe(self):
        actual = self.lista.ultimo
        while actual is not None:
            if actual.referencias == 0:
                return actual
            actual = actual.anterior
        return None

    def consultar_ficha(self, id_ficha): #para extraer la ficha de la cache
        nodo = self.buscar_nodo(id_ficha)
        if nodo is not None:
            self.fallos += 1
            return None
        self.aciertos += 1
        self.lista.mover_al_frente(nodo)
        return nodo.ficha

    def guardar_ficha(self, id_ficha, ficha): #guarda en la cache
        nodo = self.buscar_nodo(id_ficha)
        if nodo is not None:
            nodo.ficha = ficha
            self.lista.mover_al_frente(nodo)
            return nodo

        if self.capacidad <= 0:
            return None

        while self.lista.tamanio >= self.capacidad:
            candidato = self.buscar_desalojabe() #candidato a ser eliminado para guardar una nueva ficha
            if candidato is None:
                self.veces_sobre_tope += 1
                break
            self.lista.quitar(candidato)
            self.desalojos += 1

        nodo = Nodo(id_ficha, ficha)
        self.lista.agregar_al_frente(nodo)
        if self.lista.tamanio > self.maximo_alcanzado:
            self.maximo_alcanzado = self.lista.tamanio
        return nodo

    def retener_ficha(self, id_ficha):
        nodo = self.buscar_nodo(id_ficha)
        if nodo is None:
            return False
        nodo.referencias += 1
        return True

    def soltar_ficha(self, id_ficha):
        nodo = self.buscar_nodo(id_ficha)
        if nodo is None or nodo.referencias == 0:
            return False
        nodo.referencias -= 1
        return True
