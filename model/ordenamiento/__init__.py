#Expone ordenar(), que elige automaticamente entre insercion y merge segun el tamano
#y el desorden de la entrada. selection_sort existe solo como referencia en los benchmarks.

from .selector import ordenar

__all__ = ["ordenar"]