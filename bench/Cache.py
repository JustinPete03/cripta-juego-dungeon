import random
import time
import os
import tempfile

from model.cache.CacheFichas import CacheFichas
from adapters.GuardadoCache import guardarCache, cargarCache
from adapters.AlmacenFichasDisco import AlmacenFichasDisco

#creamos constantes fijas para evidencias/resultados del analisis
SEMILLA = 2026
TOTAL_FICHAS_CATALOGO = 60
NUMERO_PETICIONES= 1000    #cantidad de peticiones propuesta para la simulacion
ARCHIVO_BENCH_TEMP = "cache_bench_temp.json"
VERSION_BENCH = "1.0.0"

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

class CacheFifo(CacheFichas):
    #Política descartada: desaloja la ficha que lleva más tiempo en memoria, aunque se haya usado hace poco.
    def consultarFicha(self, idFicha):
        nodo = self.buscarNodo(idFicha)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        return nodo.ficha

def simularCarga(capacidad, peticiones, claseCache=CacheFichas):
    cache = claseCache(capacidad=capacidad)
    llamadasExternas = 0

    def cargadorSimulado(lote):
        nonlocal llamadasExternas
        llamadasExternas += len(lote)
        return[(idF, f"datos_{idF}") for idF in lote]

    t0 = time.perf_counter()

    for idFicha in peticiones:
        cache.obtenerFichas([idFicha], cargadorSimulado)

    tiempoMs = (time.perf_counter() - t0) * 1000

    totalConsultas = cache.aciertos + cache.fallos
    hitRate = (cache.aciertos / totalConsultas * 100) if totalConsultas > 0 else 0.0

    return{
        "capacidad": capacidad,
        "aciertos" : cache.aciertos,
        "fallos" : cache.fallos,
        "desalojos" : cache.desalojos,
        "hitRate" : hitRate,
        "llamadasExternas" : llamadasExternas,
        "tiempoMs" : tiempoMs,
    }

def benchPersistencia(capacidad, peticiones):
    #Inicio sin archivo previo
    cacheVacia = CacheFichas(capacidad = capacidad)
    llamadasVacia = 0

    def cargadorVacia(lote):
        nonlocal llamadasVacia
        llamadasVacia += len(lote)
        return[(idF, f"datos_{idF}") for idF in lote]

    for idFicha in peticiones:
        cacheVacia.obtenerFichas([idFicha], cargadorVacia)

    if not guardarCache(ARCHIVO_BENCH_TEMP, VERSION_BENCH, cacheVacia):
        print("Aviso: no se pudo guardar la cache de prueba")

    #Restaurando desde el disco
    cacheRestaurada = CacheFichas(capacidad = capacidad)
    cargarCache(ARCHIVO_BENCH_TEMP, VERSION_BENCH, cacheRestaurada)
    llamadasRestaurada = 0

    def cargadorRestaurada(lote):
        nonlocal llamadasRestaurada
        llamadasRestaurada += len(lote)
        return[(idF, f"datos_{idF}") for idF in lote]

    try:
        for idFicha in peticiones:
            cacheRestaurada.obtenerFichas([idFicha], cargadorRestaurada)
    finally:
        if os.path.exists(ARCHIVO_BENCH_TEMP): #eliminar el archivo temporal
            os.remove(ARCHIVO_BENCH_TEMP)

    solicitudesAhorradas = llamadasVacia - llamadasRestaurada
    porcentajeAhorro = (solicitudesAhorradas / llamadasVacia * 100) if llamadasVacia > 0 else 0.0

    return{
        "llamadasVacia" : llamadasVacia,
        "llamadasRestaurada" : llamadasRestaurada,
        "ahorro" : solicitudesAhorradas,
        "porcentajeAhorro" : porcentajeAhorro,
    }

def cargadorDisco(lote):
    return [(idF, f"datos_{idF}") for idF in lote]

def correrPeticiones(cache, peticiones):
    t0 = time.perf_counter()
    for idFicha in peticiones:
        cache.obtenerFichas([idFicha], cargadorDisco)
    return (time.perf_counter() - t0) * 1000

