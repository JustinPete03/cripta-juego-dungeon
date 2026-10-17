#contraro para guardar y recuperar fichas fuera de la memoria (interfaz)
#El modelo solo conoce esta interfaz. Cómo y dónde se guardan las fichas
#lo decide el adaptador que la implemente.

class AlmacenFichas:

    def guardar(self, idFicha, ficha):
        raise NotImplementedError  #Guarda la ficha. Devuelve true si se guardó

    def leer(self, idFicha):
        raise NotImplementedError #devuelve la ficha, o none si no está o no se pudo leer