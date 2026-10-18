import json
import os

# Clase para manejar la tabla de puntajes locales, con registro de partidas y ordenamiento (sección 2.12 / sección 4.9).
class GestorTablaPuntajes:
    def __init__(self, rutaArchivo: str = "puntajes_locales.json"):
        self.rutaArchivo = rutaArchivo

    @property
    def ruta_archivo(self):
        return self.rutaArchivo

    def registrarPartida(
        self,
        nombreJugador: str,
        idCripta: str,
        versionCripta: str,
        accionesEjecutadas: int,
        enemigosDerrotados: int,
        tiempoFinal: int,
        victoria: bool,
    ):
        # Carga los puntajes existentes, agrega el nuevo registro y guarda la lista ordenada (sección 2.12)
        puntajes = self._cargarPuntajes()
        nuevoRegistro = {
            "nombre_jugador": nombreJugador,
            "id_cripta": idCripta,
            "version_cripta": versionCripta,
            "acciones_ejecutadas": accionesEjecutadas,
            "enemigos_derrotados": enemigosDerrotados,
            "tiempo_final": tiempoFinal,
            "victoria": victoria,
        }
        puntajes.append(nuevoRegistro)

        # Ordenamos antes de guardar usando Insertion Sort o Merge Sort según propiedades (sección 4.9)
        puntajesOrdenados = self.ordenarPuntajes(puntajes)
        self._guardarPuntajes(puntajesOrdenados)

    def obtenerTablaOrdenada(self) -> list:
        puntajes = self._cargarPuntajes()
        return self.ordenarPuntajes(puntajes)

    def ordenarPuntajes(self, lista: list) -> list:
        # Selección adaptativa (sección 4.9): si la lista es pequeña o casi ordenada usa Insertion Sort; si no, Merge Sort.
        n = len(lista)
        if n <= 1:
            return list(lista)

        # Medimos desorden contando pares adyacentes invertidos
        desordenes = 0
        for i in range(n - 1):
            if not self._esMejorOIgual(lista[i], lista[i + 1]):
                desordenes += 1

        if n <= 24 or (desordenes * 100 // n) <= 15:
            return self._insertionSort(lista)
        else:
            return self._mergeSort(lista)

    def _esMejorOIgual(self, regA: dict, regB: dict) -> bool:
        # Criterio (sección 2.12): Victorias primero -> Menor tiempo final -> Menos acciones -> Más enemigos derrotados
        if regA["victoria"] != regB["victoria"]:
            return regA["victoria"] > regB["victoria"]
        if regA["tiempo_final"] != regB["tiempo_final"]:
            return regA["tiempo_final"] < regB["tiempo_final"]
        if regA["acciones_ejecutadas"] != regB["acciones_ejecutadas"]:
            return regA["acciones_ejecutadas"] < regB["acciones_ejecutadas"]
        return regA["enemigos_derrotados"] >= regB["enemigos_derrotados"]

    def _insertionSort(self, arr: list) -> list:
        copia = list(arr)
        for i in range(1, len(copia)):
            actual = copia[i]
            j = i - 1
            while j >= 0 and not self._esMejorOIgual(copia[j], actual):
                copia[j + 1] = copia[j]
                j -= 1
            copia[j + 1] = actual
        return copia

    def _mergeSort(self, arr: list) -> list:
        if len(arr) <= 1:
            return list(arr)
        medio = len(arr) // 2
        izquierda = self._mergeSort(arr[:medio])
        derecha = self._mergeSort(arr[medio:])
        return self._merge(izquierda, derecha)

    def _merge(self, izq: list, der: list) -> list:
        resultado = []
        i = 0
        j = 0
        while i < len(izq) and j < len(der):
            if self._esMejorOIgual(izq[i], der[j]):
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

    def _cargarPuntajes(self) -> list:
        if not os.path.exists(self.rutaArchivo):
            return []
        try:
            with open(self.rutaArchivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _guardarPuntajes(self, lista: list):
        with open(self.rutaArchivo, "w", encoding="utf-8") as f:
            json.dump(lista, f, indent=2, ensure_ascii=False)

    def formatearTabla(self, limite: int = 10) -> str:
        tabla = self.obtenerTablaOrdenada()[:limite]
        if not tabla:
            return "No hay partidas registradas en la tabla de puntajes."
        lineas = [
            "=== TABLA DE PUNTAJES LOCALES ===",
            f"{'#':<3} {'Jugador':<16} {'Cripta':<12} {'Resultado':<10} {'Tiempo':<8} {'Acciones':<9} {'Bajas':<6}",
            "-" * 68,
        ]
        for idx, r in enumerate(tabla, 1):
            estado = "Victoria" if r.get("victoria") else "Derrota"
            lineas.append(
                f"{idx:<3} {r.get('nombre_jugador', 'Anónimo')[:15]:<16} {r.get('id_cripta', '')[:11]:<12} "
                f"{estado:<10} {r.get('tiempo_final', 0):<8} {r.get('acciones_ejecutadas', 0):<9} {r.get('enemigos_derrotados', 0):<6}"
            )
        lineas.append("=" * 68)
        return "\n".join(lineas)

    # Alias en snake_case
    registrar_partida = registrarPartida
    obtener_tabla_ordenada = obtenerTablaOrdenada
    ordenar_puntajes = ordenarPuntajes
    _es_mejor_o_igual = _esMejorOIgual
    _insertion_sort = _insertionSort
    _merge_sort = _mergeSort
    _cargar_puntajes = _cargarPuntajes
    _guardar_puntajes = _guardarPuntajes