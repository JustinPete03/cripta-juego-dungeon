from model.efectos import efectosJuego


class efectosTrampa(efectosJuego):
    """Extiende los efectos de Jurnier con lo que el contenido declara en cada ficha de trampa.

    model/efectos.py no se modifica: aquí solo se lee el campo opcional "veneno" (daño por pulso).
    §2.10 fija la regla del veneno pero no el nombre del campo, y la ficha publicada de trampa trae
    solo {id, nombre, clase, daño, rearme} (ejemplo de §4.2 y las fichas de .cache_cripta): sin
    "veneno" la trampa se limita a su golpe, que es lo que hace el servicio de hoy. El camino con
    veneno lo cubre tests/pruebaTrampaVeneno.py, que declara su propia ficha.
    """

    def alActivarTrampa(self, modelo, trampa, ficha):
        cantidad = ficha.get("veneno")
        if not cantidad:
            return
        self.aplicarVeneno(modelo, modelo.jugador, int(cantidad))
