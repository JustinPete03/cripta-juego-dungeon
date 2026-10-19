import json
import os

from model.ordenamiento.Selector import ordenar

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
        # Delegado en el selector automático de la sección 4.9: en el proyecto hay una sola
        # implementación de inserción y mezcla, y esta tabla no va a mantener la suya.
        return ordenar(lista, self._clave, False)

    @staticmethod
    def _clave(registro: dict):
        # Criterio (sección 2.12): victorias primero -> menor tiempo final -> menos acciones ->
        # más enemigos derrotados. Una tupla ascendente lo expresa sin comparaciones a medida.
        return (0 if registro.get("victoria") else 1,
                registro.get("tiempo_final", 0),
                registro.get("acciones_ejecutadas", 0),
                -registro.get("enemigos_derrotados", 0))

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
    _cargar_puntajes = _cargarPuntajes
    _guardar_puntajes = _guardarPuntajes