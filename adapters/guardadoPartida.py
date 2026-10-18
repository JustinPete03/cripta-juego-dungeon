# Guardado de la partida completa (secciones 4.10 y 4.12).
#
# Vive sobre el mismo Contenedor binario de adapters/guardadoBinario.py: tres secciones con nombre
# (cripta, esqueleto, estado) y un bloque por sala con su contenido, indexado por id. Cargar una
# sala que ya está en el archivo es buscar en la tabla ordenada y leer solo ese bloque, sin tocar
# el resto del archivo ni volver a pasar por JSON.
#
# El archivo guarda la identidad de la cripta (id, versión de cripta, versión de catálogo y
# semilla) igual que la bitácora de reproducción: cargar contra datos de otra versión produciría
# una partida falsa, así que se rechaza y se informa en lugar de intentarlo.

from adapters.guardadoBinario import Contenedor

MAGIC = b"CRPS"
VERSION_FORMATO = 2
SECCIONES = ("cripta", "esqueleto", "estado")


class FuenteEmbebida:
    """Sirve desde el archivo el esqueleto y el contenido ya cargado, sala a sala.

    Las fichas siguen viniendo del proveedor real: el catálogo ya se persiste por version en
    .cache_cripta/cat_<versionCatalogo>/, y la validación de la cabecera garantiza que es el mismo.
    """

    def __init__(self, real, contenedor, ruta, esqueleto):
        self._real = real
        self._contenedor = contenedor
        self._ruta = ruta
        self._esqueleto = esqueleto

    def datosGenerales(self):
        return self._real.datosGenerales()

    def esqueleto(self):
        return self._esqueleto

    def contenidoSala(self, salaId):
        bloque = self._contenedor.cargarSala(self._ruta, salaId)
        if bloque is None:
            return self._real.contenidoSala(salaId)
        return bloque

    def ficha(self, tipoId):
        return self._real.ficha(tipoId)

    def anticipar(self, salaId):
        pass

    def asegurarFichas(self, tipoIds):
        self._real.asegurarFichas(tipoIds)

    def fijarFichasEnUso(self, productor):
        self._real.fijarFichasEnUso(productor)


class guardadoPartida:
    def __init__(self, idCripta=None, versionCripta=None, versionCatalogo=None):
        self.idCripta = idCripta
        self.versionCripta = versionCripta
        self.versionCatalogo = versionCatalogo
        self.contenedor = Contenedor(MAGIC, VERSION_FORMATO)

    def identidad(self, modelo):
        return {"idCripta": self.idCripta, "versionCripta": self.versionCripta,
                "versionCatalogo": self.versionCatalogo, "semilla": modelo.semilla}

    # ------------------------------------------------------------------ guardar
    def guardar(self, modelo, ruta):
        salas = []
        for i in range(modelo.salas.cantidad()):
            sala = modelo.salas.enPosicion(i)
            if sala.contenidoIncorporado:
                salas.append((sala.id, modelo.proveedor.contenidoSala(sala.id)))
        secciones = [("cripta", self.identidad(modelo)),
                     ("esqueleto", list(modelo.proveedor.esqueleto())),
                     ("estado", modelo.capturarEstado())]
        self.contenedor.guardar(ruta, secciones, salas)
        return ruta

    # ------------------------------------------------------------------ cargar
    def cargar(self, modelo, ruta):
        cripta = self.contenedor.leerSeccion(ruta, "cripta")
        self._validarVersion(cripta)
        secciones = self.contenedor.secciones(ruta)
        esqueleto = estado = None
        for nombre, datos in secciones:
            if nombre == "esqueleto":
                esqueleto = datos
            elif nombre == "estado":
                estado = datos
        if esqueleto is None or estado is None:
            raise ValueError("El archivo de guardado le falta la sección esqueleto o estado.")

        real = modelo.proveedor
        modelo.reiniciar()
        modelo.proveedor = FuenteEmbebida(real, self.contenedor, ruta, esqueleto)
        try:
            modelo.iniciarPartida()
        finally:
            modelo.proveedor = real
        modelo.restaurarEstado(estado)
        return ruta

    def cargarSala(self, ruta, salaId):
        """Acceso aleatorio: solo se leen el encabezado, la tabla de salas y ese bloque."""
        return self.contenedor.cargarSala(ruta, salaId)

    def _validarVersion(self, cripta):
        esperado = (("idCripta", self.idCripta), ("versionCripta", self.versionCripta),
                    ("versionCatalogo", self.versionCatalogo))
        if self.idCripta is None:
            return                      # sin identidad conocida: se confia en el proveedor activo
        for clave, valor in esperado:
            if valor is None:
                continue
            if cripta.get(clave) != valor:
                raise ValueError(
                    "La partida guardada es de otra cripta (%s: %s, ahora: %s)."
                    % (clave, cripta.get(clave), valor))
