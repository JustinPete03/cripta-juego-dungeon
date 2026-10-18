# Bench de la caché que usa el juego: model/cache_estructuras.CacheCatalogo (tabla hash con
# encadenamiento, LRU y protección de fichas en uso) y su variante con disco del adaptador.
# model/cache/CacheFichas.py no se mide aquí: es la alternativa que quedó fuera del camino vivo.
import random
import tempfile
import time

from adapters.ProveedorRed import CacheConDisco
from adapters.persistenciaCache import AlmacenamientoPersistenteCache
from model.cache_estructuras import CacheCatalogo

#creamos constantes fijas para evidencias/resultados del analisis
SEMILLA = 2026
TOTAL_FICHAS_CATALOGO = 60
NUMERO_PETICIONES = 1000    #cantidad de peticiones propuesta para la simulacion
VERSION_BENCH = "bench"

def generarSolicitudesUniformes(nPeticiones, totalFichas, azar): #este metodo hace que cualquier ficha tenga igual probabilidad de aparecer
    return[f"ficha_{azar.randint(1, totalFichas)}" for _ in range(nPeticiones)]

def generarSolicitudesSesgadas(nPeticiones, totalFichas, azar): #divide las fichas en dos grupos (20% de fichas frecuentes y un 80% de fichas raras)
    cantidadFrecuentes = max(2, int(totalFichas * 0.2))
    fichasFrecuentes = [f"ficha_{i}" for i in range(1, cantidadFrecuentes + 1)]
    fichasRaras = [f"ficha_{i}" for i in range(cantidadFrecuentes + 1, totalFichas + 1)]

    solicitudes = []
    for _ in range(nPeticiones):
        if azar.random() < 0.8:
            solicitudes.append(azar.choice(fichasFrecuentes))
        else:
            solicitudes.append(azar.choice(fichasRaras))

    return solicitudes

class CacheFifo(CacheCatalogo):
    """Política descartada (sección 4.4): desaloja la ficha más antigua aunque se use seguido.

    Reusa la máquina de desalojo de la base y solo deja de refrescar la marca de último acceso,
    así la comparación de políticas corre sobre el mismo código y no sobre dos implementaciones."""

    def _entrada(self, idEntidad):
        for entrada in self.cubetas[self._hash(idEntidad)]:
            if entrada.id_entidad == idEntidad:
                return entrada
        return None

    def _sinRefrescar(self, metodo, idEntidad, *extra):
        entrada = self._entrada(idEntidad)
        marca = None if entrada is None else entrada.ultimo_acceso
        resultado = metodo(self, idEntidad, *extra)
        if marca is not None:
            entrada.ultimo_acceso = marca
        return resultado

    def contiene(self, idEntidad, registrar_metrica=True):
        return self._sinRefrescar(CacheCatalogo.contiene, idEntidad, registrar_metrica)

    def obtener(self, idEntidad):
        return self._sinRefrescar(CacheCatalogo.obtener, idEntidad)

def correrPeticiones(cache, peticiones):
    """Lee y, en lo que falta, inserta como haría el adaptador tras una respuesta del servicio."""
    llamadasRed = 0
    t0 = time.perf_counter()
    for idFicha in peticiones:
        if cache.obtener(idFicha) is None:
            llamadasRed += 1
            cache.insertar(idFicha, {"id": idFicha, "nombre": idFicha})
    return llamadasRed, (time.perf_counter() - t0) * 1000

def simularCarga(capacidad, peticiones, claseCache=CacheCatalogo):
    cache = claseCache(capacidad)
    llamadasExternas, tiempoMs = correrPeticiones(cache, peticiones)
    totalConsultas = cache.aciertos + cache.fallos
    hitRate = (cache.aciertos / totalConsultas * 100) if totalConsultas > 0 else 0.0
    return {
        "capacidad": capacidad,
        "aciertos": cache.aciertos,
        "fallos": cache.fallos,
        "desalojos": cache.desalojos,
        "hitRate": hitRate,
        "llamadasExternas": llamadasExternas,
        "tiempoMs": tiempoMs,
    }

