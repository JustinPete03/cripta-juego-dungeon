# Vista grafica (pygame) con presentacion estilo Pokemon: escenario, cajas de texto y menus.
#
# La clase solo lee el estado del modelo y envia intenciones al controlador. No cambia reglas:
# toda mutacion pasa por Controlador.ejecutarAccion -> Modelo.ejecutar.

import math

import pygame

from model.Constantes import (ACC_ABRIR, ACC_ANTERIOR, ACC_ATACAR, ACC_EQUIPAR, ACC_ESPERAR,
                              ACC_MOVER, ACC_RECOGER, ACC_RETROCESO, ACC_SIGUIENTE, ACC_SOLTAR,
                              ACC_USAR, EN_CURSO)
from model.Acciones import Accion
from view import presentacion, sprites

ANCHO, ALTO = 980, 660

TINTA = (10, 10, 20)
BLANCO = (248, 248, 248)
PERLA = (222, 226, 240)
ACERO = (150, 158, 178)
APAGADO = (104, 112, 134)
AGUA = (18, 24, 48)
AGUA_CLARA = (44, 60, 104)
CREMA = (246, 242, 214)
PIEDRA = (76, 72, 100)
PIEDRA_OSCURA = (28, 26, 42)
LOSETA = (64, 60, 86)
LOSETA_CLARA = (86, 82, 112)
VERDE = (72, 190, 92)
AMARILLO = (238, 196, 56)
ROJO = (222, 72, 72)
SOMBRA_CAJA = (6, 6, 12)
DORADO = (244, 202, 88)
DORADO_OSCURO = (122, 88, 24)
CIAN = (92, 224, 244)
MORADO = (158, 106, 226)
PANEL = (16, 22, 44)
PANEL_CLARO = (26, 34, 62)
BORDE_ACERO = (104, 134, 194)
SELECCION = (62, 92, 156)

CAJA_JUGADOR = pygame.Rect(16, 16, 620, 72)
CAJA_MINI = pygame.Rect(652, 16, 312, 188)
CAJA_ESTADO = pygame.Rect(652, 216, 312, 212)
ESCENARIO = pygame.Rect(16, 100, 620, 328)
CAJA_TEXTO = pygame.Rect(16, 440, 620, 204)
CAJA_MENU = pygame.Rect(652, 440, 312, 204)

MURO = 40
LOSETA_LADO = 48
MARGEN = 5
ANCHO_TEXTO = 56

UI_SUBMENU = "submenu"
UI_IR = "ir"
UI_SERVICIO = "servicio"

# Criterios de la vista ordenada del inventario; None conserva el orden real de la lista.
VOCALIAS_INVENTARIO = (None, "peso", "valor", "nombre")

# Cada acción del menú arcade se pinta con su propio color para reconocerla sin leer.
TONO_ACCION = {ACC_ATACAR: ROJO, ACC_ESPERAR: AMARILLO, ACC_RETROCESO: MORADO,
               ACC_RECOGER: VERDE, ACC_MOVER: CIAN, ACC_ABRIR: DORADO,
               ACC_USAR: VERDE, ACC_EQUIPAR: CIAN, ACC_SOLTAR: ROJO,
               UI_SUBMENU: BORDE_ACERO, UI_IR: BORDE_ACERO, UI_SERVICIO: BORDE_ACERO}


def _tonoAccion(accion):
    return TONO_ACCION.get(accion, BORDE_ACERO)


# Dentro de una misma acción el destino del clic también tiene su propio color.
TONO_DESTINO = {UI_SERVICIO: {"guardar": VERDE, "cargar": VERDE, "bitacora": CIAN,
                              "ayuda": ACERO, "empezar": VERDE},
                UI_IR: {"bolsa": AMARILLO, "sistema": MORADO, "volver": ACERO, "titulo": ROJO}}


def _tonoEntrada(entrada):
    destinos = TONO_DESTINO.get(entrada.accion)
    if destinos is not None and entrada.dato in destinos:
        return destinos[entrada.dato]
    return _tonoAccion(entrada.accion)


def _ratio(valor, maximo):
    if maximo <= 0:
        return 0.0
    return max(0.0, min(1.0, float(valor) / float(maximo)))


def _mezclar(tono, otro, factor):
    return tuple(int(tono[i] + (otro[i] - tono[i]) * factor) for i in range(3))


def _aclara(tono, factor):
    return _mezclar(tono, BLANCO, factor)


def _oscurece(tono, factor):
    return _mezclar(tono, (0, 0, 0), factor)


def _atributo(etiqueta, valor, bono):
    """Un bono de 0 no aporta información y le resta espacio a la fila de atributos."""
    return "%s %d" % (etiqueta, valor) if bono == 0 else "%s %d(%+d)" % (etiqueta, valor, bono)


def _tonoVida(valor, maximo):
    if valor <= 0:
        return APAGADO
    ratio = _ratio(valor, maximo)
    if ratio > 0.5:
        return VERDE
    if ratio > 0.2:
        return AMARILLO
    return ROJO


def _envolver(cadena, ancho=ANCHO_TEXTO):
    lineas = []
    for parrafo in str(cadena).split("\n"):
        restante = parrafo.strip()
        if len(restante) == 0:
            lineas.append("")
            continue
        while len(restante) > ancho:
            corte = restante.rfind(" ", 0, ancho)
            if corte <= 0:
                corte = ancho
            lineas.append(restante[:corte])
            restante = restante[corte:].lstrip()
        lineas.append(restante)
    return lineas


def _envolverPartes(cadena, ancho=ANCHO_TEXTO):
    """Agrupa los segmentos unidos por ' · ' sin partir ninguno por la mitad."""
    lineas = []
    actual = ""
    for parte in str(cadena).split(" · "):
        unido = parte if len(actual) == 0 else actual + " · " + parte
        if len(unido) > ancho and len(actual) > 0:
            lineas.append(actual)
            actual = parte
        else:
            actual = unido
    if len(actual) > 0:
        lineas.append(actual)
    return lineas


def _recortar(fuente, cadena, ancho):
    """Etiqueta recortada con puntos suspensivos: dos lecturas de una misma fila nunca se solapan."""
    if fuente.size(cadena)[0] <= ancho:
        return cadena
    while cadena and fuente.size(cadena + "...")[0] > ancho:
        cadena = cadena[:-1]
    return cadena + "..."


def _desplazar(cursor, delta, cantidad):
    if cantidad <= 0:
        return 0
    return (cursor + delta) % cantidad


class Entrada:
    def __init__(self, texto, accion, dato=None, habilitada=True, detalle="", marca=""):
        self.texto = texto
        self.accion = accion
        self.dato = dato
        self.habilitada = habilitada
        self.detalle = detalle
        self.marca = marca


