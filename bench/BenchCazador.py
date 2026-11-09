# Benchmark de rutas del cazador (Parte II §5.1, §5.2, §6.1, §6.3).
# Especificación: specs/005-rutas-e-invalidacion (PR-009 a PR-013). Plan: mediciones 1 a 4.
#
# Cada sección verifica primero que mide lo que dice medir (PR-013):
#   - las alternativas comparadas toman exactamente las mismas decisiones;
#   - en el ciclo de eventos ocurren decisiones de cazador de verdad.
# Si una verificación falla, la sección se detiene con un error en vez de reportar tiempos.
#
# Todas las criptas son sintéticas y deterministas por semilla (PR-011).

import random
import time

from model.Entidades import Sala, Salida, Puerta, Enemigo
from model.Salas import IndiceOrdenado
from model.Tabla import Tabla
from model.Constantes import DIRECCIONES, ACC_ESPERAR
from model.Acciones import Accion
from model.Dijkstra import MinHeapDijkstra, dijkstraDesde
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

        # Verificación (PR-013): ambas alternativas deciden lo mismo para cada cazador
        dist = dijkstraDesde(jugador, salas)
        for c in cazadores:
            a = _destinoDe(elegirPasoCazador(c, jugador, dist))
            b = _destinoDe(_decisionIndividual(c, jugador))
            if a != b:
                raise AssertionError("Decisiones distintas para %s: compartido %s, individual %s" % (c.instancia, a, b))

        repeticiones = 30
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            dist = dijkstraDesde(jugador, salas)
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
    print("  Compara la búsqueda completa (actual) contra la búsqueda acotada al rango.")
    print("  %-7s | %-6s | %-22s | %-22s" % ("Salas", "Rango", "Completa ms (salas)", "Acotada ms (salas)"))
    for lado in (10, 32, 71):
        salas, lista, _ = _cuadricula(lado, lado, SEMILLA)
        jugador = lista[(lado // 2) * lado + lado // 2]
        for rango in (150, 2000):
            vecino = jugador.salidas[0].destino
            cazadores = [_cazador("c-cerca", vecino, rango)] + _repartirCazadores(lista, 9, rango, SEMILLA, jugador)

            # Verificación (PR-013): acotar no cambia ninguna decisión
            completa = dijkstraDesde(jugador, salas)
            acotada = dijkstraDesde(jugador, salas, rangoMax=rango)
            for c in cazadores:
                if _destinoDe(elegirPasoCazador(c, jugador, completa)) != _destinoDe(elegirPasoCazador(c, jugador, acotada)):
                    raise AssertionError("La búsqueda acotada cambió la decisión de %s" % c.instancia)

            repeticiones = 20 if lado < 71 else 5
            t0 = time.perf_counter()
            for _ in range(repeticiones):
                dijkstraDesde(jugador, salas)
            tCompleta = (time.perf_counter() - t0) / repeticiones * 1000
            t0 = time.perf_counter()
            for _ in range(repeticiones):
                dijkstraDesde(jugador, salas, rangoMax=rango)
            tAcotada = (time.perf_counter() - t0) / repeticiones * 1000
            print("  %-7d | %-6d | %10.3f (%7d)   | %10.3f (%7d)" %
                  (lado * lado, rango, tCompleta, len(completa), tAcotada, len(acotada)))
    print("  (salas) = salas con distancia registrada en la búsqueda.")


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
    """Cuenta decisiones de cazador y búsquedas envolviendo las funciones que usa el modelo."""

    def __init__(self):
        self.decisiones = 0
        self.busquedas = 0
        self._originales = None

    def __enter__(self):
        self._originales = (moduloJuego.elegirPasoCazador, moduloJuego.dijkstraDesde)
        decidir, buscar = self._originales

        def decidirContando(*args, **kwargs):
            self.decisiones += 1
            return decidir(*args, **kwargs)

        def buscarContando(*args, **kwargs):
            self.busquedas += 1
            return buscar(*args, **kwargs)

        moduloJuego.elegirPasoCazador = decidirContando
        moduloJuego.dijkstraDesde = buscarContando
        return self

    def __exit__(self, *exc):
        moduloJuego.elegirPasoCazador, moduloJuego.dijkstraDesde = self._originales
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
    """Abre o cierra una puerta como lo haría un evento del juego y avisa al cálculo de rutas.

    Mientras el modelo use la bandera gruesa, avisar = invalidar. Cuando exista el componente de
    rutas del plan 005 (D5), este es el único lugar del bench que hay que adaptar.
    """
    modelo.asignar(puerta, "cerrada", not puerta.cerrada)
    modelo._rutasCazadorValidas = False


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


def _medirCiclos(modelo, ciclos, escenario, semilla, recalcularSiempre=False):
    """Ejecuta `ciclos` decisiones de esperar del jugador. Devuelve (tiempos ms, traza, contador)."""
    azar = random.Random(semilla)
    puertas = _puertasNoCriticas(modelo)
    critica = _puertaEnCaminoMinimo(modelo) if escenario == "C" else None
    if recalcularSiempre:
        original = modelo._obtenerDistanciasCazador

        def siempre():
            modelo._rutasCazadorValidas = False
            return original()
        modelo._obtenerDistanciasCazador = siempre
    tiempos = []
    traza = []
    with _Contador() as contador:
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
        for nombre, siempre in (("recalcular siempre", True), ("bandera gruesa", False)):
            modelo = _modeloConCazadores(30, 30, 10 ** 6, SEMILLA)
            tiempos, traza, cont = _medirCiclos(modelo, 30, escenario, SEMILLA, recalcularSiempre=siempre)
            if cont.decisiones == 0:
                raise AssertionError("Escenario %s: no ocurrió ninguna decisión de cazador" % escenario)
            trazas.append(traza)
            print("  %-3s | %-18s | %10.3f | %10.3f | %10d | %10d | %d de %d" %
                  (escenario, nombre, sum(tiempos) / len(tiempos), max(tiempos), cont.busquedas, cont.decisiones,
                   cont.ciclosConDecisiones, len(tiempos)))
        if trazas[0] != trazas[1]:
            raise AssertionError("Escenario %s: las estrategias produjeron partidas distintas" % escenario)
    print("  Verificación: en cada escenario, todas las estrategias producen la misma partida.")
    print("  (La invalidación fina del plan 005, D5, se agrega aquí cuando exista.)")


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


if __name__ == "__main__":
    main()
