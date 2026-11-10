# Benchmark de rutas del cazador (Parte II §5.1, §5.2, §6.1, §6.3).
# Especificación: specs/005-rutas-e-invalidacion (PR-009 a PR-013). Plan: mediciones 1 a 4.
#
# Cada sección verifica primero que mide lo que dice medir (PR-013):
#   - las alternativas comparadas toman exactamente las mismas decisiones;
#   - en el ciclo de eventos ocurren decisiones de cazador de verdad.
# Si una verificación falla, la sección se detiene con un error en vez de reportar tiempos.
#
# Todas las criptas son sintéticas y deterministas por semilla (PR-011).

import gc
import random
import time

from model.Entidades import Sala, Salida, Puerta, Enemigo
from model.Salas import IndiceOrdenado
from model.Tabla import Tabla
from model.Constantes import DIRECCIONES, ACC_ESPERAR
from model.Acciones import Accion
from model.Dijkstra import (MinHeapDijkstra, dijkstraDesde, calcularDistancias, puertaAbierta,
                            EspacioBusqueda)
from model.Cazador import elegirPasoCazador
import model.Juego as moduloJuego

SEMILLA = 2026
COSTO_MIN = 10
COSTO_MAX = 200


# --------------------------------------------------------------------- criptas sintéticas
def _cuadricula(ancho, alto, semilla):
    """Cuadrícula ancho x alto con costos al azar (10 a 200) y una puerta compartida por par de salas.

    Las salidas se agregan en el orden canónico N, S, E, O, igual que Juego._construirSalas.
    Devuelve (indiceSalas, listaSalas, listaPuertas).
    """
    azar = random.Random(semilla)
    salas = IndiceOrdenado()
    lista = []
    for i in range(ancho * alto):
        sala = Sala(i + 1, "Sala %d" % (i + 1))
        salas.insertar(sala.id, sala)
        lista.append(sala)

    # Costo y puerta de cada conexión: horizontales (x, x+1) y verticales (y, y+1)
    horizontal = [[None] * ancho for _ in range(alto)]
    vertical = [[None] * ancho for _ in range(alto)]
    puertas = []
    for y in range(alto):
        for x in range(ancho):
            if x < ancho - 1:
                horizontal[y][x] = (Puerta(False, None, None), azar.randint(COSTO_MIN, COSTO_MAX))
                puertas.append(horizontal[y][x][0])
            if y < alto - 1:
                vertical[y][x] = (Puerta(False, None, None), azar.randint(COSTO_MIN, COSTO_MAX))
                puertas.append(vertical[y][x][0])

    for y in range(alto):
        for x in range(ancho):
            sala = lista[y * ancho + x]
            vecinos = {}
            if y > 0:
                vecinos["N"] = (lista[(y - 1) * ancho + x], vertical[y - 1][x])
            if y < alto - 1:
                vecinos["S"] = (lista[(y + 1) * ancho + x], vertical[y][x])
            if x < ancho - 1:
                vecinos["E"] = (lista[y * ancho + x + 1], horizontal[y][x])
            if x > 0:
                vecinos["O"] = (lista[y * ancho + x - 1], horizontal[y][x - 1])
            for direccion in DIRECCIONES:
                if direccion in vecinos:
                    destino, (puerta, costo) = vecinos[direccion]
                    salida = Salida(direccion, sala, destino.id, puerta, costo)
                    salida.destino = destino
                    sala.salidas.append(salida)
                    if puerta.salaA is None:
                        puerta.salaA, puerta.salaB, puerta.costo = sala, destino, costo
    for i, sala in enumerate(lista):
        sala.indice = i                # como Juego._construirSalas (spec 005, T004)
    return salas, lista, puertas


def _cazador(nombre, sala, rango):
    c = Enemigo(nombre, "ent_cazador_bench", "Cazador", "cazador", 20, 20, 1, 50, 100, rango=rango)
    c.sala = sala
    return c


