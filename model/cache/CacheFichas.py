from model.cache.ListaDoble import ListaDoble
from model.cache.Nodo import Nodo

class CacheFichas:

    def __init__(self, capacidad=25, almacen=None):
        self.capacidad = capacidad
        self.lista = ListaDoble()
        self.almacen = almacen

        #contadores de metricas:
        self.aciertos = 0
        self.fallos = 0
        self.desalojos = 0
        self.vecesSobreTope = 0
        self.maximoAlcanzado = 0
        self.aciertosDisco = 0
        self.llamadasRed = 0

    def buscarNodo(self, idFicha): #devuelve el nodo con ese id, sino devuelve None
        actual = self.lista.primero
        while actual is not None:
            if actual.idFicha == idFicha:
                return actual
            actual = actual.siguiente
        return None

    def buscarDesalojable(self):
        actual = self.lista.ultimo
        while actual is not None:
            if actual.referencias == 0:
                return actual
            actual = actual.anterior
        return None

    def consultarFicha(self, idFicha): #para extraer la ficha de la cache
        nodo = self.buscarNodo(idFicha)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        self.lista.moverAlFrente(nodo)
        return nodo.ficha

    def guardarFicha(self, idFicha, ficha): #guarda en la cache
        nodo = self.buscarNodo(idFicha)
        if nodo is not None:
            nodo.ficha = ficha
            self.lista.moverAlFrente(nodo)
            return nodo

        if self.capacidad <= 0:
            return None

        while self.lista.tamanio >= self.capacidad:
            candidato = self.buscarDesalojable() #candidato a ser eliminado para guardar una nueva ficha
            if candidato is None:
                self.vecesSobreTope += 1
                break
            if self.almacen is not None:
                self.almacen.guardar(candidato.idFicha, candidato.ficha)
            self.lista.quitar(candidato)
            self.desalojos += 1

        nodo = Nodo(idFicha, ficha)
        self.lista.agregarAlFrente(nodo)
        if self.lista.tamanio > self.maximoAlcanzado:
            self.maximoAlcanzado = self.lista.tamanio
        return nodo

    def retenerFicha(self, idFicha):
        nodo = self.buscarNodo(idFicha)
        if nodo is None:
            return False
        nodo.referencias += 1
        return True

    def soltarFicha(self, idFicha):
        nodo = self.buscarNodo(idFicha)
        if nodo is None or nodo.referencias == 0:
            return False
        nodo.referencias -= 1
        return True

    def obtenerFichas(self, ids, cargador, tamanoLote=10):
        unicos = []
        resultados = []
        faltantes = []

        for idFicha in ids:
            if idFicha not in unicos:
                unicos.append(idFicha)

        for idFicha in unicos:
            ficha = self.consultarFicha(idFicha)
            if ficha is None and self.almacen is not None:
                ficha = self.almacen.leer(idFicha)
                if ficha is not None:
                    self.aciertosDisco += 1
                    self.guardarFicha(idFicha, ficha)
            if ficha is not None:
                resultados.append((idFicha, ficha))
            else:
                faltantes.append(idFicha)

        for inicio in range(0, len(faltantes), tamanoLote):
            lote = faltantes[inicio : inicio + tamanoLote]
            cargadas = cargador(lote)
            self.llamadasRed += 1
            for idFicha, ficha in cargadas:
                self.guardarFicha(idFicha, ficha)
                resultados.append((idFicha, ficha))

        return resultados


