import random
import time
import os

from model.cache.CacheFichas import CacheFichas
from model.cache.PersistenciaCache import guardarCache, cargarCache

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

def simularCarga(capacidad, peticiones):
    cache = CacheFichas(capacidad = capacidad)
    llamadasExternas = 0

    def cargadorSimulado(lote):
        nonlocal llamadasExternas
        llamadasExternas += len(lote)
        return[(id_f, f"datos_{id_f}") for id_f in lote]

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

def main():
    azar = random.Random(SEMILLA)
    capacidades = (5, 10, 25, 50)

    print(f"semilla={SEMILLA}  peticiones={NUMERO_PETICIONES}")
    print(f"{'patron':<12}{'cap':>6}{'aciertos':>10}{'fallos':>10}{'hit_rate':>12}{'desalojos':>12}{'ms':>10}")

    pruebas = [("uniforme", generarSolicitudesUniformes(NUMERO_PETICIONES, TOTAL_FICHAS_CATALOGO, azar)), ("sesgado", generarSolicitudesSesgadas(NUMERO_PETICIONES, TOTAL_FICHAS_CATALOGO, azar))]

    for nombre, solicitudes in pruebas:
        for cap in capacidades:
            res = simularCarga(cap, solicitudes)
            print(f"{nombre:<12}{cap:>6}{res['aciertos']:>10}{res['fallos']:>10}{res['hitRate']:>11.1f}%{res['desalojos']:>12}{res['tiempoMs']:>10.2f}")

    print("\n--- Persistencia (Arranque) ---")
    for n in (25, 50, 100):
        solicitudes_arranque = generarSolicitudesSesgadas(n, TOTAL_FICHAS_CATALOGO, azar)
        datos = benchPersistencia(25, solicitudes_arranque)
        print(f"peticiones={n:<4} vacia={datos['llamadasVacia']:<3} restaurada={datos['llamadasRestaurada']:<3} ahorro={datos['porcentajeAhorro']:.1f}%")


if __name__ == "__main__":
    main()