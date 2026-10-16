import json
import os

# Clase para manejar la tabla de puntajes locales, con registro de partidas y ordenamiento.
class GestorTablaPuntajes:
    def __init__(self, ruta_archivo: str = "puntajes_locales.json"):
        self.ruta_archivo = ruta_archivo

    def registrar_partida(
        self,
        nombre_jugador: str,
        id_cripta: str,
        version_cripta: str,
        acciones_ejecutadas: int,
        enemigos_derrotados: int,
        tiempo_final: int,
        victoria: bool,
    ):
        # Carga los puntajes existentes, agrega el nuevo registro y guarda la lista ordenada.
        puntajes = self._cargar_puntajes()
        nuevo_registro = {
            "nombre_jugador": nombre_jugador,
            "id_cripta": id_cripta,
            "version_cripta": version_cripta,
            "acciones_ejecutadas": acciones_ejecutadas,
            "enemigos_derrotados": enemigos_derrotados,
            "tiempo_final": tiempo_final,
            "victoria": victoria,
        }
        puntajes.append(nuevo_registro)

        # Ordenamos antes de guardar usando Merge Sort o Insertion Sort (depende)y luego guardamos en disco.)
        puntajes_ordenados = self.ordenar_puntajes(puntajes)
        self._guardar_puntajes(puntajes_ordenados)

    def obtener_tabla_ordenada(self) -> list:
        puntajes = self._cargar_puntajes()
        return self.ordenar_puntajes(puntajes)

    def ordenar_puntajes(self, lista: list) -> list:
       # Si la lista es pequeña o casi ordenada, usar Insertion Sort; de lo contrario, Merge Sort.
        n = len(lista)
        if n <= 1: return lista

        # Medimos si está casi ordenada contando pares adyacentes desordenados
        desordenes = 0
        for i in range(n - 1):
            if not self._es_mejor_o_igual(lista[i], lista[i + 1]): desordenes += 1

        # Si el arreglo es pequeño (n <= 24) o está casi ordenado (<= 15% desorden), Insertion Sort es O(n)
        if n <= 24 or (desordenes * 100 // n) <= 15:
            return self._insertion_sort(lista)
        else:
            return self._merge_sort(lista)
        
#El criterio de ordenamiento es: primero victorias, luego menor tiempo_final, luego menos acciones ejecutadas.
    def _es_mejor_o_igual(self, reg_a: dict, reg_b: dict) -> bool:
        #Si los registros difieren en victoria, el que tiene victoria es mejor. Si son iguales, el que tiene menor tiempo_final es mejor. Si también son iguales, el que tiene menos acciones_ejecutadas es mejor.
        if reg_a["victoria"] != reg_b["victoria"]: return reg_a["victoria"] > reg_b["victoria"]
        # Si ambos tienen el mismo estado de victoria, comparamos por tiempo_final (menor es mejor)
        if reg_a["tiempo_final"] != reg_b["tiempo_final"]: return reg_a["tiempo_final"] < reg_b["tiempo_final"]
        # Si ambos tienen el mismo tiempo_final, comparamos por acciones_ejecutadas (menor es mejor)
        return reg_a["acciones_ejecutadas"] <= reg_b["acciones_ejecutadas"]
#Metodo de ordenamiento por inserción Insertion Sort para listas pequeñas o casi ordenadas.
    def _insertion_sort(self, arr: list) -> list:
        copia = [elem for elem in arr]
        for i in range(1, len(copia)):
            actual = copia[i]
            j = i - 1
            while j >= 0 and not self._es_mejor_o_igual(copia[j], actual):
                copia[j + 1] = copia[j]
                j -= 1
            copia[j + 1] = actual
        return copia
# Metodo de ordenamiento Merge Sort para listas grandes o desordenadas.
    def _merge_sort(self, arr: list) -> list:
        if len(arr) <= 1:
            return arr
        medio = len(arr) // 2
        izquierda = self._merge_sort(arr[:medio])
        derecha = self._merge_sort(arr[medio:])
        return self._merge(izquierda, derecha)

    def _merge(self, izq: list, der: list) -> list:
        resultado = []
        i = 0
        j = 0
        while i < len(izq) and j < len(der):
            if self._es_mejor_o_igual(izq[i], der[j]):
                resultado.append(izq[i])
                i += 1
            else:
                resultado.append(der[j])
                j += 1
        while i < len(izq):
            resultado.append(izq[i])
            i += 1
        while j < len(der):
            resultado.append(der[j])
            j += 1
        return resultado

#Carga la lista de puntajes desde un archivo JSON, devolviendo una lista vacía si el archivo no existe o está corrupto.
    def _cargar_puntajes(self) -> list:
        if not os.path.exists(self.ruta_archivo): return []
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return []

    def _guardar_puntajes(self, lista: list):
        with open(self.ruta_archivo, "w", encoding="utf-8") as f: json.dump(lista, f, indent=2, ensure_ascii=False)