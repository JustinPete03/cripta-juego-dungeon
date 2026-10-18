from model.efectos import efectosJuego


class efectosTrampa(efectosJuego):
    """Extiende los efectos de Jurnier con lo que el contenido declara en cada ficha de trampa.
    model/efectos.py no se modifica: aquí solo se lee el campo opcional "veneno" (daño por pulso)."""

    def alActivarTrampa(self, modelo, trampa, ficha):
        cantidad = ficha.get("veneno")
        if not cantidad:
            return
        self.aplicarVeneno(modelo, modelo.jugador, int(cantidad))