class VistaGrafica:
    def __init__(self, fabrica, criptas, rutaGuardado="partida.sav"):
        self.fabrica = fabrica
        self.criptas = criptas
        self.rutaGuardado = rutaGuardado
        self.pantalla = None
        self.terminar = False
        self.escena = "titulo"
        self.indiceCripta = 0
        self.semilla = 1
        self.controlador = None
        self.modelo = None
        self.captura = None
        self.criterio = None
        self.cola = []
        self.linea = None
        self.esperando = False
        self.historial = []
        self.totalMensajes = None
        self.celdas = []
        self.celdasSala = None
        self.cursorMenu = 0
        self.cursorSub = 0
        self.submenu = None
        self.cursorBolsa = 0
        self.cursorSistema = 0
        self.cursorTitulo = 0
        self.posicionesBolsa = []
        self.zonas = []
        self.fuentes = []
        self.hojas = []
        self.barras = []
        self.parpadeos = []
        self.flotantes = []
        self.posiciones = []
        self.sacudida = 0.0
        self.salto = None
        self.transicion = 0.0
        self.combate = False
        # Superficies recicladas: las cajas, el escenario y las luces se dibujan una sola vez.
        self.cajas = {}
        self.escenarios = {}
        self.fondos = {}
        self.luces = {}
        self.sombras = {}

    # ------------------------------------------------------------------ arranque
    def iniciar(self):
        pygame.init()
        pygame.display.set_caption("CRIPTA - interfaz grafica")
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        for escala in (1, 2, 3, 4, 5):
            for nombre in sprites.NOMBRES:
                self.hojas.append([nombre, escala, sprites.construir(pygame, nombre, escala)])

    def apagar(self):
        pygame.quit()

    def fuente(self, tam):
        for entrada in self.fuentes:
            if entrada[0] == tam:
                return entrada[1]
        nueva = None
        for nombre in ("couriernew", "consolas", "courier"):
            try:
                nueva = pygame.font.SysFont(nombre, tam, bold=True)
            except Exception:
                nueva = None
            if nueva is not None:
                break
        if nueva is None:
            nueva = pygame.font.Font(None, tam + 4)
        self.fuentes.append([tam, nueva])
        return nueva

    def hoja(self, nombre, escala=3):
        mejor = None
        for entrada in self.hojas:
            if entrada[0] != nombre:
                continue
            if entrada[1] <= escala and (mejor is None or entrada[1] > mejor[1]):
                mejor = entrada
        if mejor is None:
            return self.hojas[0][2]
        return mejor[2]

    def blitear(self, nombre, x, y, escala=3, alpha=255, clave=None):
        superficie = self.hoja(nombre, escala)
        lado = sprites.MEDIDA * escala
        dx = dy = 0
        if clave is not None:
            dx, dy = self.desplazamiento(clave)
        rect = pygame.Rect(int(x + dx), int(y + dy), lado, lado)
        if alpha < 255:
            copia = superficie.copy()
            copia.set_alpha(alpha)
            self.pantalla.blit(copia, rect)
        else:
            self.pantalla.blit(superficie, rect)
        return rect

    # ------------------------------------------------------------------ piezas de dibujado
    def texto(self, x, y, cadena, tam=20, tono=BLANCO, centrado=False, derecha=False,
              sombra=None):
        superficie = self.fuente(tam).render(cadena, True, tono)
        rect = superficie.get_rect()
        if centrado:
            rect.center = (x, y)
        elif derecha:
            rect.topright = (x, y)
        else:
            rect.topleft = (x, y)
        if sombra is not None and len(cadena) > 0:
            borde = self.fuente(tam).render(cadena, True, sombra)
            self.pantalla.blit(borde, rect.move(2, 2))
        self.pantalla.blit(superficie, rect)
        return rect

    def caja(self, rect, relleno=PANEL, borde=BORDE_ACERO, grosor=3, radio=10):
        pygame.draw.rect(self.pantalla, TINTA, rect.move(4, 4), border_radius=radio)
        clave = (rect.width, rect.height, relleno, borde, grosor, radio)
        cara = self.cajas.get(clave)
        if cara is None:
            cara = self._construirCaja(*clave)
            self._guardar(self.cajas, clave, cara)
        self.pantalla.blit(cara, rect.topleft)
        return rect

    def _construirCaja(self, ancho, alto, relleno, borde, grosor, radio):
        """Tres bandas (pie, cuerpo, brillo), doble biselado y esquinas doradas de salón recreativo."""
        radio = max(0, min(radio, ancho // 2, alto // 2))
        cara = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        cuerpo = cara.get_rect()
        pygame.draw.rect(cara, _oscurece(relleno, 0.20), cuerpo, border_radius=radio)
        medio = pygame.Rect(0, 0, ancho, min(alto, max(2 * radio, int(alto * 0.82))))
        pygame.draw.rect(cara, relleno, medio, border_radius=radio)
        brillo = pygame.Rect(grosor + 2, grosor + 1, ancho - 2 * (grosor + 2),
                             max(radio, int(alto * 0.22)))
        if brillo.width > 2 * radio and brillo.height > 2:
            pygame.draw.rect(cara, _aclara(relleno, 0.09), brillo,
                             border_radius=max(2, radio - grosor - 1))
        pygame.draw.rect(cara, borde, cuerpo, grosor, border_radius=radio)
        pygame.draw.rect(cara, _aclara(borde, 0.40), cuerpo.inflate(-grosor, -grosor), 1,
                         border_radius=max(2, radio - 1))
        fino = cuerpo.inflate(-2 * grosor - 5, -2 * grosor - 5)
        if fino.width > 4 and fino.height > 4:
            pygame.draw.rect(cara, _aclara(relleno, 0.22), fino, 1,
                             border_radius=max(2, radio - 3))
        if ancho > 56 and alto > 56:
            self._esquinas(cara, grosor, borde)
        return cara

    def _esquinas(self, cara, grosor, borde):
        """Cuatro escuadras doradas: el marco que separa el panel del fondo."""
        ancho, alto = cara.get_size()
        lado = min(11, ancho // 4, alto // 4)
        brillante = _mezclar(borde, DORADO, 0.75)
        for x, y, dx, dy in ((grosor + 3, grosor + 3, 1, 1),
                             (ancho - grosor - 4, grosor + 3, -1, 1),
                             (grosor + 3, alto - grosor - 4, 1, -1),
                             (ancho - grosor - 4, alto - grosor - 4, -1, -1)):
            pygame.draw.line(cara, brillante, (x, y), (x + lado * dx, y), 2)
            pygame.draw.line(cara, brillante, (x, y), (x, y + lado * dy), 2)

    def _guardar(self, cache, clave, superficie):
        if len(cache) >= 64:
            cache.clear()
        cache[clave] = superficie
        return superficie

    def _sombra(self, ancho):
        clave = (ancho,)
        capa = self.sombras.get(clave)
        if capa is None:
            alto = max(5, int(ancho * 0.28))
            capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            pasos = max(3, alto // 3)
            for i in range(pasos):
                factor = (i + 1) / float(pasos)
                anchoFila = max(1, int(ancho * factor))
                altoFila = max(1, int(alto * factor))
                pygame.draw.ellipse(capa, (0, 0, 0, int(26 + 54 * factor)),
                                    pygame.Rect((ancho - anchoFila) // 2,
                                                (alto - altoFila) // 2, anchoFila, altoFila))
            self._guardar(self.sombras, clave, capa)
        return capa

    def _dibujarSombra(self, x, y, lado):
        capa = self._sombra(int(lado * 1.25))
        self.pantalla.blit(capa, (int(x + lado / 2.0) - capa.get_width() // 2,
                                  int(y + lado - capa.get_height() / 2.0) + 1))

    def _dibujarActor(self, nombre, x, y, escala, alpha=255, clave=None):
        """Sprite con su sombra al pie, siguiendo el mismo desplazamiento de animacion."""
        lado = sprites.MEDIDA * escala
        dx = dy = 0
        if clave is not None:
            dx, dy = self.desplazamiento(clave)
        self._dibujarSombra(x + dx, y + dy, lado)
        return self.blitear(nombre, x, y, escala, alpha, clave)

    def _escenario(self, ancho, alto):
        clave = (ancho, alto)
        cara = self.escenarios.get(clave)
        if cara is not None:
            return cara
        cara = pygame.Surface((ancho + 2 * MARGEN, alto + 2 * MARGEN), pygame.SRCALPHA)
        pygame.draw.rect(cara, PIEDRA_OSCURA, cara.get_rect(), border_radius=12)
        pygame.draw.rect(cara, _aclara(PIEDRA_OSCURA, 0.18), cara.get_rect(), 2,
                         border_radius=12)
        base = pygame.Rect(MARGEN, MARGEN, ancho, alto)
        suelo = base.inflate(-2 * MURO, -2 * MURO)
        self._pintarSuelo(cara, suelo)
        self._pintarMuros(cara, base, suelo)
        cara.blit(self._luz(cara.get_width(), cara.get_height()), (0, 0))
        return self._guardar(self.escenarios, clave, cara)

    def _pintarSuelo(self, cara, suelo):
        """Loseta a Loseta con junta iluminada arriba e izquierda, en sombra abajo y derecha."""
        fila = 0
        y = suelo.y
        while y < suelo.bottom:
            x = suelo.x
            columna = 0
            while x < suelo.right:
                bloque = pygame.Rect(x, y, LOSETA_LADO, LOSETA_LADO).clamp(suelo)
                tono = LOSETA if (fila + columna) % 2 == 0 else LOSETA_CLARA
                pygame.draw.rect(cara, tono, bloque)
                pygame.draw.line(cara, _aclara(tono, 0.22), (bloque.x + 1, bloque.y),
                                 (bloque.right - 2, bloque.y))
                pygame.draw.line(cara, _aclara(tono, 0.11), (bloque.x, bloque.y + 1),
                                 (bloque.x, bloque.bottom - 2))
                pygame.draw.line(cara, _oscurece(tono, 0.36), (bloque.x, bloque.bottom - 1),
                                 (bloque.right - 1, bloque.bottom - 1))
                pygame.draw.line(cara, _oscurece(tono, 0.26), (bloque.right - 1, bloque.y),
                                 (bloque.right - 1, bloque.bottom - 1))
                grano = (fila * 7 + columna * 13) % 11
                if grano < 4:
                    mancha = pygame.Rect(bloque.x + 5 + grano * 10,
                                         bloque.y + 7 + (grano * 9) % 28, 4, 3)
                    pygame.draw.rect(cara, _oscurece(tono, 0.20), mancha.clamp(bloque))
                x += LOSETA_LADO
                columna += 1
            y += LOSETA_LADO
            fila += 1

    def _pintarMuros(self, cara, base, suelo):
        bandas = (pygame.Rect(base.x, base.y, base.width, MURO),
                  pygame.Rect(base.x, suelo.bottom, base.width, base.bottom - suelo.bottom),
                  pygame.Rect(base.x, suelo.y, MURO, suelo.height),
                  pygame.Rect(suelo.right, suelo.y, base.right - suelo.right, suelo.height))
        for banda in bandas:
            pygame.draw.rect(cara, PIEDRA, banda)
            y = banda.y
            fila = 0
            while y < banda.bottom:
                x = banda.x - (24 if fila % 2 else 0)
                while x < banda.right:
                    ladrillo = pygame.Rect(x, y, 48, 24).clamp(banda)
                    if ladrillo.width > 6 and ladrillo.height > 6:
                        pygame.draw.rect(cara, _aclara(PIEDRA, 0.08), ladrillo, border_radius=3)
                        pygame.draw.line(cara, _aclara(PIEDRA, 0.32),
                                         (ladrillo.x + 3, ladrillo.y + 1),
                                         (ladrillo.right - 4, ladrillo.y + 1))
                        pygame.draw.line(cara, _oscurece(PIEDRA, 0.36),
                                         (ladrillo.x + 3, ladrillo.bottom - 2),
                                         (ladrillo.right - 4, ladrillo.bottom - 2))
                        pygame.draw.rect(cara, _oscurece(PIEDRA, 0.58), ladrillo, 1,
                                         border_radius=3)
                    x += 48
                y += 24
                fila += 1
        pygame.draw.rect(cara, _oscurece(PIEDRA, 0.78), suelo.inflate(3, 3), 3, border_radius=6)
        pygame.draw.rect(cara, _aclara(LOSETA, 0.18), suelo, 1, border_radius=4)

    def _luz(self, ancho, alto):
        """Halos concéntricos cálidos: la sala se lee iluminada desde el centro."""
        clave = ("luz", ancho, alto)
        capa = self.luces.get(clave)
        if capa is not None:
            return capa
        capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pasos = 12
        for i in range(pasos):
            factor = (pasos - i) / float(pasos)
            radio = int(ancho * 0.60 * factor)
            altoRadio = int(radio * 0.62)
            pygame.draw.ellipse(capa, (255, 208, 136, int(34 * (1.0 - factor))),
                                pygame.Rect(ancho // 2 - radio, int(alto * 0.46) - altoRadio,
                                            2 * radio, 2 * altoRadio))
        return self._guardar(self.luces, clave, capa)

    def _vineta(self, ancho, alto):
        clave = ("vineta", ancho, alto)
        capa = self.luces.get(clave)
        if capa is not None:
            return capa
        capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        capa.fill((6, 6, 14, 46))
        pasos = 14
        for i in range(pasos):
            factor = i / float(pasos - 1)
            radioX = int(ancho * (0.62 - 0.42 * factor))
            radioY = int(alto * (0.66 - 0.46 * factor))
            pygame.draw.ellipse(capa, (6, 6, 14, int(46 * (1.0 - factor))),
                                pygame.Rect(ancho // 2 - radioX, alto // 2 - radioY,
                                            2 * radioX, 2 * radioY))
        return self._guardar(self.luces, clave, capa)

    def _halo(self, diametro):
        """Círculo aditivo cálido, dibujado de afuera hacia adentro para que el centro queme."""
        clave = ("halo", diametro)
        capa = self.luces.get(clave)
        if capa is not None:
            return capa
        centro = diametro // 2
        capa = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
        pasos = 16
        for i in range(pasos):
            factor = (pasos - i) / float(pasos)
            pygame.draw.circle(capa, (255, 190, 90, int(150 * (1.0 - factor))), (centro, centro),
                               max(1, int(centro * factor)))
        return self._guardar(self.luces, clave, capa)

    def _fondo(self, desde, hasta):
        clave = (desde, hasta)
        cara = self.fondos.get(clave)
        if cara is None:
            cara = pygame.Surface((ANCHO, ALTO))
            for i in range(ALTO):
                pygame.draw.line(cara, _mezclar(desde, hasta, i / float(ALTO - 1)),
                                 (0, i), (ANCHO, i))
            for x in range(0, ANCHO, 56):
                pygame.draw.line(cara, _aclara(hasta, 0.05), (x, 0), (x, ALTO))
            self._guardar(self.fondos, clave, cara)
        return cara

    def _resaltar(self, rect, base):
        """Fila de menú con degradado y filete claro: el cursor se ve aunque no haya flecha."""
        pygame.draw.rect(self.pantalla, _oscurece(base, 0.20), rect, border_radius=7)
        brillo = pygame.Rect(rect.x, rect.y, rect.width, max(3, rect.height // 2))
        pygame.draw.rect(self.pantalla, base, brillo, border_radius=7)
        pygame.draw.rect(self.pantalla, _aclara(base, 0.30),
                         rect.inflate(-2, -2), 1, border_radius=6)

    def _encabezado(self, rect, titulo, derecha=None):
        """Cabecera arcade: mayúsculas doradas sobre un filete a altura fija."""
        self.texto(rect.x + 14, rect.y + 6, titulo.upper(), 16, DORADO, sombra=TINTA)
        if derecha is not None:
            self.texto(rect.right - 14, rect.y + 6, derecha, 16, CIAN, derecha=True, sombra=TINTA)
        y = rect.y + 27
        pygame.draw.line(self.pantalla, DORADO_OSCURO, (rect.x + 10, y), (rect.right - 11, y))
        pygame.draw.line(self.pantalla, _aclara(DORADO_OSCURO, 0.35), (rect.x + 10, y + 1),
                         (rect.right - 11, y + 1))
        return y + 5

    def _chip(self, centro, cadena, tono, limite=None):
        """Pastilla oscura con el borde del color de la acción: se lee sin tocar el sprite."""
        superficie = self.fuente(13).render(cadena, True, tono)
        rect = superficie.get_rect()
        rect.center = centro
        if limite is not None:
            rect.clamp_ip(limite)
        fondo = rect.inflate(12, 5)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.45), fondo, border_radius=5)
        pygame.draw.rect(self.pantalla, _mezclar(tono, PANEL, 0.30), fondo, 1, border_radius=5)
        self.pantalla.blit(superficie, rect)
        return rect

    def _tecla(self, rect, tono):
        """Casillero de tecla al inicio de una fila de menú."""
        cuadro = pygame.Rect(rect.x + 6, rect.centery - 9, 18, 18)
        pygame.draw.rect(self.pantalla, _oscurece(tono, 0.45), cuadro, border_radius=4)
        pygame.draw.rect(self.pantalla, tono, cuadro, 1, border_radius=4)
        return cuadro

    def barraVida(self, rect, valor, maximo, etiqueta="", compacta=False):
        self.caja(rect, relleno=CREMA, borde=TINTA, grosor=3, radio=9)
        hueco = rect.inflate(-16, -16)
        if compacta:
            hueco = rect.inflate(-14, -12)
            hueco.bottom = rect.bottom - 5
        pygame.draw.rect(self.pantalla, _oscurece(CREMA, 0.34), hueco, border_radius=6)
        ratio = _ratio(valor, maximo)
        ancho = int((hueco.width - 4) * ratio)
        if ancho > 0:
            tono = _tonoVida(valor, maximo)
            cuerpo = pygame.Rect(hueco.x + 2, hueco.y + 2, ancho, hueco.height - 4)
            pygame.draw.rect(self.pantalla, _oscurece(tono, 0.26), cuerpo, border_radius=5)
            brillo = pygame.Rect(cuerpo.x, cuerpo.y, cuerpo.width,
                                 max(2, int(cuerpo.height * 0.55)))
            pygame.draw.rect(self.pantalla, tono, brillo, border_radius=4)
            if brillo.height > 3:
                pygame.draw.line(self.pantalla, _aclara(tono, 0.45),
                                 (brillo.x + 2, brillo.y + 1), (brillo.right - 2, brillo.y + 1))
        for parte in (0.25, 0.50, 0.75):
            x = hueco.x + int(hueco.width * parte)
            pygame.draw.line(self.pantalla, _oscurece(CREMA, 0.48), (x, hueco.y + 1),
                             (x, hueco.bottom - 2))
        if len(etiqueta) > 0:
            self.texto(rect.x + 10, rect.y + 7, etiqueta, 19, TINTA)
        self.texto(rect.right - 10, rect.bottom - (20 if compacta else 27),
                   "%d/%d" % (max(0, int(round(valor))), maximo), 18, TINTA, derecha=True)

    def flecha(self, rect):
        centro = rect.centery
        rebote = 3 * math.sin(pygame.time.get_ticks() / 130.0)
        izquierda = rect.x - 16 + rebote
        puntos = ((izquierda, centro - 7), (izquierda, centro + 7), (izquierda + 11, centro))
        pygame.draw.polygon(self.pantalla, TINTA, puntos)
        pygame.draw.polygon(self.pantalla, AMARILLO, puntos)

    def zona(self, rect, accion, dato=None, habilitada=True):
        if rect.width <= 0 or rect.height <= 0:
            return
        self.zonas.append([rect, accion, dato, habilitada])

    # ------------------------------------------------------------------ estado y animacion
    def avisar(self, cadena):
        for linea in _envolver(cadena):
            self.cola.append(linea)
        self._pasarLinea()

    def mostrarTexto(self, texto):
        self.avisar(texto)

    def _pasarLinea(self):
        if self.linea is None and len(self.cola) > 0:
            self.linea = self.cola.pop(0)
            self.esperando = True

    def _avanzarTexto(self):
        if len(self.cola) > 0:
            self.linea = self.cola.pop(0)
        else:
            self.linea = None
            self.esperando = False

    def _bloqueado(self):
        return self.esperando or self.transicion > 0.55

    def _encolar(self, mensajes):
        for mensaje in mensajes:
            self.historial.append(str(mensaje))
            while len(self.historial) > 20:
                self.historial.pop(0)
            for linea in _envolver(mensaje):
                self.cola.append(linea)

    def _capturar(self, fuerzaMapa=False):
        if self.captura is not None and not fuerzaMapa and self.celdasSala == self.captura.sala.id:
            celdas = self.captura.celdas
        else:
            self.celdas = presentacion.celdasDelMapa(self.modelo)
            self.celdasSala = self.modelo.jugador.sala.id
            celdas = self.celdas
        self.captura = presentacion.Instantanea(
            presentacion.instantaneaDelJugador(self.modelo),
            presentacion.instantaneaDeSala(self.modelo),
            presentacion.instantaneaDelInventario(self.modelo, self.criterio),
            [], 0, self.modelo.estado, presentacion.contarPergaminos(self.modelo),
            celdas, presentacion.puedeRetroceder(self.modelo))
        self.combate = self.captura.sala.enCombate

    def _refrescar(self):
        nuevos, self.totalMensajes = presentacion.mensajeNuevo(self.modelo, self.totalMensajes)
        self._encolar(nuevos)
        self._sincronizarVidas()
        self._pasarLinea()

    def _barra(self, clave):
        for entrada in self.barras:
            if entrada[0] == clave:
                return entrada
        return None

    def _sincronizarVidas(self):
        claves = [("jugador", self.captura.jugador.vida)]
        for enemigo in self.captura.sala.enemigos:
            claves.append((enemigo.etiqueta, enemigo.vida))
        for clave, valor in claves:
            entrada = self._barra(clave)
            if entrada is None:
                self.barras.append([clave, valor, valor])
                continue
            if valor < entrada[2]:
                golpe = entrada[2] - valor
                self._golpe(clave, golpe)
            entrada[2] = valor
        vivas = []
        for entrada in self.barras:
            for clave, _ in claves:
                if entrada[0] == clave:
                    vivas.append(entrada)
                    break
        self.barras = vivas

    def _golpe(self, clave, golpe):
        self.parpadeos.append([clave, 0.5])
        for entrada in self.posiciones:
            if entrada[0] == clave:
                self.flotantes.append(["-%d" % golpe, entrada[1].centerx,
                                       max(34, entrada[1].top), 1.2])
                break
        if clave == "jugador":
            self.sacudida = 0.4

    def _vibrar(self, clave, dx, dy):
        self.salto = [clave, 0.26, 0.26, dx, dy]

    def desplazamiento(self, clave):
        if self.salto is not None and self.salto[0] == clave:
            avance = 1.0 - self.salto[1] / self.salto[2]
            return (self.salto[3] * math.sin(avance * math.pi),
                    self.salto[4] * math.sin(avance * math.pi))
        return (0, 0)

    def registrar(self, clave, rect):
        for entrada in self.posiciones:
            if entrada[0] == clave:
                entrada[1] = rect
                return
        self.posiciones.append([clave, rect])

    def _avanzarAnimaciones(self, dt):
        paso = max(1.0, dt * 30.0)
        for entrada in self.barras:
            if entrada[1] > entrada[2]:
                entrada[1] = max(entrada[2], entrada[1] - paso)
            elif entrada[1] < entrada[2]:
                entrada[1] = min(entrada[2], entrada[1] + paso)
        self.sacudida = max(0.0, self.sacudida - dt)
        for i in range(len(self.parpadeos) - 1, -1, -1):
            self.parpadeos[i][1] -= dt
            if self.parpadeos[i][1] <= 0:
                del self.parpadeos[i]
        for i in range(len(self.flotantes) - 1, -1, -1):
            self.flotantes[i][2] -= 26 * dt
            self.flotantes[i][3] -= dt
            if self.flotantes[i][3] <= 0:
                del self.flotantes[i]
        if self.transicion > 0:
            self.transicion = max(0.0, self.transicion - dt * 2.0)
        if self.salto is not None:
            self.salto[1] = max(0.0, self.salto[1] - dt)
            if self.salto[1] <= 0:
                self.salto = None

    def _alpha(self, clave):
        for entrada in self.parpadeos:
            if entrada[0] == clave:
                if int(entrada[1] * 24) % 2 == 0:
                    return 90
        return 255

    def _sacudir(self):
        if self.sacudida <= 0:
            return (0, 0)
        ticks = pygame.time.get_ticks() / 40.0
        return (int(3 * math.sin(ticks)), int(2 * math.cos(ticks * 1.7)))

    # ------------------------------------------------------------------ flujo de partida
    def nuevaPartida(self, indice=None, semilla=None):
        if indice is not None:
            self.indiceCripta = indice
        if semilla is not None:
            self.semilla = semilla
        self.controlador = self.fabrica(self.indiceCripta, self.semilla)
        self.modelo = self.controlador.modelo
        self.barras = []
        self.parpadeos = []
        self.flotantes = []
        self.posiciones = []
        self.cola = []
        self.linea = None
        self.esperando = False
        self.historial = []
        self.totalMensajes = None
        self.celdas = []
        self.celdasSala = None
        self.criterio = None
        self.submenu = None
        self.cursorMenu = 0
        self.cursorBolsa = 0
        self.escena = "escenario"
        self.transicion = 1.0
        self._capturar(True)
        self._refrescar()

    def _enviar(self, tipo, dato=None, investidura=False):
        if self.modelo.estado != EN_CURSO:
            self.escena = "final"
            return
        if investidura:
            self._vibrar("jugador", -30, -22)
        salaAnterior = self.captura.sala.id
        self.controlador.ejecutarAccion(Accion(tipo, dato))
        self._capturar()
        self._refrescar()
        if self.captura.sala.id != salaAnterior:
            self.transicion = 1.0
            self.submenu = None
        if self.modelo.estado != EN_CURSO and not self.esperando:
            self.escena = "final"

    def _navegarBolsa(self, delta):
        self.controlador.ejecutarAccion(Accion(ACC_SIGUIENTE if delta > 0 else ACC_ANTERIOR))
        self._capturar()
        if self.captura.inventario.cursor >= 0:
            self.cursorBolsa = max(0, self.captura.inventario.cursorVista)

    # ------------------------------------------------------------------ menus
    def _entradasMenu(self):
        captura = self.captura
        sala = captura.sala
        if self.submenu is not None:
            return []
        if self.combate:
            return [
                Entrada("Atacar", UI_SUBMENU, "objetivo", len(sala.enemigos) > 0),
                Entrada("Bolsa", UI_IR, "bolsa"),
                Entrada("Retroceso", ACC_RETROCESO, None,
                        captura.pergaminos > 0 and captura.puedeRetroceder,
                        "sin pergamino" if captura.pergaminos == 0 else "nada que deshacer"),
                Entrada("Esperar", ACC_ESPERAR),
            ]
        hayLlavePuerta = False
        for salida in sala.salidas:
            if salida.sePuedeAbrir:
                hayLlavePuerta = True
        return [
            Entrada("Mover", UI_SUBMENU, "mover", len(sala.salidas) > 0, "sin salidas"),
            Entrada("Abrir", UI_SUBMENU, "abrir", hayLlavePuerta, "sin puerta accesible"),
            Entrada("Tomar", UI_SUBMENU, "suelo", len(sala.suelo) > 0, "sala vacia"),
            Entrada("Bolsa", UI_IR, "bolsa"),
            Entrada("Retroceso", ACC_RETROCESO, None,
                    captura.pergaminos > 0 and captura.puedeRetroceder,
                    "sin pergamino" if captura.pergaminos == 0 else "nada que deshacer"),
            Entrada("Esperar", ACC_ESPERAR),
        ]

    def _entradasSubmenu(self):
        if self.submenu is None:
            return []
        clase = self.submenu
        sala = self.captura.sala
        if clase == "objetivo":
            entradas = []
            for i, enemigo in enumerate(sala.enemigos):
                entradas.append(Entrada("%d) %s" % (i + 1, enemigo.nombre), ACC_ATACAR,
                                        enemigo.indice, True, "",
                                        "%d/%d %s" % (enemigo.vida, enemigo.vidaMax,
                                                      enemigo.comportamiento)))
            return entradas
        if clase == "suelo":
            entradas = []
            for objeto in sala.suelo:
                # Al recoger sólo importa el nombre y el dato que decide: sin peso ni valor.
                entradas.append(Entrada(objeto.ficha.nombre, ACC_RECOGER, objeto.indice,
                                        not self.captura.inventario.lleno,
                                        "inventario lleno", objeto.ficha.resumen))
            return entradas
        entradas = []
        for salida in sala.salidas:
            if clase == "mover":
                habilitada = salida.transitable
                detalle = "" if habilitada else ("cierra con llave" if salida.necesitaLlave
                                                 else "cerrada")
            else:
                habilitada = salida.sePuedeAbrir
                detalle = "" if habilitada else "falta la llave"
            entradas.append(Entrada("%s  ->  Sala %s" % (salida.direccion, salida.destinoId),
                                    ACC_MOVER if clase == "mover" else ACC_ABRIR,
                                    salida.direccion, habilitada, detalle,
                                    "cerrada" if salida.cerrada else "abierta"))
        return entradas

    def _activar(self, entrada):
        if not entrada.habilitada:
            self.avisar(entrada.detalle if len(entrada.detalle) > 0 else "Ahora no puedes hacer eso.")
            return
        if entrada.accion == UI_SUBMENU:
            self.submenu = entrada.dato
            self.cursorSub = 0
            return
        if entrada.accion == UI_IR:
            if entrada.dato == "bolsa":
                self.escena = "bolsa"
                self.cursorBolsa = max(0, self.captura.inventario.cursorVista)
            elif entrada.dato == "sistema":
                self.escena = "sistema"
                self.cursorSistema = 0
            elif entrada.dato == "volver":
                self.escena = "escenario"
            elif entrada.dato[:11] == "bolsa-fila-":
                self.cursorBolsa = int(entrada.dato[11:])
                self._alinearCursor()
            elif entrada.dato == "titulo":
                self.escena = "titulo"
            return
        if entrada.accion == UI_SERVICIO:
            if entrada.dato == "empezar":
                self._pulsarA()
            elif entrada.dato[:7] == "cripta:":
                self.indiceCripta = int(entrada.dato[7:])
                self.cursorTitulo = self.indiceCripta
            elif entrada.dato == "guardar":
                self.controlador.procesar("guardar %s" % self.rutaGuardado)
                self._refrescarCaptura()
            elif entrada.dato == "cargar":
                self.controlador.procesar("cargar %s" % self.rutaGuardado)
                self._refrescarCaptura()
                self.escena = "escenario" if self.modelo.estado == EN_CURSO else "final"
            elif entrada.dato == "bitacora":
                self.escena = "bitacora"
            elif entrada.dato == "ayuda":
                self.controlador.procesar("ayuda")
                self._refrescarCaptura()
            return
        self._enviar(entrada.accion, entrada.dato, entrada.accion == ACC_ATACAR)
        self.submenu = None

    def _refrescarCaptura(self):
        self._capturar()
        self._refrescar()

    def _pulsarA(self):
        if self.esperando:
            self._avanzarTexto()
            if self.modelo is not None and self.modelo.estado != EN_CURSO and not self.esperando:
                self.escena = "final"
            return
        if self.escena == "titulo":
            self.indiceCripta = min(self.indiceCripta, len(self.criptas) - 1)
            self.nuevaPartida()
            return
        if self.escena == "final":
            self.escena = "titulo"
            return
        if self.escena == "bitacora":
            self.escena = "escenario"
            return
        if self.escena == "sistema":
            entradas = self._entradasSistema()
            self._activar(entradas[min(self.cursorSistema, len(entradas) - 1)])
            return
        if self.escena == "bolsa":
            entradas = self._entradasBolsa()
            indice = self._accionBolsa(entradas)
            if indice < 0:
                if len(entradas) == 1:
                    self._activar(entradas[0])
                else:
                    self.avisar("Primero mueve el cursor hasta ese objeto.")
                return
            self._activar(entradas[indice])
            return
        if self.submenu is not None:
            entradas = self._entradasSubmenu()
            if len(entradas) > 0:
                self._activar(entradas[min(self.cursorSub, len(entradas) - 1)])
            return
        entradas = self._entradasMenu()
        if len(entradas) > 0:
            self._activar(entradas[min(self.cursorMenu, len(entradas) - 1)])

    def _pulsarB(self):
        if self.esperando:
            self.cola = []
            self.linea = None
            self.esperando = False
            return
        if self.escena in ("bolsa", "sistema", "bitacora"):
            self.escena = "escenario"
            return
        if self.submenu is not None:
            self.submenu = None
            return
        if self.escena == "escenario":
            self.escena = "sistema"
            self.cursorSistema = 0
        elif self.escena == "final":
            self.escena = "titulo"

    def _entradasBolsa(self):
        inventario = self.captura.inventario
        bolsillos = inventario.bolsillos
        if len(bolsillos) == 0:
            return [Entrada("Cerrar", UI_IR, "volver")]
        seleccion = min(self.cursorBolsa, len(bolsillos) - 1)
        clase = bolsillos[seleccion].ficha.clase
        enCursor = bolsillos[seleccion].esCursor
        sinCursor = "primero mueve el cursor del inventario hasta aqui"
        return [
            Entrada("Usar", ACC_USAR, None,
                    clase in ("pocion", "antidoto", "antorcha") and enCursor,
                    "eso no se puede consumir" if clase not in ("pocion", "antidoto", "antorcha")
                    else sinCursor),
            Entrada("Equipar", ACC_EQUIPAR, None, clase in ("arma", "armadura") and enCursor,
                    "eso no se puede equipar" if clase not in ("arma", "armadura") else sinCursor),
            Entrada("Soltar", ACC_SOLTAR, None, enCursor, sinCursor),
            Entrada("Cerrar", UI_IR, "volver"),
        ]

    def _accionBolsa(self, entradas):
        """Fila de accion que dispara Z: usar o equipar, nunca soltar."""
        for i in range(min(2, len(entradas))):
            if entradas[i].habilitada:
                return i
        return -1

    def _entradasSistema(self):
        return [
            Entrada("Guardar partida", UI_SERVICIO, "guardar"),
            Entrada("Cargar partida", UI_SERVICIO, "cargar"),
            Entrada("Bitacora (20 mensajes)", UI_SERVICIO, "bitacora"),
            Entrada("Comandos de consola", UI_SERVICIO, "ayuda"),
            Entrada("Volver al juego", UI_IR, "volver"),
            Entrada("Cerrar sesion", UI_IR, "titulo"),
        ]

    # ------------------------------------------------------------------ entrada
    def _manejarEvento(self, evento):
        if evento.type == pygame.QUIT:
            self.terminar = True
            return
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.esperando:
                self._avanzarTexto()
                if self.modelo is not None and self.modelo.estado != EN_CURSO and not self.esperando:
                    self.escena = "final"
                return
            for zona in self.zonas:
                if zona[0].collidepoint(evento.pos):
                    if not zona[3]:
                        self.avisar("Esa opcion no esta disponible ahora.")
                        return
                    self._activar(Entrada("", zona[1], zona[2]))
                    return
            if self.captura is not None and CAJA_TEXTO.collidepoint(evento.pos) and len(self.historial) > 0:
                self.escena = "bitacora"
            return
        if evento.type != pygame.KEYDOWN:
            return
        tecla = evento.key
        if tecla in (pygame.K_ESCAPE,) and self.escena in ("escenario", "bolsa", "sistema", "bitacora"):
            self._pulsarB()
            return
        if tecla in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE):
            self._pulsarA()
            return
        if tecla == pygame.K_x:
            self._pulsarB()
            return
        if tecla == pygame.K_i and self.escena in ("escenario", "bolsa"):
            self.escena = "escenario" if self.escena == "bolsa" else "bolsa"
            if self.escena == "bolsa":
                self.cursorBolsa = max(0, self.captura.inventario.cursorVista)
            return
        if tecla == pygame.K_TAB:
            self.escena = "bitacora" if self.escena != "bitacora" else "escenario"
            return
        if self.escena == "titulo":
            self._teclaTitulo(tecla)
            return
        if self.escena == "bolsa":
            self._teclaBolsa(tecla)
            return
        if self.escena == "sistema":
            self._teclaLista(tecla, self._entradasSistema(), "cursorSistema")
            return
        if self.escena == "bitacora":
            return
        if self.escena != "escenario" or self._bloqueado():
            return
        if self.submenu is not None:
            self._teclaLista(tecla, self._entradasSubmenu(), "cursorSub")
            return
        total = len(self._entradasMenu())
        if tecla in (pygame.K_UP, pygame.K_w):
            self.cursorMenu = _desplazar(self.cursorMenu, -1, total)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.cursorMenu = _desplazar(self.cursorMenu, 1, total)
        elif tecla in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4) and self.combate:
            indice = int(pygame.key.name(tecla)) - 1
            if indice < len(self.captura.sala.enemigos):
                self._enviar(ACC_ATACAR, indice, True)

    def _teclaTitulo(self, tecla):
        total = len(self.criptas) + 1
        enSemilla = self.cursorTitulo >= len(self.criptas)
        if tecla in (pygame.K_UP, pygame.K_w):
            self.cursorTitulo = _desplazar(self.cursorTitulo, -1, total)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.cursorTitulo = _desplazar(self.cursorTitulo, 1, total)
        elif tecla in (pygame.K_LEFT, pygame.K_a):
            if enSemilla:
                self.semilla = max(1, self.semilla - 1)
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            if enSemilla:
                self.semilla += 1
        if self.cursorTitulo < len(self.criptas):
            self.indiceCripta = self.cursorTitulo

    def _teclaLista(self, tecla, entradas, atributo):
        total = len(entradas)
        if tecla in (pygame.K_UP, pygame.K_w):
            setattr(self, atributo, _desplazar(getattr(self, atributo), -1, total))
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            setattr(self, atributo, _desplazar(getattr(self, atributo), 1, total))
        elif tecla in (pygame.K_LEFT, pygame.K_a):
            setattr(self, atributo, _desplazar(getattr(self, atributo), -1, total))
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            setattr(self, atributo, _desplazar(getattr(self, atributo), 1, total))

    def _teclaBolsa(self, tecla):
        total = len(self.captura.inventario.bolsillos)
        if tecla in (pygame.K_UP, pygame.K_w):
            if total > 0:
                self.cursorBolsa = _desplazar(self.cursorBolsa, -1, total)
                self._alinearCursor()
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            if total > 0:
                self.cursorBolsa = _desplazar(self.cursorBolsa, 1, total)
                self._alinearCursor()
        elif tecla in (pygame.K_e,):
            self._activar(Entrada("", ACC_EQUIPAR))
        elif tecla in (pygame.K_d,):
            self._activar(Entrada("", ACC_SOLTAR))
        elif tecla in (pygame.K_q, pygame.K_RIGHT, pygame.K_LEFT):
            self._cambiarCriterio(1 if tecla != pygame.K_LEFT else -1)

    def _alinearCursor(self):
        """Mueve el cursor real del inventario hasta el bolsillo subrayado en pantalla."""
        bolsillos = self.captura.inventario.bolsillos
        if self.cursorBolsa >= len(bolsillos):
            return
        objetivo = bolsillos[self.cursorBolsa].real
        actual = self.captura.inventario.cursor
        tamano = self.captura.inventario.tamano
        if tamano <= 0 or actual < 0:
            return
        adelante = (objetivo - actual) % tamano
        atras = (actual - objetivo) % tamano
        delta = 1 if adelante <= atras else -1
        for _ in range(min(adelante, atras)):
            self._navegarBolsa(delta)
        self._capturar()
        self.cursorBolsa = max(0, self.captura.inventario.cursorVista)

    def _cambiarCriterio(self, delta):
        posicion = 0
        for i in range(len(VOCALIAS_INVENTARIO)):
            if VOCALIAS_INVENTARIO[i] == self.criterio:
                posicion = i
        self.criterio = VOCALIAS_INVENTARIO[(posicion + delta) % len(VOCALIAS_INVENTARIO)]
        self._capturar()
        self.cursorBolsa = max(0, self.captura.inventario.cursorVista)

    # ------------------------------------------------------------------ dibujado de pantalla
    def _lienzo(self, tono=PIEDRA_OSCURA):
        self.pantalla.blit(self._fondo(_oscurece(tono, 0.45), tono), (0, 0))
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.65), pygame.Rect(0, 0, ANCHO, 12))
        pygame.draw.line(self.pantalla, DORADO_OSCURO, (0, 12), (ANCHO, 12))
        self.zonas = []
        self.posicionesBolsa = []

    def _dibujarTitulo(self):
        self._lienzo((18, 18, 30))
        for escala, x, y in ((4, 60, 120), (4, 820, 140)):
            lado = sprites.MEDIDA * escala
            pulso = 0.6 + 0.4 * math.sin(pygame.time.get_ticks() / 260.0 + x)
            capa = self._halo(300).copy()
            capa.set_alpha(int(255 * pulso))
            self.pantalla.blit(capa, (x + lado // 2 - 150, y + int(lado * 0.28) - 150))
            self.blitear("antorcha", x, y, escala)
        self.texto(ANCHO // 2, 96, "CRIPTA", 74, DORADO, centrado=True, sombra=TINTA)
        self.texto(ANCHO // 2, 158, "JUEGO DE MAZMORRA DIRIGIDO POR EVENTOS", 20, CIAN,
                   centrado=True, sombra=TINTA)
        caja = pygame.Rect(120, 210, 420, 240)
        self.caja(caja)
        self._encabezado(caja, "elige tu cripta")
        for i in range(len(self.criptas)):
            nombre, parametros = self.criptas[i]
            rect = pygame.Rect(caja.x + 18, caja.y + 46 + i * 46, caja.width - 36, 40)
            if i == self.cursorTitulo:
                self._resaltar(rect, SELECCION)
            else:
                pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.40), rect, border_radius=8)
                pygame.draw.rect(self.pantalla, AGUA_CLARA, rect, 1, border_radius=8)
            if i == self.cursorTitulo:
                self.flecha(rect)
            self._tecla(rect, DORADO if i == self.cursorTitulo else BORDE_ACERO)
            self.texto(rect.x + 32, rect.y + 8, nombre.upper(), 20,
                       BLANCO if i == self.cursorTitulo else APAGADO)
            if "ancho" in parametros:
                detalle = "%dx%d salas" % (parametros["ancho"], parametros["alto"])
            else:
                detalle = "%s salas · dif. %s" % (parametros.get("salas", "?"),
                                                  parametros.get("dificultad", "?"))
            self.texto(rect.right - 14, rect.y + 12, detalle, 17, ACERO, derecha=True)
            self.zona(rect, UI_SERVICIO, "cripta:%d" % i)
        cajaSemilla = pygame.Rect(caja.x, caja.bottom + 16, caja.width, 56)
        self.caja(cajaSemilla)
        self.texto(cajaSemilla.x + 20, cajaSemilla.y + 18, "SEMILLA", 18, DORADO, sombra=TINTA)
        self.texto(cajaSemilla.right - 20, cajaSemilla.y + 14, str(self.semilla).zfill(5), 24,
                   CIAN, derecha=True, sombra=TINTA)
        self.texto(cajaSemilla.x + 130, cajaSemilla.y + 18, "<- -> AJUSTA", 16, APAGADO)
        cajaSalir = pygame.Rect(580, 210, 280, 120)
        self.caja(cajaSalir, relleno=_mezclar(PANEL, VERDE, 0.16), borde=VERDE)
        self.texto(cajaSalir.centerx, cajaSalir.y + 24, "EMPEZAR", 30, BLANCO, centrado=True,
                   sombra=TINTA)
        self._chip((cajaSalir.centerx, cajaSalir.y + 82), "Z  /  ENTER", VERDE)
        self.zona(cajaSalir, UI_SERVICIO, "empezar")
        controles = pygame.Rect(580, 350, 280, 100)
        self.caja(controles)
        arriba = self._encabezado(controles, "controles")
        for i, (tecla, accion) in enumerate((("Z", "confirmar"), ("X", "retroceder"),
                                             ("I", "bolsa   ESC   menu"))):
            self._chip((controles.x + 32, arriba + 10 + i * 21), tecla, DORADO)
            self.texto(controles.x + 54, arriba + 1 + i * 21, accion, 16, PERLA)
        local = len(self.criptas) > 0 and "ancho" in self.criptas[0][1]
        self.texto(ANCHO // 2, ALTO - 30,
                   "datos de demostracion local: el motor y las estructuras no cambian" if local
                   else "criptas del paquete --offline: el motor y las estructuras no cambian",
                   16, APAGADO, centrado=True)

    def _dibujarJuego(self):
        self._lienzo()
        if self.escena == "bolsa":
            self._dibujarBolsa()
        else:
            if self.combate:
                self._dibujarCombate()
            else:
                self._dibujarSala()
        self._dibujarHudJugador()
        if self.escena != "bolsa":
            self._dibujarMinimapa()
            self._dibujarEstado()
        self._dibujarTexto()
        if self.escena == "escenario":
            self._dibujarMenu()
        elif self.escena == "bolsa":
            self._dibujarMenuBolsa()
        elif self.escena == "sistema":
            self._dibujarSistema()
        elif self.escena == "bitacora":
            self._dibujarBitacora()
        elif self.escena == "final":
            self._dibujarFinal()
        # La viñeta sólo oscurece el escenario: las cajas de la interfaz mantienen su contraste.
        zona = ESCENARIO.inflate(10, 10)
        self.pantalla.blit(self._vineta(zona.width, zona.height), zona.topleft)
        self._dibujarFlotantes()
        self._dibujarTransicion()

    def _dibujarSala(self):
        sala = self.captura.sala
        temblor = self._sacudir()
        base = ESCENARIO.move(temblor)
        self.pantalla.blit(self._escenario(ESCENARIO.width, ESCENARIO.height),
                           (base.x - MARGEN, base.y - MARGEN))
        suelo = base.inflate(-2 * MURO, -2 * MURO)
        self._dibujarSalidas(base, sala)
        # El héroe va debajo de los objetos: comparten fila y sus etiquetas deben quedar visibles.
        rect = self._dibujarActor("heroe", suelo.centerx - 24, suelo.bottom - 92, 3,
                                  self._alpha("jugador"), "jugador")
        self.registrar("jugador", rect)
        for i in range(len(sala.suelo)):
            objeto = sala.suelo[i]
            x, y = self._posicionSuelo(i, suelo)
            escala = 2
            rect = self._dibujarActor(objeto.ficha.sprite, x, y, escala)
            self.registrar("suelo-%d" % i, rect)
            self.texto(rect.centerx, rect.bottom + 8, str(i + 1), 17, DORADO, centrado=True,
                       sombra=TINTA)
            self.zona(rect.inflate(6, 6), ACC_RECOGER, i, not self.captura.inventario.lleno)
        for i in range(len(sala.trampas)):
            trampa = sala.trampas[i]
            x = suelo.x + 26 + i * 40
            self._dibujarActor("trampa", x, suelo.bottom - 40, 2,
                               255 if trampa.armada else 90)
        salaLlena = len(sala.enemigos) > 4
        for i in range(len(sala.enemigos)):
            enemigo = sala.enemigos[i]
            x, y = self._posicionEnemigo(i, suelo, len(sala.enemigos))
            escala = 3
            rect = self._dibujarActor(enemigo.sprite, x, y, escala,
                                      self._alpha(enemigo.etiqueta), enemigo.etiqueta)
            self.registrar(enemigo.etiqueta, rect)
            etiqueta = pygame.Rect(rect.x - 6, rect.y - 26, 132, 22)
            # Con la sala llena sólo quedan el índice y la fila de enemigos del panel: la barra de
            # vida de cada sprite no cabría entre dos filas de la cuadrícula.
            self.texto(etiqueta.x + 2, etiqueta.y,
                       _recortar(self.fuente(17),
                                 "%d) %s" % (i + 1, "" if salaLlena else enemigo.nombre.upper()),
                                 etiqueta.width - 4), 17,
                       BLANCO if enemigo.activo else APAGADO, sombra=TINTA)
            if salaLlena:
                continue
            self.barraVida(pygame.Rect(rect.x, rect.bottom + 4, rect.width, 20),
                           self._valorMostrado(enemigo.etiqueta, enemigo.vida),
                           enemigo.vidaMax, "", True)

    def _dibujarSalidas(self, base, sala):
        centro = base.center
        for salida in sala.salidas:
            x, y = centro[0] - 24, centro[1] - 24
            if salida.direccion == "N":
                x, y = base.centerx - 24, base.top - 4
            elif salida.direccion == "S":
                x, y = base.centerx - 24, base.bottom - 44
            elif salida.direccion == "E":
                x, y = base.right - 44, base.centery - 24
            elif salida.direccion == "O":
                x, y = base.left - 4, base.centery - 24
            nombre = "puerta_cerrada" if salida.cerrada else "pasaje"
            if salida.esSalida and not salida.cerrada:
                nombre = "salida"
            rect = self.blitear(nombre, x, y, 3)
            # La pastilla dice el estado con una palabra y su color: no hay que adivinar el sprite.
            if salida.esSalida and not salida.cerrada:
                texto, tono = "SALIDA", VERDE
            elif salida.transitable:
                texto, tono = "ABIERTA", CIAN
            elif salida.sePuedeAbrir:
                texto, tono = ("ABRIR LLAVE" if salida.necesitaLlave else "SE ABRE"), DORADO
            else:
                texto, tono = ("CON LLAVE" if salida.necesitaLlave else "CERRADA"), ROJO
            pasado = ((rect.centerx, base.top + 14) if salida.direccion == "N" else
                      (rect.centerx, base.bottom - 14) if salida.direccion == "S" else
                      (base.left + 22, rect.centery) if salida.direccion == "O" else
                      (base.right - 22, rect.centery))
            self._chip(pasado, "%s %s" % (salida.direccion, texto), tono,
                       base.inflate(-4, -4))
            self.zona(rect.inflate(10, 10), UI_SUBMENU,
                      "abrir" if salida.cerrada else "mover")

    def _arena(self, ancho, alto):
        """Fondo de combate: marco biselado, dos plataformas ovaladas y la misma luz cálida."""
        clave = ("arena", ancho, alto)
        cara = self.escenarios.get(clave)
        if cara is not None:
            return cara
        marco = pygame.Rect(4, 4, ancho, alto)
        cara = pygame.Surface((ancho + 8, alto + 8), pygame.SRCALPHA)
        pygame.draw.rect(cara, _oscurece(PANEL, 0.25), cara.get_rect(), border_radius=14)
        pygame.draw.rect(cara, AGUA, marco, border_radius=10)
        plate = pygame.Rect(marco.x + 40, marco.y + 40, ancho - 80, 180)
        pygame.draw.ellipse(cara, _aclara(AGUA, 0.22), plate)
        pygame.draw.ellipse(cara, AGUA_CLARA, plate, 2)
        frente = pygame.Rect(marco.centerx - 180, marco.bottom - 150, 360, 140)
        pygame.draw.ellipse(cara, _aclara(AGUA, 0.30), frente)
        pygame.draw.ellipse(cara, BORDE_ACERO, frente, 2)
        pygame.draw.rect(cara, DORADO_OSCURO, marco, 2, border_radius=10)
        cara.blit(self._luz(ancho + 8, alto + 8), (0, 0))
        return self._guardar(self.escenarios, clave, cara)

    def _dibujarCombate(self):
        sala = self.captura.sala
        temblor = self.sacudida if self.sacudida > 0 else 0
        base = ESCENARIO.move((int(temblor * math.sin(pygame.time.get_ticks() / 38.0)),
                               int(temblor * math.cos(pygame.time.get_ticks() / 27.0))))
        self.pantalla.blit(self._arena(ESCENARIO.width, ESCENARIO.height),
                           (base.x - 4, base.y - 4))
        enemigos = sala.enemigos
        compacto = len(enemigos) > 4
        escala = 3 if compacto else 4
        posiciones = ((base.x + 150, base.y + 58), (base.x + 330, base.y + 26),
                      (base.x + 470, base.y + 66), (base.x + 250, base.y + 128))
        for i in range(len(enemigos)):
            enemigo = enemigos[i]
            if compacto:
                # Más de cuatro actores: cuadrícula de ocho huecos por encima del héroe. Las cuatro
                # posiciones fijas se solapan y el submenudo sigue listando a todos.
                x = base.x + 40 + (i % 4) * 140
                y = base.y + 26 + (i // 4) * 74
            else:
                x, y = posiciones[i % 4]
            rect = self._dibujarActor(enemigo.sprite, x, y, escala, self._alpha(enemigo.etiqueta),
                                      enemigo.etiqueta)
            self.registrar(enemigo.etiqueta, rect)
            etiqueta = pygame.Rect(x - 30, max(base.y + 6, y - 30), 96 if compacto else 150, 26)
            self.texto(etiqueta.x + 6, etiqueta.y + 3,
                       "%d)" % (i + 1) if compacto else "%d) %s" % (i + 1, enemigo.nombre.upper()),
                       18, BLANCO, sombra=TINTA)
            self.barraVida(pygame.Rect(x - 30, y + 42 if compacto else y + 64,
                                       96 if compacto else 150, 20 if compacto else 24),
                           self._valorMostrado(enemigo.etiqueta, enemigo.vida),
                           enemigo.vidaMax, "", True)
            if self.submenu is not None and self.submenu == "objetivo" and \
                    self.cursorSub == i:
                self._dibujarBlanco(rect)
            self.zona(rect.inflate(14, 22), ACC_ATACAR, enemigo.indice)
        jugador = self.captura.jugador
        rect = self._dibujarActor("heroe_espaldas", base.x + 430, base.bottom - 168, 5,
                                  self._alpha("jugador"), "jugador")
        self.registrar("jugador", rect)
        self.texto(rect.x - 12, rect.bottom - 34, jugador.nombre.upper(), 18, PERLA, derecha=True,
                   sombra=TINTA)

    def _dibujarBlanco(self, rect):
        rebote = 4 * math.sin(pygame.time.get_ticks() / 130.0)
        lado = 16
        esquinas = ((rect.x - rebote, rect.y), (rect.right, rect.centery),
                    (rect.right + rebote, rect.bottom), (rect.x, rect.centery))
        for i in range(4):
            x, y = esquinas[i]
            puntos = ((x - lado, y - lado), (x + lado, y - lado), (x, y)) if i in (0, 2) else \
                     ((x - lado, y - lado), (x - lado, y + lado), (x, y))
            pygame.draw.polygon(self.pantalla, TINTA, puntos)
            pygame.draw.polygon(self.pantalla, AMARILLO,
                                ((x - lado + 1, y - lado), (x + lado - 1, y - lado), (x, y))
                                if i in (0, 2) else ((x - lado, y - lado + 1),
                                                     (x - lado, y + lado - 1), (x, y)))

    def _valorMostrado(self, clave, real):
        entrada = self._barra(clave)
        if entrada is None:
            return real
        return entrada[1]

    def _posicionSuelo(self, indice, suelo):
        columnas = 6
        x = suelo.x + 26 + (indice % columnas) * 56
        y = suelo.bottom - 76 - (indice // columnas) * 44
        return x, y

    def _posicionEnemigo(self, indice, suelo, total):
        """Dos columnas con nombre y barra, cuatro cuando sólo se muestra el índice."""
        columnas = 2 if total <= 4 else 4
        paso = (suelo.width - 60) // columnas
        # Con barra de vida el par sprite+barra+etiqueta pide más separación entre filas.
        alto = 104 if total <= 4 else 76
        return int(suelo.x + 30 + (indice % columnas) * paso), \
            int(suelo.y + 12 + (indice // columnas) * alto)

    def _dibujarHudJugador(self):
        jugador = self.captura.jugador
        self.caja(CAJA_JUGADOR)
        self.blitear("heroe", CAJA_JUGADOR.x + 14, CAJA_JUGADOR.y + 12, 3,
                     self._alpha("retrato"), "retrato")
        self.registrar("retrato", pygame.Rect(CAJA_JUGADOR.x + 14, CAJA_JUGADOR.y + 12, 48, 48))
        nombre = self.texto(CAJA_JUGADOR.x + 72, CAJA_JUGADOR.y + 10, jugador.nombre.upper(), 21,
                            DORADO, sombra=TINTA)
        inicio = max(CAJA_JUGADOR.x + 190, nombre.right + 12)
        self.barraVida(pygame.Rect(inicio, CAJA_JUGADOR.y + 10,
                                   min(210, CAJA_JUGADOR.x + 406 - inicio), 34),
                       self._valorMostrado("jugador", jugador.vida), jugador.vidaMax, "VIDA")
        self.texto(CAJA_JUGADOR.right - 16, CAJA_JUGADOR.y + 12,
                   "RELOJ %05d" % self.captura.sala.reloj, 19, CIAN, derecha=True, sombra=TINTA)
        atributos = self.texto(CAJA_JUGADOR.x + 72, CAJA_JUGADOR.y + 44,
                               "   ".join((_atributo("ATR", jugador.ataque, jugador.bonoAtaque),
                                           _atributo("DEF", jugador.defensa, jugador.bonoDefensa),
                                           "VEL %d" % jugador.velocidad)), 17, PERLA)
        if len(jugador.efectos) > 0:
            # Los efectos son la lectura más larga de la barra: si desbordan, se cuenta en lugar
            # de escribir encima del reloj.
            efectos = " / ".join(jugador.efectos).upper()
            leido = self.fuente(14).size(efectos)[0] <= CAJA_JUGADOR.right - 20 - atributos.right
            self.texto(atributos.right + 14, CAJA_JUGADOR.y + 46,
                       efectos if leido else "%d EFECTOS" % len(jugador.efectos), 14, VERDE,
                       sombra=TINTA)

    def _dibujarMinimapa(self):
        self.caja(CAJA_MINI)
        self._encabezado(CAJA_MINI, "MAPA", derecha="SALA %02d" % self.captura.sala.id)
        celdas = self.captura.celdas
        if len(celdas) == 0:
            return
        minX = minY = 10 ** 6
        maxX = maxY = -10 ** 6
        for celda in celdas:
            minX = min(minX, celda.x)
            maxX = max(maxX, celda.x)
            minY = min(minY, celda.y)
            maxY = max(maxY, celda.y)
        area = pygame.Rect(CAJA_MINI.x + 12, CAJA_MINI.y + 38, CAJA_MINI.width - 24,
                           CAJA_MINI.height - 62)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.50), area, border_radius=8)
        pygame.draw.rect(self.pantalla, AGUA_CLARA, area, 1, border_radius=8)
        anchoCelda = max(6, min(22, area.width // max(1, maxX - minX + 1)))
        altoCelda = max(6, min(22, area.height // max(1, maxY - minY + 1)))
        lado = min(anchoCelda, altoCelda)
        offsetX = area.centerx - (maxX - minX + 1) * lado / 2.0
        offsetY = area.centery - (maxY - minY + 1) * lado / 2.0
        for celda in celdas:
            rect = pygame.Rect(offsetX + (celda.x - minX) * lado,
                               offsetY + (celda.y - minY) * lado, lado - 2, lado - 2)
            if not celda.visitada:
                tono = (30, 34, 56)
            elif celda.actual:
                pulso = int(120 + 100 * math.sin(pygame.time.get_ticks() / 220.0))
                tono = (int(pulso * 0.4), pulso, 220)
            elif celda.esSalida:
                tono = (176, 138, 44)
            else:
                tono = (74, 88, 128)
            pygame.draw.rect(self.pantalla, tono, rect, border_radius=3)
            if celda.esSalida:
                self.texto(rect.centerx, rect.centery, "S", 13, DORADO, centrado=True)
            if celda.actual:
                self.texto(rect.centerx, rect.centery, "@", 14, BLANCO, centrado=True)
        jugador = self.captura.jugador
        self.texto(CAJA_MINI.x + 14, CAJA_MINI.bottom - 22,
                   "acciones %d   bajas %d" % (jugador.acciones, jugador.derrotados), 15, ACERO)

    def _dibujarEstado(self):
        self.caja(CAJA_ESTADO, relleno=PANEL_CLARO)
        sala = self.captura.sala
        arriba = self._encabezado(CAJA_ESTADO, sala.nombre) + 2
        secciones = (("ENEMIGOS", sala.enemigos, "enemigo", CIAN),
                     ("EN EL SUELO", sala.suelo, "suelo", VERDE),
                     ("TRAMPAS", sala.trampas, "trampa", ROJO))
        filas = []
        for titulo, elementos, clase, tono in secciones:
            if len(elementos) == 0:
                continue
            filas.append((titulo, None, None, tono, True))
            for elemento in elementos:
                if clase == "enemigo":
                    nombre = elemento.etiqueta
                    dato = "%d/%d" % (elemento.vida, elemento.vidaMax)
                    sprite = elemento.sprite
                    disponible = _ratio(elemento.vida, elemento.vidaMax) > 0
                elif clase == "suelo":
                    nombre = "%d) %s" % (elemento.indice + 1, elemento.ficha.nombre)
                    dato = elemento.ficha.resumen
                    sprite = elemento.ficha.sprite
                    disponible = True
                else:
                    nombre = elemento.ficha.nombre
                    dato = "ARMADA" if elemento.armada else "DESARMADA"
                    sprite = "trampa"
                    disponible = elemento.armada
                filas.append((nombre, sprite, dato, tono, disponible))
        # Una sala con muchos actores no debe escribir encima del pie de la caja.
        limite = CAJA_ESTADO.bottom - 48
        y = arriba
        for i, (nombre, sprite, dato, tono, disponible) in enumerate(filas):
            if y > limite:
                self.texto(CAJA_ESTADO.x + 14, limite, "y %d lineas mas" % (len(filas) - i), 15,
                           ACERO)
                break
            if sprite is None:
                self.texto(CAJA_ESTADO.x + 14, y, nombre, 14, _aclara(tono, 0.15), sombra=TINTA)
                y += 22
            else:
                rect = pygame.Rect(CAJA_ESTADO.x + 16, y - 4, CAJA_ESTADO.width - 32, 20)
                self.blitear(sprite, rect.x, rect.y - 2, 1)
                sobra = rect.width - 24 - self.fuente(13).size(dato)[0] - 12
                self.texto(rect.x + 20, y,
                           _recortar(self.fuente(15), nombre.upper(), sobra), 15,
                           BLANCO if disponible else APAGADO)
                if len(dato) > 0:
                    self.texto(rect.right - 2, y + 1, dato, 13, tono if disponible else APAGADO,
                               derecha=True)
                y += 22
        inventario = self.captura.inventario
        self.texto(CAJA_ESTADO.x + 14, CAJA_ESTADO.bottom - 26,
                   "bolsa %d/%d   pergaminos %d" % (inventario.tamano, inventario.capacidad,
                                                    self.captura.pergaminos), 16,
                   ROJO if inventario.lleno else PERLA)

    def _dibujarTexto(self):
        self.caja(CAJA_TEXTO, relleno=PANEL_CLARO)
        arriba = self._encabezado(CAJA_TEXTO, "BITÁCORA DE EVENTOS",
                                  derecha="%d en total" % (self.totalMensajes or
                                                           len(self.historial)))
        if self.esperando or self.linea is not None:
            for i, linea in enumerate(_envolver(self.linea or "", 48)[:2]):
                self.texto(CAJA_TEXTO.x + 22, arriba + 2 + i * 24, linea, 19, BLANCO, sombra=TINTA)
            si = int(6 + 6 * math.sin(pygame.time.get_ticks() / 160.0))
            pygame.draw.polygon(self.pantalla, DORADO,
                                ((CAJA_TEXTO.right - 34, CAJA_TEXTO.bottom - 26 + si),
                                 (CAJA_TEXTO.right - 20, CAJA_TEXTO.bottom - 26 + si),
                                 (CAJA_TEXTO.right - 27, CAJA_TEXTO.bottom - 16 + si)))
            self.texto(CAJA_TEXTO.x + 22, CAJA_TEXTO.bottom - 30, "Z / ENTER SIGUE", 14, ACERO)
        else:
            visibles = self.historial[-4:]
            y = arriba + 2
            for mensaje in visibles:
                for linea in _envolver(mensaje, 58):
                    self.texto(CAJA_TEXTO.x + 22, y, linea, 17,
                               PERLA if mensaje is visibles[-1] else ACERO)
                    y += 21
            self.texto(CAJA_TEXTO.x + 22, CAJA_TEXTO.bottom - 30,
                       "FLECHAS Y Z: MENU   CLIC: ACCION DIRECTO", 14, ACERO)

    def _dibujarMenu(self):
        self.caja(CAJA_MENU, relleno=PANEL_CLARO)
        entradas = self._entradasMenu()
        if self.submenu is not None:
            entradas = self._entradasSubmenu()
            cursor = min(self.cursorSub, max(0, len(entradas) - 1))
            titulo = {"objetivo": "objetivo", "mover": "direccion",
                      "abrir": "puertas"}.get(self.submenu, "tomar")
        else:
            cursor = min(self.cursorMenu, max(0, len(entradas) - 1))
            titulo = "que haces?"
        arriba = self._encabezado(CAJA_MENU, titulo)
        # 24 px por fila: las seis acciones del menú caben sin que el cursor tenga que desplazarse.
        self._listaEntradas(CAJA_MENU, entradas, cursor, arriba, 24,
                            "x vuelve" if self.submenu is not None else "i bolsa  esc menu")

    def _listaEntradas(self, caja, entradas, cursor, arriba, alto, pie=None):
        """Filas del menú arcade: cada acción lleva su testigo de color y la lista se desplaza
        para que el cursor nunca salga de la caja."""
        huecos = max(1, (caja.bottom - (24 if pie else 8) - arriba) // alto)
        inicio = min(max(0, cursor - huecos + 1), max(0, len(entradas) - huecos))
        fondo = min(len(entradas), inicio + huecos)
        fuente = self.fuente(17)
        for i in range(inicio, fondo):
            entrada = entradas[i]
            rect = pygame.Rect(caja.x + 18, arriba + (i - inicio) * alto, caja.width - 36, alto - 3)
            acento = _tonoEntrada(entrada)
            if i == cursor:
                self._resaltar(rect, SELECCION)
                self.flecha(rect)
            if entrada.habilitada:
                self._tecla(rect, acento)
            centro = rect.y + max(2, (rect.height - fuente.get_linesize()) // 2)
            etiqueta = self.texto(rect.x + 30, centro, entrada.texto.upper(), 17,
                                  BLANCO if i == cursor and entrada.habilitada
                                  else (PERLA if entrada.habilitada else APAGADO))
            if len(entrada.marca) > 0 and rect.right - 8 - etiqueta.right > 12:
                texto = _recortar(self.fuente(13), entrada.marca.upper(),
                                  rect.right - 8 - etiqueta.right - 10)
                self.texto(rect.right - 8, centro + 2, texto, 13,
                           DORADO if entrada.habilitada else APAGADO, derecha=True)
            self.zona(rect, entrada.accion, entrada.dato, entrada.habilitada)
        if len(entradas) == 0:
            self.texto(caja.x + 18, arriba, "nada disponible", 17, APAGADO)
        if pie is not None:
            self.texto(caja.x + 18, caja.bottom - 24, pie, 14, ACERO)
        if len(entradas) > huecos:
            self.texto(caja.right - 14, caja.bottom - 24,
                       "%d/%d" % (min(cursor + 1, len(entradas)), len(entradas)), 14, ACERO,
                       derecha=True)

    def _dibujarBolsa(self):
        panel = pygame.Rect(16, 100, 948, 328)
        self.caja(panel, relleno=PANEL_CLARO)
        inventario = self.captura.inventario
        etiqueta = "real"
        for opcion in VOCALIAS_INVENTARIO:
            if opcion == self.criterio:
                etiqueta = opcion if opcion is not None else "real"
        self._encabezado(panel, "bolsa %d/%d" % (inventario.tamano, inventario.capacidad),
                         derecha="orden: %s  (q/e)" % etiqueta)
        self.posicionesBolsa = []
        lista = pygame.Rect(panel.x + 16, panel.y + 52, 460, panel.height - 68)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.50), lista, border_radius=10)
        pygame.draw.rect(self.pantalla, AGUA_CLARA, lista, 1, border_radius=10)
        if len(inventario.bolsillos) == 0:
            self.texto(lista.centerx, lista.centery, "INVENTARIO VACIO", 20, APAGADO,
                       centrado=True)
        fila = 34
        for i in range(len(inventario.bolsillos)):
            bolsillo = inventario.bolsillos[i]
            y = lista.y + 8 + i * fila
            if y + fila > lista.bottom:
                break
            rect = pygame.Rect(lista.x + 6, y, lista.width - 12, fila - 4)
            self.posicionesBolsa.append(rect)
            seleccionado = i == min(self.cursorBolsa, len(inventario.bolsillos) - 1)
            if seleccionado:
                self._resaltar(rect, SELECCION)
                self.flecha(rect)
            self.blitear(bolsillo.ficha.sprite, rect.x + 12, rect.y + (rect.height - 32) // 2, 2,
                         255 if bolsillo.esCursor else 210)
            estado = ""
            if len(bolsillo.equipado) > 0:
                estado = bolsillo.equipado
            elif bolsillo.esCursor:
                estado = "cursor"
            centro = rect.y + max(2, (rect.height - self.fuente(17).get_linesize()) // 2)
            resumen = bolsillo.ficha.resumen.upper()
            anchoEstado = self.fuente(14).size(estado.upper())[0] if len(estado) > 0 else 0
            anchoResumen = self.fuente(14).size(resumen)[0]
            xResumen = rect.right - 14 - anchoEstado - anchoResumen
            nombre = _recortar(self.fuente(17), bolsillo.ficha.nombre.upper(),
                               xResumen - 12 - (rect.x + 52))
            self.texto(rect.x + 52, centro, nombre, 17,
                       BLANCO if bolsillo.esCursor else PERLA)
            if len(resumen) > 0:
                self.texto(xResumen + anchoResumen, centro, resumen, 14,
                           DORADO if seleccionado else _oscurece(DORADO, 0.18), derecha=True)
            if len(estado) > 0:
                self.texto(rect.right - 10, centro, estado.upper(), 14, CIAN, derecha=True)
            self.zona(rect, UI_IR, "bolsa-fila-%d" % i)
        detalle = pygame.Rect(panel.x + 492, panel.y + 52, panel.width - 508, 150)
        self.caja(detalle, relleno=PANEL)
        if len(inventario.bolsillos) > 0:
            seleccion = inventario.bolsillos[min(self.cursorBolsa, len(inventario.bolsillos) - 1)]
            self.blitear(seleccion.ficha.sprite, detalle.x + 20, detalle.y + 30, 4)
            self.texto(detalle.x + 100, detalle.y + 16, seleccion.ficha.nombre.upper(), 21, DORADO,
                       sombra=TINTA)
            for i, linea in enumerate(_envolverPartes(seleccion.ficha.detalle, 27)):
                self.texto(detalle.x + 100, detalle.y + 44 + i * 20, linea, 16, PERLA)
        y = detalle.bottom + 12
        for texto, valor in (("arma", inventario.arma), ("armadura", inventario.armadura)):
            if valor is None:
                continue
            self.texto(panel.right - 20, y, "%s: %s" % (texto, valor), 16, VERDE, derecha=True)
            y += 24

    def _dibujarMenuBolsa(self):
        self.caja(CAJA_MENU, relleno=PANEL_CLARO)
        entradas = self._entradasBolsa()
        resaltado = self._accionBolsa(entradas)
        if resaltado < 0:
            resaltado = len(entradas) - 1
        arriba = self._encabezado(CAJA_MENU, "con el objeto")
        self._listaEntradas(CAJA_MENU, entradas, resaltado, arriba, 24,
                            "z usar  e equipar  d soltar")

    def _dibujarSistema(self):
        panel = pygame.Rect(280, 150, 420, 340)
        self.caja(panel, relleno=PANEL_CLARO)
        entradas = self._entradasSistema()
        arriba = self._encabezado(panel, "menu del sistema")
        self._listaEntradas(panel, entradas, min(self.cursorSistema, len(entradas) - 1),
                            arriba, 40, "guardado: %s" % self.rutaGuardado)

    def _dibujarBitacora(self):
        panel = pygame.Rect(120, 90, 740, 460)
        self.caja(panel, relleno=PANEL_CLARO)
        arriba = self._encabezado(panel, "bitácora de eventos",
                                  derecha="ultimos %d mensajes" % len(self.historial))
        y = arriba + 4
        for mensaje in self.historial[-17:]:
            self.texto(panel.x + 24, y, mensaje, 17, PERLA)
            y += 24
        self.texto(panel.x + 24, panel.bottom - 26, "X / TAB vuelve", 16, ACERO)

    def _dibujarFinal(self):
        resultado = presentacion.resultadoVisual(self.modelo)
        panel = pygame.Rect(220, 160, 540, 300)
        tono = VERDE if resultado.gano else ROJO
        self.caja(panel, relleno=_mezclar(PANEL, tono, 0.12), borde=tono)
        self.texto(panel.centerx, panel.y + 40, resultado.titulo.upper(), 42, tono, centrado=True,
                   sombra=TINTA)
        pygame.draw.line(self.pantalla, DORADO_OSCURO, (panel.x + 40, panel.y + 78),
                         (panel.right - 40, panel.y + 78))
        textos = (("acciones", resultado.acciones), ("derrotados", resultado.derrotados),
                  ("tiempo final", resultado.tiempoFinal), ("semilla", self.semilla))
        y = panel.y + 100
        for etiqueta, valor in textos:
            self.texto(panel.x + 60, y, etiqueta.upper(), 19, ACERO)
            self.texto(panel.right - 60, y, str(valor), 19, BLANCO, derecha=True)
            pygame.draw.line(self.pantalla, AGUA_CLARA, (panel.x + 60, y + 24),
                             (panel.right - 60, y + 24))
            y += 34
        self.texto(panel.centerx, panel.bottom - 34, "Z VUELVE AL TITULO", 17, ACERO,
                   centrado=True)

    def _dibujarFlotantes(self):
        for entrada in self.flotantes:
            base = ROJO if entrada[0].startswith("-") else VERDE
            factor = min(1.0, entrada[3] / 0.45)
            self.texto(entrada[1] + 2, entrada[2] + 2, entrada[0], 24, TINTA, centrado=True)
            self.texto(entrada[1], entrada[2], entrada[0], 24,
                       (int(base[0] * factor), int(base[1] * factor), int(base[2] * factor)),
                       centrado=True)

    def _dibujarTransicion(self):
        if self.transicion <= 0:
            return
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((8, 8, 16, int(255 * min(1.0, self.transicion))))
        self.pantalla.blit(capa, (0, 0))

    # ------------------------------------------------------------------ bucle
    def paso(self, dt):
        for evento in pygame.event.get():
            self._manejarEvento(evento)
        self._avanzarAnimaciones(dt)
        if self.escena == "titulo":
            self._dibujarTitulo()
        else:
            self._dibujarJuego()
        pygame.display.flip()

    def ejecutar(self):
        self.iniciar()
        reloj = pygame.time.Clock()
        while not self.terminar:
            dt = reloj.tick(60) / 1000.0
            self.paso(min(dt, 0.05))
        self.apagar()