def benchDisco(capacidad, peticiones):
    cacheSola = CacheFichas(capacidad=capacidad)
    msSola = correrPeticiones(cacheSola, peticiones)

    with tempfile.TemporaryDirectory() as carpeta:
        cacheConDisco = CacheFichas(capacidad=capacidad, almacen=AlmacenFichasDisco(carpeta))
        msConDisco = correrPeticiones(cacheConDisco, peticiones)

    ahorro = cacheSola.llamadasRed - cacheConDisco.llamadasRed
    porcentaje = (ahorro / cacheSola.llamadasRed * 100) if cacheSola.llamadasRed > 0 else 0.0
    return {
        "redSola": cacheSola.llamadasRed,
        "redConDisco": cacheConDisco.llamadasRed,
        "aciertosDisco": cacheConDisco.aciertosDisco,
        "porcentajeAhorro": porcentaje,
        "msSola": msSola,
        "msConDisco": msConDisco,
    }

TAMANOS_BUSQUEDA = (25, 100, 400, 1600)
REPETICIONES_BUSQUEDA = 2000

def benchBusqueda(n):
    azar = random.Random(SEMILLA)   #generador propio: no altera los otros resultados
    cache = CacheFichas(capacidad=n)
    for i in range(n):
        cache.guardarFicha(f"ficha_{i}", f"datos_{i}")

    presentes = [f"ficha_{azar.randrange(n)}" for _ in range(REPETICIONES_BUSQUEDA)]
    ausentes = [f"ausente_{i}" for i in range(REPETICIONES_BUSQUEDA)]
    peorCaso = "ficha_0"    #la primera que se guardó queda al final de la lista

    resultados = {}
    for nombre, ids in (("presente", presentes), ("ausente", ausentes), ("peor", [peorCaso] * REPETICIONES_BUSQUEDA)):
        t0 = time.perf_counter()
        for idFicha in ids:
            cache.buscarNodo(idFicha)
        resultados[nombre] = (time.perf_counter() - t0) / REPETICIONES_BUSQUEDA * 1_000_000
    return resultados

def main():
    azar = random.Random(SEMILLA)
    capacidades = (5, 10, 25, 50)
    politicas = (("LRU", CacheFichas), ("FIFO", CacheFifo))

    print(f"semilla={SEMILLA}  peticiones={NUMERO_PETICIONES}")
    print(f"{'patron':<12}{'politica':<10}{'cap':>6}{'aciertos':>10}{'fallos':>10}{'hit_rate':>12}{'desalojos':>12}{'ms':>10}")

    pruebas = [("uniforme", generarSolicitudesUniformes(NUMERO_PETICIONES, TOTAL_FICHAS_CATALOGO, azar)), ("sesgado", generarSolicitudesSesgadas(NUMERO_PETICIONES, TOTAL_FICHAS_CATALOGO, azar))]

    for nombre, solicitudes in pruebas:
        for cap in capacidades:
            for nombrePolitica, claseCache in politicas:
                res = simularCarga(cap, solicitudes, claseCache)
                print(f"{nombre:<12}{nombrePolitica:<10}{cap:>6}{res['aciertos']:>10}{res['fallos']:>10}{res['hitRate']:>11.1f}%{res['desalojos']:>12}{res['tiempoMs']:>10.2f}")

    print("\n--- Recuperacion desde disco (patron sesgado, mismas peticiones) ---")
    print(f"{'cap':>6}{'redSola':>10}{'redConDisco':>13}{'aciertosDisco':>15}{'ahorro':>10}{'msSola':>10}{'msConDisco':>12}")
    solicitudesSesgadas = pruebas[1][1]
    for cap in capacidades:
        d = benchDisco(cap, solicitudesSesgadas)
        print(f"{cap:>6}{d['redSola']:>10}{d['redConDisco']:>13}{d['aciertosDisco']:>15}{d['porcentajeAhorro']:>9.1f}%{d['msSola']:>10.2f}{d['msConDisco']:>12.2f}")

    print("\n--- Búsqueda en la cache (µs por búsqueda) ---")
    print(f"{'n':>6}{'presente':>12}{'ausente':>12}{'peorCaso':>12}")
    for n in TAMANOS_BUSQUEDA:
        r = benchBusqueda(n)
        print(f"{n:>6}{r['presente']:>12.2f}{r['ausente']:>12.2f}{r['peor']:>12.2f}")

    print("\n--- Persistencia (Arranque) ---")
    for n in (25, 50, 100):
        solicitudesArranque = generarSolicitudesSesgadas(n, TOTAL_FICHAS_CATALOGO, azar)
        datos = benchPersistencia(25, solicitudesArranque)
        print(f"peticiones={n:<4} vacia={datos['llamadasVacia']:<3} restaurada={datos['llamadasRestaurada']:<3} ahorro={datos['porcentajeAhorro']:.1f}%")


if __name__ == "__main__":
    main()