def _repartirCazadores(lista, cantidad, rango, semilla, excluir):
    azar = random.Random(semilla)
    cazadores = []
    for i in range(cantidad):
        sala = lista[azar.randrange(len(lista))]
        while sala is excluir:
            sala = lista[azar.randrange(len(lista))]
        cazadores.append(_cazador("c-%03d" % i, sala, rango))
    return cazadores


# --------------------------------------------------------------------- alternativa individual
def _decisionIndividual(cazador, salaJugador):
    """Cálculo individual correcto (plan 005, D2, alternativa): búsqueda desde la sala del cazador.

    Guarda por sala la distancia y el «primer salto» (id de la vecina por la que empieza el camino).
    Al empatar en distancia se queda el primer salto de menor id, así el resultado cumple el
    desempate de §3.2 sin importar el orden de exploración. Se detiene al extraer la sala del
    jugador o al superar el rango. Devuelve (salida, costo) con la misma convención que
    elegirPasoCazador.
    """
    origen = cazador.sala
    if origen is salaJugador:
        return (None, 0)
    rango = cazador.rango
    distancia = Tabla()
    primerSalto = Tabla()
    distancia.guardar(origen.id, 0)
    heap = MinHeapDijkstra()
    heap.empujar(0, origen.id)
    porId = Tabla()
    porId.guardar(origen.id, origen)
    d = None
    while not heap.estaVacio():
        du, uId = heap.extraerMin()
        if du > distancia.obtener(uId):
            continue
        if du > rango:
            break
        if uId == salaJugador.id:
            d = du
            break
        u = porId.obtener(uId)
        for salida in u.salidas:
            if salida.puerta.cerrada:
                continue
            v = salida.destino
            nd = du + salida.costo
            fh = v.id if u is origen else primerSalto.obtener(uId)
            dv = distancia.obtener(v.id)
            if dv is None or nd < dv:
                distancia.guardar(v.id, nd)
                primerSalto.guardar(v.id, fh)
                porId.guardar(v.id, v)
                heap.empujar(nd, v.id)
            elif nd == dv and fh < primerSalto.obtener(v.id):
                primerSalto.guardar(v.id, fh)
    if d is None:
        return (None, 100)
    elegidoId = primerSalto.obtener(salaJugador.id)
    # Hacia la vecina elegida, la salida abierta más barata; empate: orden N, S, E, O (spec Q4)
    mejor = None
    for salida in origen.salidas:
        if salida.destino.id == elegidoId and not salida.puerta.cerrada:
            if mejor is None or salida.costo < mejor.costo:
                mejor = salida
    return (mejor, mejor.costo)


def _destinoDe(decision):
    salida, costo = decision
    return (None if salida is None else salida.destino.id, costo)