def benchDisco(capacidad, peticiones):
    """Costo de la caché con disco (sección 4.4) sobre el mismo almacén que usa el adaptador."""
    with tempfile.TemporaryDirectory() as carpeta:
        almacen = AlmacenamientoPersistenteCache(carpeta)

        redSola, msSola = correrPeticiones(CacheCatalogo(capacidad), peticiones)
        primera, msPrimera = correrPeticiones(CacheConDisco(capacidad, almacen, VERSION_BENCH), peticiones)
        # Segunda sesión: la RAM arranca vacía pero el directorio de caché ya está poblado.
        restaurada, msRestaurada = correrPeticiones(
            CacheConDisco(capacidad, almacen, VERSION_BENCH), peticiones)

    ahorro = redSola - restaurada
    porcentaje = (ahorro / redSola * 100) if redSola > 0 else 0.0
    return {
        "redSola": redSola,
        "redConDisco": primera,
        "redRestaurada": restaurada,
        "ahorro": ahorro,
        "porcentajeAhorro": porcentaje,
        "msSola": msSola,
        "msConDisco": msPrimera,
        "msRestaurada": msRestaurada,
    }

TAMANOS_BUSQUEDA = (25, 100, 400, 1600)
REPETICIONES_BUSQUEDA = 2000

def benchBusqueda(n):
    azar = random.Random(SEMILLA)   #generador propio: no altera los otros resultados
    cache = CacheCatalogo(n)
    for i in range(n):
        cache.insertar(f"ficha_{i}", {"id": f"ficha_{i}", "nombre": f"ficha_{i}"})

    presentes = [f"ficha_{azar.randrange(n)}" for _ in range(REPETICIONES_BUSQUEDA)]
    ausentes = [f"ausente_{i}" for i in range(REPETICIONES_BUSQUEDA)]

    micro = {}
    for nombre, ids in (("presente", presentes), ("ausente", ausentes)):
        t0 = time.perf_counter()
        for idFicha in ids:
            cache.obtener(idFicha)
        micro[nombre] = (time.perf_counter() - t0) / REPETICIONES_BUSQUEDA * 1_000_000
    micro["cubetas"] = cache.num_cubetas
    micro["cadena"] = cache.cantidad_actual / cache.num_cubetas
    return micro

def main():
    azar = random.Random(SEMILLA)
    capacidades = (5, 10, 25, 50)
    politicas = (("LRU", CacheCatalogo), ("FIFO", CacheFifo))

    print(f"semilla={SEMILLA}  peticiones={NUMERO_PETICIONES}")
    print(f"{'patron':<12}{'politica':<10}{'cap':>6}{'aciertos':>10}{'fallos':>10}{'hit_rate':>12}{'desalojos':>12}{'ms':>10}")

    pruebas = [("uniforme", generarSolicitudesUniformes(NUMERO_PETICIONES, TOTAL_FICHAS_CATALOGO, azar)), ("sesgado", generarSolicitudesSesgadas(NUMERO_PETICIONES, TOTAL_FICHAS_CATALOGO, azar))]

    for nombre, solicitudes in pruebas:
        for cap in capacidades:
            for nombrePolitica, claseCache in politicas:
                res = simularCarga(cap, solicitudes, claseCache)
                print(f"{nombre:<12}{nombrePolitica:<10}{cap:>6}{res['aciertos']:>10}{res['fallos']:>10}{res['hitRate']:>11.1f}%{res['desalojos']:>12}{res['tiempoMs']:>10.2f}")

    print("\n--- Cache con disco: peticiones al servicio (patron sesgado, mismas peticiones) ---")
    print(f"{'cap':>6}{'sinDisco':>10}{'primera':>10}{'restaurada':>13}{'ahorro':>9}{'msPrimera':>11}{'msRestaurada':>14}")
    solicitudesSesgadas = pruebas[1][1]
    for cap in capacidades:
        d = benchDisco(cap, solicitudesSesgadas)
        print(f"{cap:>6}{d['redSola']:>10}{d['redConDisco']:>10}{d['redRestaurada']:>13}"
              f"{d['porcentajeAhorro']:>8.1f}%{d['msConDisco']:>11.2f}{d['msRestaurada']:>14.2f}")

    print("\n--- Búsqueda en la cache viva (µs por búsqueda) ---")
    print(f"{'n':>6}{'presente':>12}{'ausente':>12}{'cubetas':>10}{'cadena':>9}")
    for n in TAMANOS_BUSQUEDA:
        r = benchBusqueda(n)
        print(f"{n:>6}{r['presente']:>12.2f}{r['ausente']:>12.2f}{r['cubetas']:>10}{r['cadena']:>9.2f}")


if __name__ == "__main__":
    main()
