"""Contratos con los módulos de los demás (acordados el 19-21 sep).

El modelo solo depende de estas interfaces: nunca de HTTP, disco ni vista.
"""


class Resultado:
    def __init__(self, ok, mensaje="", registrable=False):
        self.ok = ok
        self.mensaje = mensaje
        self.registrable = registrable   # True si debe anotarse en la bitácora de partida


class SinDatos(Exception):
    """El proveedor no pudo conseguir los datos que la acción necesitaba (sección 2.3)."""


class PresupuestoAgotado(SinDatos):
    """Ya se usaron las solicitudes HTTP que la cripta permite para esta partida (sección 3.3)."""


class ProveedorDatos:
    """Lo implementan Diego (red / --offline). El modelo no sabe de dónde vienen los datos."""

    def datosGenerales(self):
        raise NotImplementedError

    def esqueleto(self):
        """Lista completa de salas (todas las páginas), tal como las entrega el JSON."""
        raise NotImplementedError

    def contenidoSala(self, salaId):
        """Contenido de la sala. BLOQUEA hasta tenerlo; esperar nunca mueve el reloj virtual."""
        raise NotImplementedError

    def ficha(self, tipoId):
        """Ficha de catálogo (pasa por la caché de Keilor)."""
        raise NotImplementedError

    def anticipar(self, salaId):
        """Aviso de que el jugador está en salaId: Diego decide qué precargar. No bloquea."""

    def asegurarFichas(self, tipoIds):
        """Pide de una vez, en lotes, las fichas que la sala va a necesitar. No mueve el reloj."""

    def fijarFichasEnUso(self, productor):
        """productor() -> lista de tipoId en uso: la caché no puede desalojarlos (4.4)."""


class InventarioBase:
    """Lo implementa Jorge. Toda mutación debe pasar por modelo.asignar o registrar en
    modelo.diario su inversa, para que el retroceso pueda deshacerla sin copias."""

    def configurar(self, capacidad):
        raise NotImplementedError

    def validar(self, modelo, accion):
        """Para RECOGER, USAR, EQUIPAR, SOLTAR. NO debe mutar nada. Devuelve Resultado."""
        raise NotImplementedError

    def aplicar(self, modelo, accion):
        """Ejecuta la acción ya validada. El modelo ya programó la siguiente acción del jugador."""
        raise NotImplementedError

    def tieneLlave(self, llave_id):
        raise NotImplementedError

    def objetos(self):
        """Lista de ObjetoInstancia (para saber qué fichas están en uso)."""
        raise NotImplementedError

    def avanzar(self):
        raise NotImplementedError

    def retroceder(self):
        raise NotImplementedError

    def actual(self):
        raise NotImplementedError


class DiarioBase:
    """Lo implementa Jorge (historial de retroceso, máximo 5 acciones)."""

    activo = True

    def abrirIntervalo(self):
        """Se llama justo antes de ejecutar una acción del jugador que consume tiempo."""

    def registrar(self, deshacer):
        """deshacer es un callable sin argumentos que invierte un cambio."""

    def cerrarIntervalo(self):
        """Se llama cuando el jugador vuelve a tener la decisión."""

    def retroceder(self, modelo):
        """Revierte el último intervalo y consume el pergamino. Devuelve Resultado."""
        return Resultado(False, "El retroceso no está disponible.")


class DiarioNulo(DiarioBase):
    activo = False


class EfectosBase:
    """Lo implementa Jurnier (veneno, antorcha, regeneración, velocidad)."""

    def alActivarEnemigo(self, modelo, enemigo):
        """Aquí se programa la regeneración si la ficha la declara."""

    def alMorir(self, modelo, actor):
        """Aquí se cancelan los efectos del actor muerto."""

    def alActivarTrampa(self, modelo, trampa, ficha):
        """Efectos extra de una trampa (más allá del daño directo)."""

    def descripcionjugador(self, modelo):
        """Lista de textos con los efectos activos, para la vista."""
        return []
