# Rutas del cazador con caché e invalidación fina (spec 005; plan 005, D2 y D5; T012 a T014).
#
# Todos los cazadores persiguen la misma sala, así que una sola búsqueda desde el jugador sirve
# para todos (§5.1, pregunta 1 de §8). Esa búsqueda se corta en el mayor rango activo (PR-010)
# y se reutiliza mientras se pueda demostrar que nada cambió su resultado (§5.2, FR-041).
#
# Por qué basta con saber si la tabla de distancias cambió: la decisión del cazador depende de
# la tabla y de las salidas actuales de su sala, y esas salidas se leen en vivo en cada decisión
# (elegirPrimerPaso). Si la tabla no cambia, la decisión es la misma que la de un cálculo desde
# cero (FR-039).

from model.Dijkstra import calcularDistancias, puertaAbierta, EspacioBusqueda


class RutasCazador:

    def __init__(self, cantidadSalas=0):
        self._espacio = EspacioBusqueda(cantidadSalas) if cantidadSalas > 0 else None
        self._distancias = None
        self._salaJugador = None
        self._cota = None
        self.recalculos = 0            # búsquedas hechas (para el bench, PR-012)
        self.invalidaciones = 0        # veces que un evento obligó a recalcular
        self.puertasIgnoradas = 0      # cambios de puerta que se demostró que no afectan

    # ------------------------------------------------------------------ consulta
    def distanciasPara(self, salaJugador, rangoNecesario, cotaActual):
        """Distancias al jugador válidas para un cazador de rango `rangoNecesario`.

        cotaActual: función sin argumentos que devuelve el mayor rango entre los cazadores
        activos. Solo se llama si hay que recalcular.

        Recalcula si (FR-040):
          - no hay cálculo válido (nunca se hizo, o un evento lo invalidó);
          - el jugador está en otra sala (cubre movimiento, pergamino y carga de partida);
          - el rango pedido supera la cota del cálculo (se activó un cazador de más rango).
        """
        if (self._distancias is None
                or self._salaJugador is not salaJugador
                or rangoNecesario > self._cota):
            cota = cotaActual()
            if cota < rangoNecesario:
                cota = rangoNecesario
            self._distancias = calcularDistancias(salaJugador, puertaAbierta, cota, self._espacio)
            self._salaJugador = salaJugador
            self._cota = cota
            self.recalculos += 1
        return self._distancias

    # ------------------------------------------------------------------ eventos
    def invalidar(self):
        """Descarta el cálculo. Se usa cuando no se puede saber qué cambió (pergamino, restaurar)."""
        if self._distancias is not None:
            self.invalidaciones += 1
        self._distancias = None

    def puertaCambio(self, puerta, seAbrio):
        """Decide si el cambio de `puerta` puede alterar alguna distancia (plan 005, D5).

        Con u, v las salas de la puerta y c su costo; una distancia desconocida o mayor que la
        cota cuenta como infinita:
          - cierre: la tabla no cambia si la salida no está en ningún camino mínimo, es decir,
            si no se cumple dist(u) + c = dist(v) ni dist(v) + c = dist(u);
          - apertura: la tabla no cambia si no aparece ningún camino más corto dentro de la cota,
            es decir, si no se cumple dist(u) + c < dist(v) ni dist(v) + c < dist(u).
        En cualquier otro caso se invalida. Si la puerta no conoce sus salas, se invalida.
        """
        if self._distancias is None:
            return
        u = puerta.salaA
        v = puerta.salaB
        c = puerta.costo
        if u is None or v is None or c is None:
            self.invalidar()
            return
        du = self._distancias.de(u)
        dv = self._distancias.de(v)
        if seAbrio:
            afecta = self._mejora(du, c, dv) or self._mejora(dv, c, du)
        else:
            afecta = (du is not None and dv is not None
                      and (du + c == dv or dv + c == du))
        if afecta:
            self.invalidar()
        else:
            self.puertasIgnoradas += 1

    def _mejora(self, desde, costo, hasta):
        """¿Llegar por la puerta nueva acorta `hasta` sin salir de la cota?"""
        if desde is None:
            return False
        nueva = desde + costo
        if hasta is not None:
            return nueva < hasta
        # `hasta` es desconocida: hoy está fuera de la cota o es inalcanzable. Solo cambia algo
        # si el camino nuevo la deja dentro de la cota.
        return self._cota is None or nueva <= self._cota