# --------------------------------------------------------------------- 1. compartido vs individual
def benchCompartidoVsIndividual():
    print("--- 1. Uno frente a muchos: cálculo compartido frente a individual (§5.1, PR-012) ---")
    salas, lista, _ = _cuadricula(20, 20, SEMILLA)
    jugador = lista[len(lista) // 2]
    print("  Cripta: cuadrícula de %d salas, costos %d a %d, rango 600" % (len(lista), COSTO_MIN, COSTO_MAX))
    print("  %-11s | %-18s | %-18s | %s" % ("Cazadores", "Compartido (ms)", "Individual (ms)", "Decisiones iguales"))
    for cantidad in (1, 10, 30, 60):
        cazadores = _repartirCazadores(lista, cantidad, 600, SEMILLA + cantidad, jugador)

        espacio = EspacioBusqueda(len(lista))
        # Verificación (PR-013): ambas alternativas deciden lo mismo para cada cazador
        dist = calcularDistancias(jugador, puertaAbierta, 600, espacio)
        for c in cazadores:
            a = _destinoDe(elegirPasoCazador(c, jugador, dist))
            b = _destinoDe(_decisionIndividual(c, jugador))
            if a != b:
                raise AssertionError("Decisiones distintas para %s: compartido %s, individual %s" % (c.instancia, a, b))

        repeticiones = 30
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            dist = calcularDistancias(jugador, puertaAbierta, 600, espacio)
            for c in cazadores:
                elegirPasoCazador(c, jugador, dist)
        tCompartido = (time.perf_counter() - t0) / repeticiones * 1000

        t0 = time.perf_counter()
        for _ in range(repeticiones):
            for c in cazadores:
                _decisionIndividual(c, jugador)
        tIndividual = (time.perf_counter() - t0) / repeticiones * 1000
        print("  %-11d | %18.3f | %18.3f | sí (%d de %d)" % (cantidad, tCompartido, tIndividual, cantidad, cantidad))


# --------------------------------------------------------------------- 2. rango pequeño vs grande
def benchRangoPequenoVsGrande():
    print("\n--- 2. Rango pequeño frente a grande, criptas de tamaño creciente (§5.1, PR-010) ---")
    print("  Búsqueda completa (como antes de la spec 005) frente a búsqueda acotada al rango (actual).")
    print("  %-7s | %-6s | %-22s | %-22s" % ("Salas", "Rango", "Completa ms (salas)", "Acotada ms (salas)"))
    for lado in (10, 32, 71):
        salas, lista, _ = _cuadricula(lado, lado, SEMILLA)
        espacio = EspacioBusqueda(len(lista))
        jugador = lista[(lado // 2) * lado + lado // 2]
        for rango in (150, 2000):
            vecino = jugador.salidas[0].destino
            cazadores = [_cazador("c-cerca", vecino, rango)] + _repartirCazadores(lista, 9, rango, SEMILLA, jugador)

            # Verificación (PR-013): acotar no cambia ninguna decisión
            completa = calcularDistancias(jugador, puertaAbierta)
            for c in cazadores:
                antes = _destinoDe(elegirPasoCazador(c, jugador, completa))
                acotada = calcularDistancias(jugador, puertaAbierta, rango, espacio)
                if antes != _destinoDe(elegirPasoCazador(c, jugador, acotada)):
                    raise AssertionError("La búsqueda acotada cambió la decisión de %s" % c.instancia)

            repeticiones = 20 if lado < 71 else 5
            t0 = time.perf_counter()
            for _ in range(repeticiones):
                completa = calcularDistancias(jugador, puertaAbierta, None, espacio)
            tCompleta = (time.perf_counter() - t0) / repeticiones * 1000
            examinadasCompleta = completa.salasExaminadas
            t0 = time.perf_counter()
            for _ in range(repeticiones):
                acotada = calcularDistancias(jugador, puertaAbierta, rango, espacio)
            tAcotada = (time.perf_counter() - t0) / repeticiones * 1000
            print("  %-7d | %-6d | %10.3f (%7d)   | %10.3f (%7d)" %
                  (lado * lado, rango, tCompleta, examinadasCompleta, tAcotada, acotada.salasExaminadas))
    print("  (salas) = salas examinadas por la búsqueda.")


def benchTablaVsSellos():
    print("\n--- 5. Distancias en Tabla frente a arreglo con sellos (plan 005, D3, T022) ---")
    print("  Búsqueda completa desde el centro; mismas distancias en ambas (verificado).")
    print("  %-7s | %-12s | %-12s | %s" % ("Salas", "Tabla ms", "Sellos ms", "Mejora"))
    for lado in (10, 32, 71):
        salas, lista, _ = _cuadricula(lado, lado, SEMILLA)
        espacio = EspacioBusqueda(len(lista))
        origen = lista[(lado // 2) * lado + lado // 2]
        conTabla = calcularDistancias(origen, puertaAbierta)
        conSellos = calcularDistancias(origen, puertaAbierta, None, espacio)
        for sala in lista:
            if conTabla.de(sala) != conSellos.de(sala):
                raise AssertionError("Tabla y sellos dan distancias distintas en la sala %d" % sala.id)
        repeticiones = 20 if lado < 71 else 5
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            calcularDistancias(origen, puertaAbierta)
        tTabla = (time.perf_counter() - t0) / repeticiones * 1000
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            calcularDistancias(origen, puertaAbierta, None, espacio)
        tSellos = (time.perf_counter() - t0) / repeticiones * 1000
        print("  %-7d | %12.3f | %12.3f | %.1fx" % (lado * lado, tTabla, tSellos, tTabla / tSellos))


# --------------------------------------------------------------------- 3 y 4. modelo real
class _FuenteCazadores:
    """Proveedor en memoria para el bench: cuadrícula con costos y cazadores repartidos.

    El jugador tiene vida muy alta para que la partida no termine durante la medición.
    """

    def __init__(self, lado, cantidadCazadores, rango, semilla):
        azar = random.Random(semilla)
        self.total = lado * lado
        self.salas = []
        for y in range(lado):
            for x in range(lado):
                idSala = y * lado + x + 1
                self.salas.append({"id": idSala, "nombre": "Sala %d" % idSala, "salidas": {}})
        for y in range(lado):
            for x in range(lado):
                idSala = y * lado + x + 1
                if x < lado - 1:
                    c = azar.randint(COSTO_MIN, COSTO_MAX)
                    self.salas[idSala - 1]["salidas"]["E"] = {"sala": idSala + 1, "costo": c}
                    self.salas[idSala]["salidas"]["O"] = {"sala": idSala, "costo": c}
                if y < lado - 1:
                    c = azar.randint(COSTO_MIN, COSTO_MAX)
                    self.salas[idSala - 1]["salidas"]["S"] = {"sala": idSala + lado, "costo": c}
                    self.salas[idSala + lado - 1]["salidas"]["N"] = {"sala": idSala, "costo": c}
        self.enemigosPorSala = [[] for _ in range(self.total)]
        for i in range(cantidadCazadores):
            idSala = 2 + azar.randrange(self.total - 1)          # nunca en la sala inicial
            self.enemigosPorSala[idSala - 1].append({"instancia": "c-%03d" % i, "tipo": "ent_cazador_bench"})
        self.fichaCazador = {"id": "ent_cazador_bench", "clase": "enemigo", "nombre": "Cazador",
                             "vida_max": 20, "ataque": 1, "defensa": 50, "velocidad": 100,
                             "comportamiento": "cazador", "rango": rango, "suelta": []}

    def datosGenerales(self):
        return {"id": "cripta-bench", "version": "v1", "sala_inicial": 1, "sala_salida": self.total,
                "llave_salida": "itm_inexistente", "presupuesto_solicitudes": 10 ** 6, "inventario_max": 10,
                "jugador": {"vida_max": 10 ** 9, "ataque": 1, "defensa": 1000, "velocidad": 100}}

    def esqueleto(self):
        return self.salas

    def contenidoSala(self, salaId):
        return {"sala": salaId, "enemigos": list(self.enemigosPorSala[salaId - 1]), "objetos": [], "trampas": []}

    def ficha(self, tipoId):
        if tipoId == "ent_cazador_bench":
            return self.fichaCazador
        raise KeyError(tipoId)

    def anticipar(self, salaId):
        pass

    def asegurarFichas(self, tipoIds):
        pass

    def fijarFichasEnUso(self, productor):
        pass


class _Contador:
    """Cuenta decisiones de cazador (envolviendo la función que usa el motor) y búsquedas
    (contador `recalculos` del componente de rutas del modelo)."""

    def __init__(self, modelo):
        self.modelo = modelo
        self.decisiones = 0
        self._original = None
        self._recalculosIniciales = 0

    @property
    def busquedas(self):
        return self.modelo.rutasCazador.recalculos - self._recalculosIniciales

    def __enter__(self):
        self._original = moduloJuego.elegirPasoCazador
        decidir = self._original

        def decidirContando(*args, **kwargs):
            self.decisiones += 1
            return decidir(*args, **kwargs)

        moduloJuego.elegirPasoCazador = decidirContando
        self._recalculosIniciales = self.modelo.rutasCazador.recalculos
        return self

    def __exit__(self, *exc):
        moduloJuego.elegirPasoCazador = self._original
        return False


def _modeloConCazadores(lado, cantidad, rango, semilla):
    from model.Inventario import Inventario
    from model.Diario import Diario
    fuente = _FuenteCazadores(lado, cantidad, rango, semilla)
    modelo = moduloJuego.Modelo(fuente, semilla, Inventario(fuente), Diario())
    modelo.iniciarPartida()
    # Los enemigos solo existen en salas con contenido incorporado y solo actúan si están activos
    # (P1 §2.4). El bench los incorpora y activa a todos para medir carga real de cazadores.
    for i in range(modelo.salas.cantidad()):
        sala = modelo.salas.enPosicion(i)
        modelo._asegurarContenido(sala)
        modelo._activarDormidos(sala)
    return modelo


def _cambiarPuerta(modelo, puerta):
    """Abre o cierra una puerta como lo hacen los eventos del juego y avisa a las rutas."""
    modelo.asignar(puerta, "cerrada", not puerta.cerrada)
    modelo.rutasCazador.puertaCambio(puerta, not puerta.cerrada)


def _aplicarEstrategia(modelo, estrategia):
    """Configura el componente de rutas del modelo con una de las estrategias comparadas.

    - «recalcular siempre»: cada decisión de cazador hace una búsqueda nueva.
    - «bandera gruesa»: cualquier cambio de puerta invalida (como antes de la spec 005).
    - «invalidación fina»: la del plan 005, D5 (la que usa el juego).
    """
    rutas = modelo.rutasCazador
    if estrategia == "recalcular siempre":
        original = rutas.distanciasPara

        def siempre(*args):
            rutas.invalidar()
            return original(*args)
        rutas.distanciasPara = siempre
    elif estrategia == "bandera gruesa":
        rutas.puertaCambio = lambda puerta, seAbrio: rutas.invalidar()


def _puertasNoCriticas(modelo):
    """Puertas cuyo cierre no deja a nadie sin salida: las horizontales de salas interiores."""
    puertas = []
    for i in range(modelo.salas.cantidad()):
        sala = modelo.salas.enPosicion(i)
        for salida in sala.salidas:
            if salida.direccion == "E":
                puertas.append(salida.puerta)
    return puertas


def _puertaEnCaminoMinimo(modelo):
    """Una puerta que está en un camino mínimo hacia el jugador (escenario C)."""
    dist = dijkstraDesde(modelo.jugador.sala, modelo.salas)
    for i in range(modelo.salas.cantidad()):
        u = modelo.salas.enPosicion(i)
        du = dist.obtener(u.id)
        for salida in u.salidas:
            dv = dist.obtener(salida.destinoId)
            if du is not None and dv is not None and du + salida.costo == dv and salida.direccion == "E":
                return salida.puerta
    return None


def _medirCiclos(modelo, ciclos, escenario, semilla, estrategia="invalidación fina"):
    """Ejecuta `ciclos` decisiones de esperar del jugador. Devuelve (tiempos ms, traza, contador)."""
    azar = random.Random(semilla)
    puertas = _puertasNoCriticas(modelo)
    critica = _puertaEnCaminoMinimo(modelo) if escenario == "C" else None
    _aplicarEstrategia(modelo, estrategia)
    # Libera la basura de mediciones anteriores para que una pausa del recolector causada por
    # otra sección no se cuente como costo de este ciclo.
    gc.collect()
    tiempos = []
    traza = []
    with _Contador(modelo) as contador:
        contador.ciclosConDecisiones = 0
        for _ in range(ciclos):
            antes = contador.decisiones
            if escenario == "B":
                _cambiarPuerta(modelo, puertas[azar.randrange(len(puertas))])
            elif escenario == "C" and critica is not None:
                _cambiarPuerta(modelo, critica)
            t0 = time.perf_counter()
            modelo.ejecutar(Accion(ACC_ESPERAR))
            tiempos.append((time.perf_counter() - t0) * 1000)
            if contador.decisiones > antes:
                contador.ciclosConDecisiones += 1
            traza.append(tuple(e.sala.id for e in modelo.enemigosVivos))
    return tiempos, traza, contador


def _resumen(tiempos):
    orden = sorted(tiempos)
    n = len(orden)
    return orden[n // 2], orden[min(n - 1, (n * 95) // 100)], orden[-1]


def benchInvalidacion():
    print("\n--- 3. Reutilización frente a recálculo, puertas estables e inestables (§5.2, PR-012) ---")
    print("  Modelo real, 30 cazadores activos, cuadrícula de 900 salas, 30 ciclos.")
    print("  A: puertas estables | B: una puerta al azar cambia cada ciclo | C: cambia una puerta de un camino mínimo")
    print("  %-3s | %-18s | %-10s | %-10s | %-10s | %-10s | %s" % ("Esc", "Estrategia", "Media ms", "Peor ms", "Búsquedas", "Decisiones", "Ciclos c/ decisión"))
    for escenario in ("A", "B", "C"):
        trazas = []
        for nombre in ("recalcular siempre", "bandera gruesa", "invalidación fina"):
            modelo = _modeloConCazadores(30, 30, 10 ** 6, SEMILLA)
            tiempos, traza, cont = _medirCiclos(modelo, 30, escenario, SEMILLA, nombre)
            if cont.decisiones == 0:
                raise AssertionError("Escenario %s: no ocurrió ninguna decisión de cazador" % escenario)
            trazas.append(traza)
            print("  %-3s | %-18s | %10.3f | %10.3f | %10d | %10d | %d de %d" %
                  (escenario, nombre, sum(tiempos) / len(tiempos), max(tiempos), cont.busquedas, cont.decisiones,
                   cont.ciclosConDecisiones, len(tiempos)))
        if trazas[0] != trazas[1] or trazas[0] != trazas[2]:
            raise AssertionError("Escenario %s: las estrategias produjeron partidas distintas" % escenario)
    print("  Verificación: en cada escenario, las tres estrategias producen la misma partida.")


def benchCicloEventos():
    print("\n--- 4. Ciclo de eventos con decenas de cazadores activos (§6.1, PR-009, límite 20 ms) ---")
    for cantidad in (30, 60):
        modelo = _modeloConCazadores(30, cantidad, 10 ** 6, SEMILLA)
        tiempos, _, cont = _medirCiclos(modelo, 40, "B", SEMILLA)
        if cont.decisiones == 0:
            raise AssertionError("No ocurrió ninguna decisión de cazador: la medición no sería válida")
        mediana, p95, peor = _resumen(tiempos)
        print("  %2d cazadores | ciclos con decisiones: %d de %d | decisiones: %d | mediana %.3f ms | p95 %.3f ms | peor %.3f ms | %s" %
              (cantidad, cont.ciclosConDecisiones, len(tiempos), cont.decisiones, mediana, p95, peor,
               "cumple" if peor < 20.0 else "NO CUMPLE"))
    print("  Cuadrícula de 900 salas, escenario B (una puerta cambia cada ciclo). El peor caso incluye los puntos de control de la línea de tiempo.")


def main():
    benchCompartidoVsIndividual()
    benchRangoPequenoVsGrande()
    benchInvalidacion()
    benchCicloEventos()
    benchTablaVsSellos()


if __name__ == "__main__":
    main()
