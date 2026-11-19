# Vista grafica (pygame) con presentacion estilo Pokemon: escenario, cajas de texto y menus.
#
# La clase solo lee el estado del modelo y envia intenciones al controlador. No cambia reglas:
# toda mutacion pasa por Controlador.ejecutarAccion -> Modelo.ejecutar.

import math
import random

import pygame

from model.Constantes import (ACC_ABRIR, ACC_ANTERIOR, ACC_ATACAR, ACC_EQUIPAR, ACC_ESPERAR,
                              ACC_MOVER, ACC_RECOGER, ACC_RETROCESO, ACC_SIGUIENTE, ACC_SOLTAR,
                              ACC_USAR, EN_CURSO, VICTORIA)
from model.Acciones import Accion
from view import presentacion, sprites
from view.sonidos import BancoSonidos

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
        self.escena = "portada"
        self.posRaton = (0, 0)
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
        self._fuentesMap = {}
        self.hojas = []
        self._hojasMap = {}
        self.barras = []
        self.parpadeos = []
        self.flotantes = []
        self.particulas = []
        self.cortes = []
        self.destello = None
        self.sonidoFin = False
        self.mapaSalaSel = None
        self.hx = None
        self.hy = None
        self._salaCaminar = None
        self.moviendo = False
        self.posiciones = []
        self.sacudida = 0.0
        self.salto = None
        self.transicion = 0.0
        self.combate = False
        self.mostrarAyuda = False
        self.errorTitulo = None
        self.historiaModo = "accion"
        self.historiaAccion = 1
        self.historiaTiempo = 0
        self.historiaTexto = ""
        self.resolubilidadTexto = ""
        self.sfx = BancoSonidos()
        self.particulas = []
        self.cortes = []
        self.destello = None
        self.sonidoFin = False
        self.mapaSalaSel = None
        self.modoCaminar = True
        self.hx = None
        self.hy = None
        self.mira = 1
        self.moviendo = False
        self.fasePaso = 0.0
        self._salaCaminar = None
        # Superficies recicladas: las cajas, el escenario y las luces se dibujan una sola vez.
        self.cajas = {}
        self.escenarios = {}
        self.fondos = {}
        self.luces = {}
        self.sombras = {}

    # ------------------------------------------------------------------ arranque
    def iniciar(self):
        pygame.init()
        pygame.display.set_caption("CRIPTA — Mazmorra de Eventos Discretos")
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        try:
            pygame.display.set_icon(sprites.construir(pygame, "llave", 2))
        except Exception:
            pass
        self.sfx.iniciar(pygame)
        for escala in (1, 2, 3, 4, 5):
            for nombre in sprites.NOMBRES:
                superficie = sprites.construir(pygame, nombre, escala)
                self.hojas.append([nombre, escala, superficie])
                self._hojasMap[(nombre, escala)] = superficie

    def apagar(self):
        self.sfx.detenerMusica()
        pygame.quit()

    def fuente(self, tam):
        f = self._fuentesMap.get(tam)
        if f is not None:
            return f
        for entrada in self.fuentes:
            if entrada[0] == tam:
                self._fuentesMap[tam] = entrada[1]
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
        self._fuentesMap[tam] = nueva
        return nueva

    def hoja(self, nombre, escala=3):
        surf = self._hojasMap.get((nombre, escala))
        if surf is not None:
            return surf
        mejor = None
        for entrada in self.hojas:
            if entrada[0] != nombre:
                continue
            if entrada[1] <= escala and (mejor is None or entrada[1] > mejor[1]):
                mejor = entrada
        if mejor is None:
            return self.hojas[0][2] if self.hojas else None
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

    def _escenario(self, ancho, alto, salaId=0):
        clave = ("sala", ancho, alto, int(salaId) % 32)
        cara = self.escenarios.get(clave)
        if cara is not None:
            return cara
        cara = pygame.Surface((ancho + 2 * MARGEN, alto + 2 * MARGEN), pygame.SRCALPHA)
        pygame.draw.rect(cara, PIEDRA_OSCURA, cara.get_rect(), border_radius=12)
        pygame.draw.rect(cara, _aclara(PIEDRA_OSCURA, 0.18), cara.get_rect(), 2,
                         border_radius=12)
        base = pygame.Rect(MARGEN, MARGEN, ancho, alto)
        suelo = base.inflate(-2 * MURO, -2 * MURO)
        self._pintarSuelo(cara, suelo, salaId)
        self._pintarMuros(cara, base, suelo, salaId)
        cara.blit(self._luz(cara.get_width(), cara.get_height()), (0, 0))
        return self._guardar(self.escenarios, clave, cara)

    def _pintarSuelo(self, cara, suelo, salaId=0):
        """Loseta a loseta con textura de fantasía oscura: grietas, piedrecillas, musgo y runas grabadas."""
        sem = int(salaId) * 37 + 11
        tonoMusgo = (36, 86, 54)
        tonoRuna = (72, 134, 168)
        fila = 0
        y = suelo.y
        while y < suelo.bottom:
            x = suelo.x
            columna = 0
            while x < suelo.right:
                bloque = pygame.Rect(x, y, LOSETA_LADO, LOSETA_LADO).clamp(suelo)
                esPar = (fila + columna) % 2 == 0
                tono = LOSETA if esPar else LOSETA_CLARA
                pygame.draw.rect(cara, tono, bloque)
                # Bisel pixel-art de cada losa
                pygame.draw.line(cara, _aclara(tono, 0.22), (bloque.x + 1, bloque.y),
                                 (bloque.right - 2, bloque.y))
                pygame.draw.line(cara, _aclara(tono, 0.12), (bloque.x, bloque.y + 1),
                                 (bloque.x, bloque.bottom - 2))
                pygame.draw.line(cara, _oscurece(tono, 0.38), (bloque.x, bloque.bottom - 1),
                                 (bloque.right - 1, bloque.bottom - 1))
                pygame.draw.line(cara, _oscurece(tono, 0.28), (bloque.right - 1, bloque.y),
                                 (bloque.right - 1, bloque.bottom - 1))
                h = (fila * 19 + columna * 31 + sem) % 29
                # Variación 1: manchas y piedrecillas sueltas con luz y sombra
                if h < 7 and bloque.width >= 32 and bloque.height >= 32:
                    px = bloque.x + 6 + (h * 5) % 26
                    py = bloque.y + 8 + (h * 7) % 24
                    pygame.draw.rect(cara, _oscurece(tono, 0.28), pygame.Rect(px, py, 4, 3))
                    pygame.draw.rect(cara, _aclara(tono, 0.18), pygame.Rect(px, py, 2, 1))
                # Variación 2: grietas ramificadas en pixel-art
                elif 7 <= h <= 10 and bloque.width >= 40 and bloque.height >= 40:
                    gx = bloque.x + 10 + (h * 3) % 14
                    gy = bloque.y + 8 + (h * 5) % 12
                    cGrieta = _oscurece(tono, 0.48)
                    for pasoG in range(6):
                        pygame.draw.rect(cara, cGrieta, pygame.Rect(gx + pasoG * 2, gy + pasoG * 2, 2, 2))
                    pygame.draw.rect(cara, cGrieta, pygame.Rect(gx + 6, gy + 2, 4, 2))
                # Variación 3: runa arcana tenue grabada en la piedra
                elif h in (13, 21) and bloque.width >= 44 and bloque.height >= 44:
                    rx, ry = bloque.centerx - 6, bloque.centery - 6
                    cR = _mezclar(tono, tonoRuna if h == 13 else DORADO_OSCURO, 0.35)
                    pygame.draw.rect(cara, cR, pygame.Rect(rx, ry, 12, 12), 1)
                    pygame.draw.rect(cara, cR, pygame.Rect(rx + 4, ry + 2, 4, 8), 1)
                    pygame.draw.rect(cara, cR, pygame.Rect(rx + 2, ry + 5, 8, 2))
                # Musgo en bordes cercanos a los muros
                if (fila == 0 or columna == 0 or y + LOSETA_LADO >= suelo.bottom) and (h % 3 == 0):
                    mx = bloque.x + 2 + (h * 7) % max(4, bloque.width - 8)
                    my = bloque.y + (2 if fila == 0 else bloque.height - 6)
                    pygame.draw.rect(cara, tonoMusgo, pygame.Rect(mx, my, 5, 3).clamp(bloque))
                x += LOSETA_LADO
                columna += 1
            y += LOSETA_LADO
            fila += 1

    def _pintarMuros(self, cara, base, suelo, salaId=0):
        sem = int(salaId) * 17 + 5
        musgoOsc = (30, 74, 46)
        musgoLuz = (52, 118, 70)
        bandas = (pygame.Rect(base.x, base.y, base.width, MURO),
                  pygame.Rect(base.x, suelo.bottom, base.width, base.bottom - suelo.bottom),
                  pygame.Rect(base.x, suelo.y, MURO, suelo.height),
                  pygame.Rect(suelo.right, suelo.y, base.right - suelo.right, suelo.height))
        for bIdx, banda in enumerate(bandas):
            pygame.draw.rect(cara, _oscurece(PIEDRA, 0.35), banda)
            y = banda.y
            fila = 0
            while y < banda.bottom:
                x = banda.x - (24 if fila % 2 else 0)
                while x < banda.right:
                    ladrillo = pygame.Rect(x, y, 48, 20).clamp(banda)
                    if ladrillo.width > 6 and ladrillo.height > 6:
                        variacion = ((x // 24) * 13 + fila * 7 + sem + bIdx * 5) % 9
                        tonoLad = _aclara(PIEDRA, 0.12) if variacion == 0 else (
                            _oscurece(PIEDRA, 0.10) if variacion in (1, 2) else _aclara(PIEDRA, 0.05)
                        )
                        pygame.draw.rect(cara, tonoLad, ladrillo)
                        pygame.draw.line(cara, _aclara(tonoLad, 0.34),
                                         (ladrillo.x + 2, ladrillo.y + 1),
                                         (ladrillo.right - 3, ladrillo.y + 1))
                        pygame.draw.line(cara, _oscurece(tonoLad, 0.42),
                                         (ladrillo.x + 2, ladrillo.bottom - 2),
                                         (ladrillo.right - 3, ladrillo.bottom - 2))
                        pygame.draw.rect(cara, _oscurece(PIEDRA, 0.62), ladrillo, 1)
                        # Grieta vertical o musgo en ciertos ladrillos
                        if variacion == 3 and ladrillo.width >= 24 and ladrillo.height >= 14:
                            gx = ladrillo.x + ladrillo.width // 2
                            pygame.draw.line(cara, _oscurece(PIEDRA, 0.72),
                                             (gx, ladrillo.y + 2), (gx + 2, ladrillo.bottom - 3))
                        elif variacion == 4 and ladrillo.width >= 20:
                            pygame.draw.rect(cara, musgoOsc,
                                             pygame.Rect(ladrillo.x + 3, ladrillo.bottom - 5, 8, 3).clamp(ladrillo))
                            pygame.draw.rect(cara, musgoLuz,
                                             pygame.Rect(ladrillo.x + 4, ladrillo.bottom - 6, 4, 2).clamp(ladrillo))
                    x += 48
                y += 20
                fila += 1

        # Pilares de esquina tallados con remaches y musgo
        esquinas = (
            pygame.Rect(base.x, base.y, MURO, MURO),
            pygame.Rect(suelo.right, base.y, MURO, MURO),
            pygame.Rect(base.x, suelo.bottom, MURO, MURO),
            pygame.Rect(suelo.right, suelo.bottom, MURO, MURO),
        )
        for pRect in esquinas:
            pygame.draw.rect(cara, _aclara(PIEDRA, 0.14), pRect)
            pygame.draw.rect(cara, _oscurece(PIEDRA, 0.65), pRect, 2)
            capitel = pRect.inflate(-8, -8)
            pygame.draw.rect(cara, _aclara(PIEDRA, 0.26), capitel)
            pygame.draw.rect(cara, _oscurece(PIEDRA, 0.50), capitel, 1)
            for rx, ry in ((capitel.x + 3, capitel.y + 3), (capitel.right - 5, capitel.y + 3),
                           (capitel.x + 3, capitel.bottom - 5), (capitel.right - 5, capitel.bottom - 5)):
                pygame.draw.rect(cara, DORADO_OSCURO, pygame.Rect(rx, ry, 2, 2))

        # Sombra proyectada desde el muro superior y muros laterales sobre el suelo
        for i in range(6):
            alfaSombra = int(115 * (1.0 - i / 6.0))
            franjaN = pygame.Surface((suelo.width, 3), pygame.SRCALPHA)
            franjaN.fill((8, 8, 16, alfaSombra))
            cara.blit(franjaN, (suelo.x, suelo.y + i * 3))
        for i in range(3):
            alfaLat = int(75 * (1.0 - i / 3.0))
            franjaL = pygame.Surface((3, suelo.height), pygame.SRCALPHA)
            franjaL.fill((8, 8, 16, alfaLat))
            cara.blit(franjaL, (suelo.x + i * 3, suelo.y))
            cara.blit(franjaL, (suelo.right - (i + 1) * 3, suelo.y))

        # Telarañas pixel-art en las esquinas superiores del suelo
        colorRed = (160, 168, 192, 95)
        redSup = pygame.Surface((26, 26), pygame.SRCALPHA)
        for pasoR in (6, 12, 18, 24):
            pygame.draw.line(redSup, colorRed, (0, pasoR), (pasoR, 0), 1)
        pygame.draw.line(redSup, colorRed, (0, 0), (22, 22), 1)
        cara.blit(redSup, (suelo.x + 1, suelo.y + 1))
        cara.blit(pygame.transform.flip(redSup, True, False), (suelo.right - 27, suelo.y + 1))

        # Estandartes desgastados en el muro norte (a ambos lados del centro)
        tonoEst = (146, 34, 48) if (salaId % 2 == 0) else (78, 44, 124)
        for ex in (suelo.x + 96, suelo.right - 116):
            est = pygame.Rect(ex, base.y + 6, 20, MURO - 8)
            pygame.draw.line(cara, DORADO_OSCURO, (est.x - 2, est.y), (est.right + 2, est.y), 2)
            pygame.draw.rect(cara, tonoEst, pygame.Rect(est.x, est.y + 2, est.width, est.height - 6))
            pygame.draw.rect(cara, DORADO, pygame.Rect(est.x + 4, est.y + 6, est.width - 8, est.height - 14), 1)
            # Flecos inferiores desgastados en pixel-art
            for fx in range(0, est.width, 4):
                pygame.draw.rect(cara, tonoEst, pygame.Rect(est.x + fx, est.bottom - 4, 2, 4))

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
        self.sfx.reproducir("alerta")
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

    def _emitirParticulas(self, x, y, tono, cantidad=12, haciaArriba=False):
        for _ in range(cantidad):
            ang = random.uniform(-math.pi, 0) if haciaArriba else random.uniform(0, 2.0 * math.pi)
            vel = random.uniform(45, 130)
            vx = math.cos(ang) * vel
            vy = math.sin(ang) * vel - (45 if haciaArriba else 15)
            vida = random.uniform(0.30, 0.65)
            self.particulas.append([float(x), float(y), vx, vy, vida, vida, tono, random.randint(2, 4)])

    def _centroDe(self, clave):
        for entrada in self.posiciones:
            if entrada[0] == clave:
                return entrada[1].center
        return (ESCENARIO.centerx, ESCENARIO.centery)

    def _golpe(self, clave, golpe):
        self.parpadeos.append([clave, 0.5])
        self.sfx.reproducir("golpe")
        for entrada in self.posiciones:
            if entrada[0] == clave:
                self.flotantes.append(["-%d" % golpe, entrada[1].centerx,
                                       max(34, entrada[1].top), 1.2])
                self._emitirParticulas(entrada[1].centerx, entrada[1].centery, ROJO, 10)
                self._emitirParticulas(entrada[1].centerx, entrada[1].centery, AMARILLO, 5)
                tonoCorte = ROJO if clave == "jugador" else DORADO
                self.cortes.append([entrada[1].centerx, entrada[1].centery, 0.22, 0.22, tonoCorte])
                break
        if clave == "jugador":
            self.sacudida = 0.4
            self.destello = [ROJO, 0.22]

    def _vibrar(self, clave, dx, dy):
        self.salto = [clave, 0.26, 0.26, dx, dy]

    def desplazamiento(self, clave):
        if self.salto is not None and self.salto[0] == clave:
            avance = 1.0 - self.salto[1] / self.salto[2]
            return (self.salto[3] * math.sin(avance * math.pi),
                    self.salto[4] * math.sin(avance * math.pi))
        if clave is not None:
            ticks = pygame.time.get_ticks()
            offset = (hash(clave) % 7) * 45
            return (0, int(1.4 * math.sin((ticks + offset) / 320.0)))
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
        for i in range(len(self.particulas) - 1, -1, -1):
            p = self.particulas[i]
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 180 * dt
            p[4] -= dt
            if p[4] <= 0:
                del self.particulas[i]
        for i in range(len(self.cortes) - 1, -1, -1):
            self.cortes[i][2] -= dt
            if self.cortes[i][2] <= 0:
                del self.cortes[i]
        if self.destello is not None:
            self.destello[1] -= dt
            if self.destello[1] <= 0:
                self.destello = None
        if self.transicion > 0:
            self.transicion = max(0.0, self.transicion - dt * 2.0)
        if self.salto is not None:
            self.salto[1] = max(0.0, self.salto[1] - dt)
            if self.salto[1] <= 0:
                self.salto = None
        self._caminar(dt)

    def _activoCaminar(self):
        return self.modoCaminar and self.captura is not None and not self.combate

    def _suelo(self):
        return ESCENARIO.inflate(-2 * MURO, -2 * MURO)

    def _caminar(self, dt):
        self.moviendo = False
        if not self._activoCaminar() or self.escena != "escenario" or self.mostrarAyuda:
            return
        suelo = self._suelo()
        lado = sprites.MEDIDA * 3
        minX = float(suelo.left)
        maxX = float(max(suelo.left, suelo.right - lado))
        minY = float(suelo.top)
        maxY = float(max(suelo.top, suelo.bottom - lado))
        salaId = self.captura.sala.id
        if self.hx is None or salaId != self._salaCaminar:
            self._salaCaminar = salaId
            self.hx = max(minX, min(maxX, float(suelo.centerx - lado // 2)))
            self.hy = max(minY, min(maxY, float(suelo.bottom - 92)))
        if self._bloqueado() or self.submenu is not None:
            return
        teclas = pygame.key.get_pressed()
        dx = (1 if (teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) else 0) - \
             (1 if (teclas[pygame.K_LEFT] or teclas[pygame.K_a]) else 0)
        dy = (1 if (teclas[pygame.K_DOWN] or teclas[pygame.K_s]) else 0) - \
             (1 if (teclas[pygame.K_UP] or teclas[pygame.K_w]) else 0)
        if dx == 0 and dy == 0:
            return
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        vel = 215.0
        self.hx = max(minX, min(maxX, self.hx + dx * vel * dt))
        self.hy = max(minY, min(maxY, self.hy + dy * vel * dt))
        if dx != 0:
            self.mira = 1 if dx > 0 else -1
        self.moviendo = True
        self.fasePaso += dt

        # Cruzar automáticamente al caminar hasta el umbral de una puerta abierta
        objetivo = self._objetivoCercano()
        if objetivo is not None and objetivo[0] == ACC_MOVER:
            dirPuerta = objetivo[1]
            if ((dirPuerta == "N" and dy < 0 and self.hy <= minY + 4) or
                    (dirPuerta == "S" and dy > 0 and self.hy >= maxY - 4) or
                    (dirPuerta == "O" and dx < 0 and self.hx <= minX + 4) or
                    (dirPuerta == "E" and dx > 0 and self.hx >= maxX - 4)):
                self._activar(Entrada("", ACC_MOVER, dirPuerta))

    def _objetivoCercano(self):
        if self.hx is None or self.captura is None:
            return None
        sala = self.captura.sala
        suelo = self._suelo()
        lado = sprites.MEDIDA * 3
        heroe = pygame.Rect(int(self.hx), int(self.hy), lado, lado).inflate(18, 18)
        base = ESCENARIO
        puertas = {"N": (base.centerx - 24, base.top - 4),
                   "S": (base.centerx - 24, base.bottom - 44),
                   "E": (base.right - 44, base.centery - 24),
                   "O": (base.left - 4, base.centery - 24)}
        for salida in sala.salidas:
            if salida.direccion in puertas:
                x, y = puertas[salida.direccion]
                if heroe.colliderect(pygame.Rect(x, y, 48, 48)):
                    return (ACC_ABRIR if salida.cerrada else ACC_MOVER, salida.direccion)
        for i in range(len(sala.suelo)):
            x, y = self._posicionSuelo(i, suelo)
            if heroe.colliderect(pygame.Rect(x, y, 32, 32)):
                return (ACC_RECOGER, i)
        return None

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
        self.errorTitulo = None
        try:
            self.controlador = self.fabrica(self.indiceCripta, self.semilla)
        except RuntimeError as error:
            self.errorTitulo = str(error)
            self.avisar(self.errorTitulo)
            return
        self.modelo = self.controlador.modelo
        self.resolubilidadTexto = getattr(self.modelo, "reporteResolubilidad", "")
        self.barras = []
        self.parpadeos = []
        self.flotantes = []
        self.particulas = []
        self.cortes = []
        self.destello = None
        self.sonidoFin = False
        self.mapaSalaSel = None
        self.hx = None
        self.hy = None
        self._salaCaminar = None
        self.moviendo = False
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
        self.historiaModo = "accion"
        self.historiaAccion = 1
        self.historiaTiempo = 0
        self.historiaTexto = ""
        self.escena = "escenario"
        self.transicion = 1.0
        self._capturar(True)
        self._refrescar()
        if self.resolubilidadTexto:
            primera = self.resolubilidadTexto.splitlines()[0]
            self.historial.append(primera)
            if "NO RESOLUBLE" in primera.upper():
                self.avisar(primera)

    def _enviar(self, tipo, dato=None, investidura=False):
        if self.modelo.estado != EN_CURSO:
            self.escena = "final"
            return
        if investidura:
            self._vibrar("jugador", -30, -22)
        salaAnterior = self.captura.sala.id
        accionesAntes = self.modelo.jugador.acciones
        self.controlador.ejecutarAccion(Accion(tipo, dato))
        self._capturar(tipo in (ACC_ABRIR, ACC_RETROCESO))
        self._refrescar()
        hx, hy = self._centroDe("jugador")
        if self.captura.sala.id != salaAnterior:
            self.transicion = 1.0
            self.submenu = None
            self.sfx.reproducir("paso")
            self._emitirParticulas(hx, hy + 12, ACERO, 8, True)
        elif self.modelo.jugador.acciones != accionesAntes or tipo in (ACC_ABRIR, ACC_RECOGER, ACC_USAR, ACC_EQUIPAR, ACC_RETROCESO):
            if tipo == ACC_ABRIR:
                self.sfx.reproducir("abrir")
                self._emitirParticulas(hx, hy, DORADO, 12)
            elif tipo == ACC_RECOGER:
                self.sfx.reproducir("recoger")
                self._emitirParticulas(hx, hy, VERDE, 10, True)
            elif tipo in (ACC_USAR, ACC_EQUIPAR):
                self.sfx.reproducir("usar")
                self._emitirParticulas(hx, hy, CIAN, 14, True)
            elif tipo == ACC_RETROCESO:
                self.sfx.reproducir("retroceso")
                self._emitirParticulas(hx, hy, MORADO, 18)
                self.destello = [MORADO, 0.28]
        if self.modelo.estado != EN_CURSO:
            if not self.sonidoFin:
                self.sfx.reproducir("victoria" if self.modelo.estado == VICTORIA else "derrota")
                self.sonidoFin = True
            if not self.esperando:
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
            Entrada("Tomar", UI_SUBMENU, "suelo", len(sala.suelo) > 0, "sala vacía"),
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
                estadoColumna = ("costo %d" % salida.costo) if salida.transitable else "cerrada"
            else:
                habilitada = salida.sePuedeAbrir
                detalle = "" if habilitada else "falta la llave"
                estadoColumna = "cerrada" if salida.cerrada else "abierta"
            entradas.append(Entrada("%s  ->  Sala %s" % (salida.direccion, salida.destinoId),
                                    ACC_MOVER if clase == "mover" else ACC_ABRIR,
                                    salida.direccion, habilitada, detalle,
                                    estadoColumna))
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
            elif entrada.dato == "ir_portada":
                self.transicion = 0.35
                self.escena = "portada"
            elif entrada.dato == "ir_titulo":
                self.transicion = 0.35
                self.escena = "titulo"
            elif entrada.dato == "semilla_menos":
                self.semilla = max(1, self.semilla - 1)
            elif entrada.dato == "semilla_mas":
                self.semilla += 1
            elif entrada.dato == "semilla_azar":
                self.semilla = random.randint(1, 99999)
                self.flotantes.append(["¡Semilla al azar!", ANCHO - 200, 140, 0.9])
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
            elif entrada.dato[:5] == "ir_a:":
                destId = int(entrada.dato[5:])
                if self.captura is not None and destId == self.captura.sala.id:
                    self.flotantes.append(["¡Ya estás en la Sala %d!" % destId, ANCHO - 260, 160, 0.9])
                else:
                    self.escena = "escenario"
                    self.sfx.reproducir("paso")
                    self.controlador.procesar("ir a %d" % destId)
                    self._refrescarCaptura()
                    self.flotantes.append(["Viaje a Sala %d" % destId, ANCHO - 260, 160, 1.0])
            elif entrada.dato == "abrir_mapa":
                self.sfx.reproducir("menu")
                self.escena = "mapa"
            elif entrada.dato == "historia":
                self.sfx.reproducir("menu")
                self._cargarHistoria(max(1, self.modelo.jugador.acciones + 1), self.modelo.reloj)
                self.escena = "historia"
            elif entrada.dato == "hist_modo":
                self.sfx.reproducir("menu")
                self.historiaModo = "tiempo" if self.historiaModo == "accion" else "accion"
                self._cargarHistoria(self.historiaAccion, self.historiaTiempo)
            elif entrada.dato[:11] == "hist_delta:":
                self.sfx.reproducir("menu")
                delta = int(entrada.dato[11:])
                if self.historiaModo == "tiempo":
                    self._cargarHistoria(self.historiaAccion, self.historiaTiempo + delta)
                else:
                    self._cargarHistoria(self.historiaAccion + delta, self.historiaTiempo)
            elif entrada.dato == "hist_inicio":
                self.sfx.reproducir("menu")
                if self.historiaModo == "tiempo":
                    self._cargarHistoria(self.historiaAccion, 0)
                else:
                    self._cargarHistoria(1, self.historiaTiempo)
            elif entrada.dato == "hist_actual":
                self.sfx.reproducir("menu")
                if self.historiaModo == "tiempo":
                    self._cargarHistoria(self.historiaAccion, self.modelo.reloj)
                else:
                    self._cargarHistoria(self.modelo.jugador.acciones + 1, self.historiaTiempo)
            elif entrada.dato == "resolubilidad":
                self.sfx.reproducir("menu")
                self.escena = "resolubilidad"
            elif entrada.dato == "toggle_sfx":
                if self.sfx.alternar():
                    self.sfx.reproducir("menu")
            elif entrada.dato == "abrir_ayuda":
                self.sfx.reproducir("menu")
                self.mostrarAyuda = True
            elif entrada.dato == "cerrar_ayuda":
                self.mostrarAyuda = False
            return
        self._enviar(entrada.accion, entrada.dato, entrada.accion == ACC_ATACAR)
        self.submenu = None

    def _refrescarCaptura(self):
        self._capturar(True)
        self._refrescar()

    def _pulsarA(self):
        if self.esperando:
            self._avanzarTexto()
            if self.modelo is not None and self.modelo.estado != EN_CURSO and not self.esperando:
                self.escena = "final"
            return
        if self.escena == "portada":
            self.transicion = 0.4
            self.escena = "titulo"
            return
        if self.escena == "titulo":
            self.indiceCripta = min(self.indiceCripta, len(self.criptas) - 1)
            self.nuevaPartida()
            return
        if self.escena == "final":
            self.transicion = 0.35
            self.escena = "titulo"
            return
        if self.escena in ("bitacora", "mapa", "historia", "resolubilidad"):
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
        if self._activoCaminar() and self.escena == "escenario" and not self.esperando:
            objetivo = self._objetivoCercano()
            if objetivo is not None:
                self._activar(Entrada("", objetivo[0], objetivo[1]))
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
        if self.escena == "titulo":
            self.transicion = 0.4
            self.escena = "portada"
            return
        if self.escena in ("bolsa", "sistema", "bitacora", "mapa", "historia", "resolubilidad"):
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
        sinCursor = "primero mueve el cursor del inventario hasta aquí"
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
            Entrada("Mapa conocido [M]", UI_SERVICIO, "abrir_mapa"),
            Entrada("Línea de tiempo [T]", UI_SERVICIO, "historia"),
            Entrada("Reporte resolubilidad", UI_SERVICIO, "resolubilidad",
                    len(self.resolubilidadTexto) > 0, "sin reporte disponible"),
            Entrada("Guardar partida", UI_SERVICIO, "guardar"),
            Entrada("Cargar partida", UI_SERVICIO, "cargar"),
            Entrada("Bitácora (20 mensajes)", UI_SERVICIO, "bitacora"),
            Entrada("Ayuda y controles [H]", UI_SERVICIO, "abrir_ayuda"),
            Entrada("Volver al juego", UI_IR, "volver"),
            Entrada("Cerrar sesión", UI_IR, "titulo"),
        ]

    # ------------------------------------------------------------------ entrada
    def _manejarEvento(self, evento):
        if evento.type == pygame.QUIT:
            self.terminar = True
            return
        if evento.type == pygame.MOUSEMOTION:
            self.posRaton = evento.pos
            return
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.posRaton = evento.pos
            if self.mostrarAyuda:
                self.mostrarAyuda = False
                return
            if self.escena == "portada":
                self.transicion = 0.35
                self.escena = "titulo"
                return
            if self.esperando:
                self._avanzarTexto()
                if self.modelo is not None and self.modelo.estado != EN_CURSO and not self.esperando:
                    self.escena = "final"
                return
            for zona in self.zonas:
                if zona[0].collidepoint(evento.pos):
                    if not zona[3]:
                        self.avisar("Esa opción no está disponible ahora.")
                        return
                    self._activar(Entrada("", zona[1], zona[2]))
                    return
            if self.captura is not None and CAJA_TEXTO.collidepoint(evento.pos) and len(self.historial) > 0:
                self.escena = "bitacora"
            return
        if evento.type != pygame.KEYDOWN:
            return
        tecla = evento.key
        if tecla in (pygame.K_h, pygame.K_F1):
            self.mostrarAyuda = not self.mostrarAyuda
            self.sfx.reproducir("menu")
            return
        if tecla == pygame.K_F2:
            if self.sfx.alternar():
                self.sfx.reproducir("menu")
            return
        if self.mostrarAyuda:
            if tecla in (pygame.K_ESCAPE, pygame.K_z, pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
                self.mostrarAyuda = False
            return
        if self.escena == "portada":
            if tecla in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE, pygame.K_x, pygame.K_ESCAPE):
                self.transicion = 0.35
                self.escena = "titulo"
            return
        if tecla in (pygame.K_ESCAPE, pygame.K_x) and self.escena == "titulo":
            self.transicion = 0.35
            self.escena = "portada"
            return
        if tecla in (pygame.K_ESCAPE,) and self.escena in ("escenario", "bolsa", "sistema", "bitacora", "mapa", "historia", "resolubilidad"):
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
        if tecla == pygame.K_m and self.escena in ("escenario", "mapa", "bitacora", "historia", "resolubilidad"):
            self.escena = "escenario" if self.escena == "mapa" else "mapa"
            return
        if tecla == pygame.K_t and self.escena in ("escenario", "mapa", "bitacora", "historia", "resolubilidad"):
            if self.escena == "historia":
                self.escena = "escenario"
            else:
                self._cargarHistoria(max(1, self.modelo.jugador.acciones + 1), self.modelo.reloj)
                self.escena = "historia"
            return
        if tecla == pygame.K_r and self.escena in ("escenario", "mapa", "bitacora", "historia", "resolubilidad"):
            if self.escena == "resolubilidad":
                self.escena = "escenario"
            elif len(self.resolubilidadTexto) > 0:
                self.escena = "resolubilidad"
            return
        if tecla == pygame.K_TAB:
            if self.escena == "historia":
                self.historiaModo = "tiempo" if self.historiaModo == "accion" else "accion"
                self._cargarHistoria(self.historiaAccion, self.historiaTiempo)
            else:
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
        if self.escena == "historia":
            pasoChico = 25 if self.historiaModo == "tiempo" else 1
            pasoGrande = 100 if self.historiaModo == "tiempo" else 5
            if tecla in (pygame.K_LEFT, pygame.K_a):
                if self.historiaModo == "tiempo":
                    self._cargarHistoria(self.historiaAccion, self.historiaTiempo - pasoChico)
                else:
                    self._cargarHistoria(self.historiaAccion - pasoChico, self.historiaTiempo)
            elif tecla in (pygame.K_RIGHT, pygame.K_d):
                if self.historiaModo == "tiempo":
                    self._cargarHistoria(self.historiaAccion, self.historiaTiempo + pasoChico)
                else:
                    self._cargarHistoria(self.historiaAccion + pasoChico, self.historiaTiempo)
            elif tecla in (pygame.K_DOWN, pygame.K_s):
                if self.historiaModo == "tiempo":
                    self._cargarHistoria(self.historiaAccion, self.historiaTiempo - pasoGrande)
                else:
                    self._cargarHistoria(self.historiaAccion - pasoGrande, self.historiaTiempo)
            elif tecla in (pygame.K_UP, pygame.K_w):
                if self.historiaModo == "tiempo":
                    self._cargarHistoria(self.historiaAccion, self.historiaTiempo + pasoGrande)
                else:
                    self._cargarHistoria(self.historiaAccion + pasoGrande, self.historiaTiempo)
            return
        if self.escena in ("bitacora", "mapa", "resolubilidad"):
            return
        if self.escena != "escenario" or self._bloqueado():
            return
        if tecla == pygame.K_c and self.captura is not None and not self.combate:
            self.modoCaminar = not self.modoCaminar
            self.sfx.reproducir("menu")
            return
        if self.submenu is not None:
            self._teclaLista(tecla, self._entradasSubmenu(), "cursorSub")
            return
        if self._activoCaminar() and tecla in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                                               pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
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
        total = len(self.criptas)
        if tecla in (pygame.K_UP, pygame.K_w):
            self.cursorTitulo = _desplazar(self.cursorTitulo, -1, total)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.cursorTitulo = _desplazar(self.cursorTitulo, 1, total)
        elif tecla in (pygame.K_LEFT, pygame.K_a):
            self.semilla = max(1, self.semilla - 1)
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            self.semilla += 1
        elif tecla == pygame.K_r:
            self.semilla = random.randint(1, 99999)
            self.flotantes.append(["¡Semilla al azar!", ANCHO - 200, 140, 0.9])
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

    def _dibujarBrasasAmbiente(self, rect, ticks, cantidad=20):
        """Brasas y motas mágicas flotando suavemente hacia arriba dentro de un área."""
        for i in range(cantidad):
            semX = (i * 97 + 31) % max(10, rect.width - 20)
            velY = 14 + (i % 5) * 6
            desplY = int((ticks * velY / 1000.0 + i * 43) % max(10, rect.height - 16))
            vaivenX = int(6.0 * math.sin(ticks / (340.0 + (i % 4) * 60.0) + i))
            bx = rect.x + 10 + (semX + vaivenX) % max(10, rect.width - 20)
            by = rect.bottom - 8 - desplY
            pulsoB = 0.45 + 0.55 * math.sin(ticks / 210.0 + i * 1.9)
            if pulsoB < 0.25:
                continue
            esDorada = (i % 3 != 0)
            baseTono = DORADO if esDorada else (255, 130, 56)
            colorB = (int(baseTono[0] * pulsoB), int(baseTono[1] * pulsoB), int(baseTono[2] * pulsoB))
            tam = 2 if (i % 4 != 0) else 3
            pygame.draw.rect(self.pantalla, colorB, pygame.Rect(bx, by, tam, tam))

    def _dibujarPlataformaPixel(self, superficie, rect, relleno, bordeLuz, bordeOsc):
        """Plataforma escalonada estilo pixel-art (sin antialiasing de elipses modernas)."""
        cx, cy = rect.centerx, rect.centery
        rx, ry = rect.width // 2, rect.height // 2
        pasoY = 3
        for dy in range(-ry, ry + 1, pasoY):
            frac = dy / float(max(1, ry))
            if abs(frac) > 1.0:
                continue
            anchoF = int(rx * math.sqrt(max(0.0, 1.0 - frac * frac)) // 4 * 4)
            if anchoF <= 4:
                continue
            filaRect = pygame.Rect(cx - anchoF, cy + dy, anchoF * 2, pasoY)
            tonoFila = _aclara(relleno, 0.12) if dy < -ry // 3 else (
                _oscurece(relleno, 0.25) if dy > ry // 2 else relleno
            )
            pygame.draw.rect(superficie, tonoFila, filaRect)
            pygame.draw.rect(superficie, bordeLuz if dy <= 0 else bordeOsc,
                             pygame.Rect(filaRect.x, filaRect.y, 4, pasoY))
            pygame.draw.rect(superficie, bordeLuz if dy <= 0 else bordeOsc,
                             pygame.Rect(filaRect.right - 4, filaRect.y, 4, pasoY))
            if abs(dy) >= ry - pasoY:
                pygame.draw.rect(superficie, bordeLuz if dy < 0 else bordeOsc, filaRect)

    def _dibujarPortada(self):
        self._lienzo((14, 14, 24))
        ticks = pygame.time.get_ticks()
        self._dibujarBrasasAmbiente(pygame.Rect(20, 20, ANCHO - 40, ALTO - 40), ticks, 26)

        # Antorchas en columnas laterales con halos de fuego vivo (doble frecuencia)
        for escala, x, y in ((5, 50, 90), (5, 850, 90)):
            lado = sprites.MEDIDA * escala
            pulso = 0.68 + 0.22 * math.sin(ticks / 190.0 + x) + 0.10 * math.cos(ticks / 85.0 + x)
            capa = self._halo(320).copy()
            capa.set_alpha(int(255 * max(0.3, min(1.0, pulso))))
            self.pantalla.blit(capa, (x + lado // 2 - 160, y + int(lado * 0.28) - 160))
            self.blitear("antorcha", x, y, escala)

        # Logotipo monumental CRIPTA con levitación sutil y relieve 8-bits
        levitacion = int(3.0 * math.sin(ticks / 360.0))
        yLogo = 90 + levitacion
        self.texto(ANCHO // 2 + 4, yLogo + 4, "CRIPTA", 86, TINTA, centrado=True)
        self.texto(ANCHO // 2 + 2, yLogo + 2, "CRIPTA", 86, DORADO_OSCURO, centrado=True)
        self.texto(ANCHO // 2, yLogo, "CRIPTA", 86, DORADO, centrado=True)
        self.texto(ANCHO // 2, yLogo - 2, "CRIPTA", 82, CREMA, centrado=True)

        self.texto(ANCHO // 2, 160 + levitacion // 2,
                   "MAZMORRA DE EVENTOS DISCRETOS · 8-BIT RETRO EDITION", 18, CIAN,
                   centrado=True, sombra=TINTA)

        # Marco del diorama central estilo portada retro / Pokémon
        areaDiorama = pygame.Rect(100, 195, 780, 280)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.40), areaDiorama, border_radius=14)
        pygame.draw.rect(self.pantalla, AGUA_CLARA, areaDiorama, 2, border_radius=14)

        # Plataforma 1 (Izquierda): El Explorador / Héroe
        platHeroe = pygame.Rect(140, 395, 190, 50)
        self._dibujarPlataformaPixel(self.pantalla, platHeroe, (24, 30, 52), BORDE_ACERO, AGUA_CLARA)
        idleHeroe = int(2.5 * math.sin(ticks / 280.0))
        self._dibujarSombra(195, 335 + idleHeroe, sprites.MEDIDA * 5)
        self.blitear("heroe", 195, 335 + idleHeroe, 5)
        self.texto(235, 452, "EL EXPLORADOR", 16, PERLA, centrado=True, sombra=TINTA)

        # Plataforma 2 (Centro): Pedestal de la Llave Sagrada
        platLlave = pygame.Rect(ANCHO // 2 - 95, 405, 190, 50)
        self._dibujarPlataformaPixel(self.pantalla, platLlave, (32, 38, 64), DORADO, DORADO_OSCURO)

        haloLlave = self._halo(220).copy()
        pulsoLlave = 140 + int(50 * math.sin(ticks / 210.0) + 20 * math.cos(ticks / 95.0))
        haloLlave.set_alpha(max(60, min(230, pulsoLlave)))
        self.pantalla.blit(haloLlave, (ANCHO // 2 - 110, 280 - 110))

        # Llave flotante con oscilación sinusoidal
        floatLlave = int(8.0 * math.sin(ticks / 250.0))
        yLlave = 280 + floatLlave
        self.blitear("llave", ANCHO // 2 - 40, yLlave, 5)

        # Destellos mágicos retro alrededor de la llave
        for ang, dist in ((0.2, 54), (1.8, 60), (3.4, 48), (4.9, 56)):
            fase = ticks / 300.0 + ang
            brillo = max(0.0, math.sin(fase))
            if brillo > 0.4:
                sx = int(ANCHO // 2 + dist * math.cos(fase * 0.8))
                sy = int(yLlave + 40 + dist * 0.5 * math.sin(fase * 0.8))
                pygame.draw.circle(self.pantalla, CREMA, (sx, sy), 3)
                pygame.draw.circle(self.pantalla, DORADO, (sx, sy), 5, 1)

        self.texto(ANCHO // 2, 456, "LA LLAVE DE SALIDA", 17, DORADO, centrado=True, sombra=TINTA)

        # Plataforma 3 (Derecha): Monstruos de la Mazmorra (Cazador + Murciélago)
        platMonstruos = pygame.Rect(650, 395, 200, 50)
        self._dibujarPlataformaPixel(self.pantalla, platMonstruos, (32, 24, 46), ROJO, (110, 42, 54))
        idleEsqueleto = int(2.5 * math.sin(ticks / 290.0 + 1.2))
        self._dibujarSombra(680, 335 + idleEsqueleto, sprites.MEDIDA * 5)
        self.blitear("cazador", 680, 335 + idleEsqueleto, 5)

        # Murciélago acechando arriba a la derecha con aleteo/flotación
        hoverMurcielago = int(5.0 * math.sin(ticks / 190.0 + 2.0))
        self.blitear("murcielago", 770, 260 + hoverMurcielago, 4)
        self.texto(750, 452, "GUARDIANES Y CAZADORES", 16, ROJO, centrado=True, sombra=TINTA)

        # Banner retro interactivo pulsante estilo arcade "PRESS START"
        pulsoTexto = int(170 + 85 * math.sin(ticks / 180.0))
        cajaStart = pygame.Rect(ANCHO // 2 - 280, 502, 560, 58)
        self.caja(cajaStart, relleno=_mezclar(PANEL, AGUA_CLARA, 0.25), borde=DORADO, radio=12)

        tonoParpadeo = (min(255, pulsoTexto + 40), min(255, pulsoTexto + 20), 120)
        self.texto(cajaStart.centerx, cajaStart.centery - 2,
                   "»  PRESIONA [Z] O [ENTER] PARA COMENZAR  «", 22, tonoParpadeo,
                   centrado=True, sombra=TINTA)

        self.texto(ANCHO // 2, 584,
                   "O HAZ CLIC EN CUALQUIER LUGAR CON EL RATÓN", 15, APAGADO, centrado=True)
        self.texto(ANCHO // 2, 626,
                   "ESTRUCTURAS DE DATOS II · PROYECTO CRIPTA 2026", 14, (70, 80, 110), centrado=True)

        self.zona(pygame.Rect(0, 0, ANCHO, ALTO), UI_SERVICIO, "ir_titulo")

    def _dibujarTitulo(self):
        self._lienzo((16, 16, 28))
        ticks = pygame.time.get_ticks()
        self._dibujarBrasasAmbiente(pygame.Rect(20, 20, ANCHO - 40, ALTO - 40), ticks, 16)

        self.texto(ANCHO // 2, 38, "CRIPTA", 44, DORADO, centrado=True, sombra=TINTA)
        self.texto(ANCHO // 2, 74, "SELECCIÓN DE EXPEDICIÓN", 18, CIAN, centrado=True, sombra=TINTA)

        # Botón volver a portada
        btnVolver = pygame.Rect(28, 28, 192, 36)
        hoverVolver = btnVolver.collidepoint(self.posRaton)
        self.caja(btnVolver, relleno=_aclara(PANEL, 0.2) if hoverVolver else PANEL,
                  borde=BLANCO if hoverVolver else BORDE_ACERO, radio=8)
        self.texto(btnVolver.centerx, btnVolver.centery, "[X / ESC] PORTADA", 15,
                   BLANCO if hoverVolver else PERLA, centrado=True)
        self.zona(btnVolver, UI_SERVICIO, "ir_portada")

        # Columna Izquierda: Criptas (Tarjetas)
        cajaCriptas = pygame.Rect(28, 96, 500, 520)
        self.caja(cajaCriptas)
        self._encabezado(cajaCriptas, "elige tu cripta")

        yCard = cajaCriptas.y + 46
        for i in range(len(self.criptas)):
            nombre, parametros = self.criptas[i]
            rect = pygame.Rect(cajaCriptas.x + 16, yCard, cajaCriptas.width - 32, 72)
            yCard += 80

            esSeleccionada = (i == self.cursorTitulo)
            esHover = rect.collidepoint(self.posRaton)

            if esSeleccionada:
                self._resaltar(rect, SELECCION)
                self.flecha(rect)
            elif esHover:
                pygame.draw.rect(self.pantalla, _aclara(PANEL, 0.35), rect, border_radius=8)
                pygame.draw.rect(self.pantalla, BORDE_ACERO, rect, 2, border_radius=8)
            else:
                pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.30), rect, border_radius=8)
                pygame.draw.rect(self.pantalla, AGUA_CLARA, rect, 1, border_radius=8)

            self._tecla(rect, DORADO if esSeleccionada else (BORDE_ACERO if esHover else AGUA_CLARA))

            self.texto(rect.x + 36, rect.y + 12, nombre.upper(), 22,
                       BLANCO if esSeleccionada else (PERLA if esHover else APAGADO), sombra=TINTA)

            if "ancho" in parametros:
                detalle = "%dx%d salas (%d totales)" % (
                    parametros["ancho"], parametros["alto"], parametros["ancho"] * parametros["alto"]
                )
                if i == 0:
                    difTexto, difTono = "[*] FÁCIL", VERDE
                elif i == 1:
                    difTexto, difTono = "[**] MEDIA", DORADO
                else:
                    difTexto, difTono = "[***] DIFÍCIL", ROJO
            else:
                salasCount = parametros.get("salas", "?")
                difRaw = str(parametros.get("dificultad", "media")).lower()
                detalle = "%s salas" % salasCount
                if "facil" in difRaw or "fácil" in difRaw:
                    difTexto, difTono = "[*] FÁCIL", VERDE
                elif "alta" in difRaw or "dificil" in difRaw or "difícil" in difRaw:
                    difTexto, difTono = "[***] DIFÍCIL", ROJO
                else:
                    difTexto, difTono = "[**] MEDIA", DORADO

            self.texto(rect.x + 36, rect.y + 42, detalle, 16, ACERO)
            self._chip((rect.right - 68, rect.centery), difTexto, difTono)
            self.zona(rect, UI_SERVICIO, "cripta:%d" % i)

        # Columna Derecha: Configuración y Acción
        colDerX = 554
        anchoDer = 398

        # Panel 1: Semilla del Azar
        cajaSemilla = pygame.Rect(colDerX, 96, anchoDer, 116)
        self.caja(cajaSemilla)
        self._encabezado(cajaSemilla, "semilla del azar")

        self.texto(cajaSemilla.x + 24, cajaSemilla.y + 46, str(self.semilla).zfill(5), 32, CIAN,
                   sombra=TINTA)

        btnMenos = pygame.Rect(cajaSemilla.x + 160, cajaSemilla.y + 44, 38, 36)
        btnMas = pygame.Rect(cajaSemilla.x + 204, cajaSemilla.y + 44, 38, 36)
        btnAzar = pygame.Rect(cajaSemilla.x + 252, cajaSemilla.y + 44, 126, 36)

        hoverMenos = btnMenos.collidepoint(self.posRaton)
        hoverMas = btnMas.collidepoint(self.posRaton)
        hoverAzar = btnAzar.collidepoint(self.posRaton)

        self.caja(btnMenos, relleno=_aclara(PANEL, 0.2) if hoverMenos else PANEL,
                  borde=BLANCO if hoverMenos else BORDE_ACERO, radio=6)
        self.texto(btnMenos.centerx, btnMenos.centery, "<", 20, BLANCO, centrado=True)
        self.zona(btnMenos, UI_SERVICIO, "semilla_menos")

        self.caja(btnMas, relleno=_aclara(PANEL, 0.2) if hoverMas else PANEL,
                  borde=BLANCO if hoverMas else BORDE_ACERO, radio=6)
        self.texto(btnMas.centerx, btnMas.centery, ">", 20, BLANCO, centrado=True)
        self.zona(btnMas, UI_SERVICIO, "semilla_mas")

        self.caja(btnAzar, relleno=_aclara(PANEL, 0.25) if hoverAzar else PANEL,
                  borde=DORADO if hoverAzar else DORADO_OSCURO, radio=6)
        self.texto(btnAzar.centerx, btnAzar.centery, "[R] AL AZAR", 16, DORADO if hoverAzar else CREMA, centrado=True)
        self.zona(btnAzar, UI_SERVICIO, "semilla_azar")

        self.texto(cajaSemilla.x + 24, cajaSemilla.y + 88, "Ajusta con < > o pulsa [R] para azar", 14, APAGADO)

        # Panel 2: Misión y Reglas
        cajaMision = pygame.Rect(colDerX, 226, anchoDer, 154)
        self.caja(cajaMision)
        self._encabezado(cajaMision, "reglas de supervivencia")

        pautas = (
            ("*", "Explora la cripta y evita trampas ocultas."),
            ("*", "Cazadores siguen la ruta de menor costo."),
            ("*", "Halla la Llave y llega vivo a la Salida."),
            ("*", "Usa Bolsa [I], Mapa [M] e Historia [T].")
        )
        maxPautaAncho = cajaMision.width - 52
        for idx, (vineta, textoPauta) in enumerate(pautas):
            self.texto(cajaMision.x + 18, cajaMision.y + 39 + idx * 26, vineta, 16, DORADO)
            self.texto(cajaMision.x + 34, cajaMision.y + 39 + idx * 26,
                       _recortar(self.fuente(14), textoPauta, maxPautaAncho), 14, PERLA)

        # Panel 3: Botón Iniciar Aventura
        cajaEmpezar = pygame.Rect(colDerX, 394, anchoDer, 102)
        hoverEmpezar = cajaEmpezar.collidepoint(self.posRaton)
        pulsoVerde = 0.85 + 0.15 * math.sin(ticks / 260.0)
        tonoFondo = _mezclar(PANEL, VERDE, 0.25 if hoverEmpezar else 0.18 * pulsoVerde)
        self.caja(cajaEmpezar, relleno=tonoFondo, borde=VERDE if hoverEmpezar else _mezclar(VERDE, ACERO, 0.4), radio=12)

        self.texto(cajaEmpezar.centerx, cajaEmpezar.y + 26, "¡INICIAR EXPEDICIÓN!", 30, BLANCO,
                   centrado=True, sombra=TINTA)
        self._chip((cajaEmpezar.centerx, cajaEmpezar.y + 70), "PULSA [Z] O [ENTER]", VERDE)
        self.zona(cajaEmpezar, UI_SERVICIO, "empezar")

        # Panel 4: Atajos de teclado
        cajaTeclas = pygame.Rect(colDerX, 510, anchoDer, 106)
        self.caja(cajaTeclas)
        arriba = self._encabezado(cajaTeclas, "atajos y controles")
        controles = (
            ("Z / ENT", "Confirmar"),
            ("X / ESC", "Volver/Menú"),
            ("I / M",   "Bolsa/Mapa"),
            ("T / H",   "Hist./Ayuda"),
        )
        for idx, (tClave, descClave) in enumerate(controles):
            col = idx % 2
            fila = idx // 2
            px = cajaTeclas.x + 14 + col * 190
            py = arriba + 10 + fila * 26
            self._chip((px + 34, py + 8), tClave, DORADO)
            self.texto(px + 72, py + 2, _recortar(self.fuente(12), descClave, 114), 12, ACERO)

        # Pie
        if self.errorTitulo:
            aviso = pygame.Rect(28, 622, ANCHO - 56, 28)
            self.caja(aviso, relleno=_mezclar(PANEL, ROJO, 0.25), borde=ROJO, grosor=2, radio=6)
            self.texto(aviso.centerx, aviso.centery, _recortar(self.fuente(15), self.errorTitulo, aviso.width - 20),
                       15, CREMA, centrado=True)
        else:
            local = len(self.criptas) > 0 and "ancho" in self.criptas[0][1]
            self.texto(ANCHO // 2, ALTO - 20,
                       "modo demostración local: motor determinista y estructuras propias" if local
                       else "modo conectado / offline: motor determinista y estructuras propias",
                       14, (75, 85, 115), centrado=True)

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
        elif self.escena == "mapa":
            self._dibujarMapaModal()
        elif self.escena == "historia":
            self._dibujarHistoriaModal()
        elif self.escena == "resolubilidad":
            self._dibujarResolubilidadModal()
        elif self.escena == "final":
            self._dibujarFinal()
        # La viñeta sólo oscurece el escenario: las cajas de la interfaz mantienen su contraste.
        zona = ESCENARIO.inflate(10, 10)
        self.pantalla.blit(self._vineta(zona.width, zona.height), zona.topleft)
        # Advertencia visual de vida baja (viñeta pulsante roja)
        if self.captura is not None and self.captura.jugador is not None:
            jugador = self.captura.jugador
            if 0 < jugador.vida <= int(jugador.vidaMax * 0.25):
                pulso = int(45 + 35 * math.sin(pygame.time.get_ticks() / 110.0))
                sPeligro = pygame.Surface((ESCENARIO.width, ESCENARIO.height), pygame.SRCALPHA)
                for g in range(1, 8):
                    alfa = int(pulso * (1.0 - g / 8.0))
                    pygame.draw.rect(sPeligro, (220, 20, 20, alfa),
                                     sPeligro.get_rect().inflate(-g * 2, -g * 2), 2, border_radius=10)
                self.pantalla.blit(sPeligro, ESCENARIO.topleft)
        self._dibujarParticulas()
        self._dibujarFlotantes()
        self._dibujarDestello()
        if self.mostrarAyuda:
            self._dibujarAyudaModal()
        self._dibujarTransicion()

    def _dibujarSala(self):
        sala = self.captura.sala
        ticks = pygame.time.get_ticks()
        temblor = self._sacudir()
        base = ESCENARIO.move(temblor)
        self.pantalla.blit(self._escenario(ESCENARIO.width, ESCENARIO.height, sala.id),
                           (base.x - MARGEN, base.y - MARGEN))
        suelo = base.inflate(-2 * MURO, -2 * MURO)
        # Antorchas de pared con fuego vivo en el muro norte
        for idxT, tx in enumerate((suelo.x + 36, suelo.right - 68)):
            ty = base.y + 4
            pulsoF = 0.65 + 0.25 * math.sin(ticks / 175.0 + idxT * 2.1) + 0.10 * math.cos(ticks / 80.0 + idxT)
            haloP = self._halo(130).copy()
            haloP.set_alpha(int(155 * max(0.3, min(1.0, pulsoF))))
            self.pantalla.blit(haloP, (tx + 16 - 65, ty + 14 - 65))
            pygame.draw.rect(self.pantalla, _oscurece(ACERO, 0.45), pygame.Rect(tx + 12, ty + 22, 8, 6))
            self.blitear("antorcha", tx, ty, 2)
            chispaY = ty + 4 - int((ticks / 90 + idxT * 7) % 10)
            pygame.draw.rect(self.pantalla, DORADO, pygame.Rect(tx + 15 + (idxT % 2), chispaY, 2, 2))
        self._dibujarBrasasAmbiente(suelo, ticks, 10)
        # Ambientación especial: círculo rúnico en Sala de Salida y alerta de Cazador
        if getattr(sala, "esSalida", False):
            pulsoSal = int(150 + 80 * math.sin(ticks / 190.0))
            cxS, cyS = suelo.centerx, suelo.centery + 8
            pygame.draw.circle(self.pantalla, (pulsoSal, int(pulsoSal * 0.78), 36), (cxS, cyS), 36, 2)
            pygame.draw.circle(self.pantalla, DORADO_OSCURO, (cxS, cyS), 26, 1)
            pygame.draw.rect(self.pantalla, DORADO, pygame.Rect(cxS - 18, cyS - 18, 36, 36), 1)
        hayCazadorSala = any(getattr(e, "comportamiento", "") == "cazador" for e in sala.enemigos)
        if hayCazadorSala:
            pulsoCazSala = int(150 + 95 * math.sin(ticks / 150.0))
            avisoCaz = pygame.Rect(suelo.centerx - 118, base.y + 8, 236, 20)
            pygame.draw.rect(self.pantalla, (28, 10, 16), avisoCaz, border_radius=5)
            pygame.draw.rect(self.pantalla, (pulsoCazSala, 44, 44), avisoCaz, 1, border_radius=5)
            self.texto(avisoCaz.centerx, avisoCaz.centery, "¡CAZADOR EN LA SALA!", 13,
                       (255, 110, 110), centrado=True, sombra=TINTA)
        self._dibujarSalidas(base, sala)
        bobHeroe = int(2.0 * math.sin(ticks / 280.0))
        spriteHeroe = "heroe"
        if self._activoCaminar() and self.hx is not None:
            if self.moviendo:
                ciclo = int(self.fasePaso * 10.0) % 4
                if ciclo == 0:
                    spriteHeroe = "heroe_paso1"
                elif ciclo == 2:
                    spriteHeroe = "heroe_paso2"
                rebote = int(3 * abs(math.sin(self.fasePaso * 10.0 * math.pi / 2.0)))
            else:
                rebote = 0
            hx, hy = int(self.hx), int(self.hy) - rebote
        else:
            hx, hy = suelo.centerx - 24, suelo.bottom - 92 + bobHeroe
        # Si el jugador lleva antorcha encendida, proyectar halo cálido pulsante en la sala.
        jugadorCap = self.captura.jugador
        if jugadorCap is not None and any("antorcha" in str(ef).lower() for ef in jugadorCap.efectos):
            pulsoAnt = int(125 + 45 * math.sin(ticks / 190.0))
            haloAnt = self._halo(200).copy()
            haloAnt.set_alpha(pulsoAnt)
            self.pantalla.blit(haloAnt, (hx + 24 - 100, hy + 24 - 100))
        # El héroe va debajo de los objetos: comparten fila y sus etiquetas deben quedar visibles.
        rect = self._dibujarActor(spriteHeroe, hx, hy, 3,
                                  self._alpha("jugador"), "jugador")
        self.registrar("jugador", rect)
        for i in range(len(sala.suelo)):
            objeto = sala.suelo[i]
            x, y = self._posicionSuelo(i, suelo)
            floteObj = int(2.0 * math.sin(ticks / 240.0 + i * 1.1))
            escala = 2
            rect = self._dibujarActor(objeto.ficha.sprite, x, y + floteObj, escala)
            self.registrar("suelo-%d" % i, rect)
            if math.sin(ticks / 210.0 + i * 1.7) > 0.35:
                pygame.draw.circle(self.pantalla, DORADO, (rect.right - 2, rect.top + 2), 2)
            self.texto(rect.centerx, rect.bottom + 8 - floteObj, str(i + 1), 17, DORADO, centrado=True,
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
            bobE = int(2.0 * math.sin(ticks / 230.0 + i * 1.4)) if enemigo.activo else 0
            escala = 3
            rect = self._dibujarActor(enemigo.sprite, x, y + bobE, escala,
                                      self._alpha(enemigo.etiqueta), enemigo.etiqueta)
            self.registrar(enemigo.etiqueta, rect)
            etiqueta = pygame.Rect(rect.x - 6, rect.y - 26, 132, 22)
            # Con la sala llena sólo quedan el índice y la fila de enemigos del panel: la barra de
            # vida de cada sprite no cabría entre dos filas de la cuadrícula.
            esCazador = getattr(enemigo, "comportamiento", "") == "cazador"
            rangoCaz = getattr(enemigo, "rango", 0)
            tagCaz = (" [CAZ R:%d]" % rangoCaz) if (esCazador and rangoCaz > 0) else (" [CAZ]" if esCazador else "")
            if esCazador:
                pulsoR = int(170 + 80 * math.sin(ticks / 170.0 + i))
                pygame.draw.rect(self.pantalla, (pulsoR, 48, 48), rect.inflate(6, 6), 2, border_radius=6)
            etiquetaTexto = "%d) %s%s" % (i + 1, "" if salaLlena else enemigo.nombre.upper(), tagCaz)
            self.texto(etiqueta.x + 2, etiqueta.y,
                       _recortar(self.fuente(17), etiquetaTexto, etiqueta.width - 4), 17,
                       ROJO if esCazador else (BLANCO if enemigo.activo else APAGADO), sombra=TINTA)
            if salaLlena:
                continue
            self.barraVida(pygame.Rect(rect.x, rect.bottom + 4, rect.width, 20),
                           self._valorMostrado(enemigo.etiqueta, enemigo.vida),
                           enemigo.vidaMax, "", True)
        if self.escena == "escenario" and not self.combate:
            if self.modoCaminar:
                self._chip((base.x + 118, base.y + 16), "CAMINANDO (WASD) · [C] MENÚ", AMARILLO,
                           base.inflate(-4, -4))
                if self.hx is not None and not self._bloqueado() and self.submenu is None:
                    objetivo = self._objetivoCercano()
                    if objetivo is not None:
                        accion, dato = objetivo
                        if accion == ACC_RECOGER:
                            txtObj, tonoObj = "Z: TOMAR", VERDE
                        elif accion == ACC_ABRIR:
                            txtObj, tonoObj = "Z: ABRIR", DORADO
                        else:
                            txtObj, tonoObj = "Z: IR %s" % dato, CIAN
                        self._chip((int(self.hx) + 24, int(self.hy) - 10), txtObj, tonoObj,
                                   base.inflate(-4, -4))
            else:
                self._chip((base.x + 76, base.y + 16), "[C] CAMINAR (WASD)", ACERO,
                           base.inflate(-4, -4))

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
            # Arco y marco de sillería de piedra pixel-art alrededor de la puerta
            marcoP = pygame.Rect(x - 6, y - 4, 60, 56).clamp(base)
            pygame.draw.rect(self.pantalla, _oscurece(PIEDRA, 0.55), marcoP, border_radius=5)
            pygame.draw.rect(self.pantalla, _aclara(PIEDRA, 0.22), marcoP.inflate(-4, -4), 2, border_radius=4)
            # Dovelas laterales y piedra angular (keystone) con gema de estado
            for dyD in range(marcoP.y + 4, marcoP.bottom - 6, 10):
                pygame.draw.rect(self.pantalla, _aclara(PIEDRA, 0.14), pygame.Rect(marcoP.x + 1, dyD, 5, 7))
                pygame.draw.rect(self.pantalla, _aclara(PIEDRA, 0.14), pygame.Rect(marcoP.right - 6, dyD, 5, 7))
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
            keystone = pygame.Rect(marcoP.centerx - 5, marcoP.y, 10, 6)
            pygame.draw.rect(self.pantalla, _aclara(PIEDRA, 0.30), keystone)
            pygame.draw.rect(self.pantalla, tono, keystone.inflate(-4, -2))
            pasado = ((rect.centerx, base.top + 14) if salida.direccion == "N" else
                      (rect.centerx, base.bottom - 14) if salida.direccion == "S" else
                      (base.left + 22, rect.centery) if salida.direccion == "O" else
                      (base.right - 22, rect.centery))
            costoTexto = " (%d)" % salida.costo
            autoTexto = " [AUTO %d]" % salida.cierreAutomatico if getattr(salida, "cierreAutomatico", None) is not None else ""
            tonoChip = tono
            if salida.transitable and salida.costo > 100 and not salida.esSalida:
                tonoChip = AMARILLO
            elif salida.transitable and salida.costo < 100 and not salida.esSalida:
                tonoChip = VERDE
            chipRect = self._chip(pasado, "%s %s%s%s" % (salida.direccion, texto, costoTexto, autoTexto), tonoChip,
                                  base.inflate(-4, -4))
            esHover = rect.collidepoint(self.posRaton) or (chipRect and chipRect.collidepoint(self.posRaton))
            if esHover:
                pulsoH = int(180 + 75 * math.sin(pygame.time.get_ticks() / 120.0))
                pygame.draw.rect(self.pantalla, (pulsoH, pulsoH, 255), rect.inflate(8, 8), 2, border_radius=6)
                if chipRect:
                    pygame.draw.rect(self.pantalla, BLANCO, chipRect.inflate(4, 4), 1, border_radius=5)
            self.zona(rect.inflate(14, 14), UI_SUBMENU,
                      "abrir" if salida.cerrada else "mover")
            if chipRect:
                self.zona(chipRect, ACC_ABRIR if salida.cerrada else ACC_MOVER, salida.direccion)

    def _arena(self, ancho, alto):
        """Fondo de combate de fantasía oscura: losas rúnicas y plataformas pixel-art escalonadas."""
        clave = ("arena", ancho, alto)
        cara = self.escenarios.get(clave)
        if cara is not None:
            return cara
        marco = pygame.Rect(4, 4, ancho, alto)
        cara = pygame.Surface((ancho + 8, alto + 8), pygame.SRCALPHA)
        pygame.draw.rect(cara, _oscurece(PANEL, 0.30), cara.get_rect(), border_radius=14)
        pygame.draw.rect(cara, (18, 20, 38), marco, border_radius=10)
        # Suelo de baldosas oscuras con grietas en el fondo de la arena
        for fy in range(marco.y + 28, marco.bottom - 12, 32):
            pygame.draw.line(cara, (26, 30, 54), (marco.x + 12, fy), (marco.right - 12, fy), 1)
        for fx in range(marco.x + 32, marco.right - 12, 48):
            pygame.draw.line(cara, (24, 28, 50), (fx, marco.y + 28), (fx, marco.bottom - 12), 1)
        # Muro superior de arcos de mazmorra
        muroSup = pygame.Rect(marco.x + 4, marco.y + 4, marco.width - 8, 26)
        pygame.draw.rect(cara, _oscurece(PIEDRA, 0.35), muroSup)
        for lx in range(muroSup.x, muroSup.right - 20, 44):
            lad = pygame.Rect(lx, muroSup.y + 2, 40, 20).clamp(muroSup)
            pygame.draw.rect(cara, PIEDRA, lad)
            pygame.draw.rect(cara, _oscurece(PIEDRA, 0.60), lad, 1)
        # Plataformas de combate en pixel-art escalonado (sin elipses con antialiasing)
        plate = pygame.Rect(marco.x + 44, marco.y + 42, ancho - 88, 174)
        self._dibujarPlataformaPixel(cara, plate, _aclara(AGUA, 0.20), AGUA_CLARA, _oscurece(AGUA, 0.35))
        self._dibujarPlataformaPixel(cara, plate.inflate(-36, -28), _aclara(AGUA, 0.28), BORDE_ACERO, AGUA_CLARA)
        frente = pygame.Rect(marco.centerx - 184, marco.bottom - 148, 368, 134)
        self._dibujarPlataformaPixel(cara, frente, _aclara(AGUA, 0.30), BORDE_ACERO, AGUA_CLARA)
        self._dibujarPlataformaPixel(cara, frente.inflate(-40, -26), _aclara(AGUA, 0.38), DORADO_OSCURO, BORDE_ACERO)
        pygame.draw.rect(cara, DORADO_OSCURO, marco, 2, border_radius=10)
        cara.blit(self._luz(ancho + 8, alto + 8), (0, 0))
        return self._guardar(self.escenarios, clave, cara)

    def _dibujarCombate(self):
        sala = self.captura.sala
        ticksComb = pygame.time.get_ticks()
        temblor = self.sacudida if self.sacudida > 0 else 0
        base = ESCENARIO.move((int(temblor * math.sin(ticksComb / 38.0)),
                               int(temblor * math.cos(ticksComb / 27.0))))
        self.pantalla.blit(self._arena(ESCENARIO.width, ESCENARIO.height),
                           (base.x - 4, base.y - 4))
        # Antorchas laterales parpadeantes y brasas flotantes en la arena de combate
        for idxT, tx in enumerate((base.x + 18, base.right - 50)):
            ty = base.y + 8
            pulsoA = 0.65 + 0.30 * math.sin(ticksComb / 170.0 + idxT * 2.0)
            haloA = self._halo(120).copy()
            haloA.set_alpha(int(145 * pulsoA))
            self.pantalla.blit(haloA, (tx + 16 - 60, ty + 16 - 60))
            self.blitear("antorcha", tx, ty, 2)
        self._dibujarBrasasAmbiente(base.inflate(-24, -24), ticksComb, 12)
        enemigos = sala.enemigos
        compacto = len(enemigos) > 4
        escala = 3 if compacto else 4
        posiciones = ((base.x + 150, base.y + 62), (base.x + 330, base.y + 34),
                      (base.x + 470, base.y + 70), (base.x + 250, base.y + 132))
        for i in range(len(enemigos)):
            enemigo = enemigos[i]
            if compacto:
                x = base.x + 40 + (i % 4) * 140
                y = base.y + 30 + (i // 4) * 74
            else:
                x, y = posiciones[i % 4]
            bobC = int(2.0 * math.sin(ticksComb / 220.0 + i * 1.2))
            rect = self._dibujarActor(enemigo.sprite, x, y + bobC, escala, self._alpha(enemigo.etiqueta),
                                      enemigo.etiqueta)
            self.registrar(enemigo.etiqueta, rect)
            esCazador = getattr(enemigo, "comportamiento", "") == "cazador"
            rangoCaz = getattr(enemigo, "rango", 0)
            if esCazador:
                pulsoCaz = int(175 + 80 * math.sin(ticksComb / 160.0 + i))
                pygame.draw.rect(self.pantalla, (pulsoCaz, 44, 44), rect.inflate(8, 8), 2, border_radius=8)
                tagCaz = " [CAZ R:%d]" % rangoCaz if compacto else " [CAZADOR R:%d]" % rangoCaz
            else:
                tagCaz = ""
            nombreTexto = ("%d)" % (i + 1) if compacto else "%d) %s" % (i + 1, enemigo.nombre.upper()))
            if esCazador:
                nombreTexto += tagCaz
            # Placa superior con aire suficiente sobre el sprite (sin superponer [1] redundante)
            anchoPlaca = max(84 if compacto else 136, self.fuente(16).size(nombreTexto)[0] + 14)
            etiqueta = pygame.Rect(rect.centerx - anchoPlaca // 2, max(base.y + 6, rect.top - 24), anchoPlaca, 20)
            pygame.draw.rect(self.pantalla, (12, 14, 26), etiqueta, border_radius=4)
            pygame.draw.rect(self.pantalla, ROJO if esCazador else BORDE_ACERO, etiqueta, 1, border_radius=4)
            self.texto(etiqueta.centerx, etiqueta.centery, nombreTexto,
                       15, ROJO if esCazador else BLANCO, centrado=True, sombra=TINTA)
            self.barraVida(pygame.Rect(rect.centerx - (48 if compacto else 75),
                                       y + 44 if compacto else y + 66,
                                       96 if compacto else 150, 20 if compacto else 24),
                           self._valorMostrado(enemigo.etiqueta, enemigo.vida),
                           enemigo.vidaMax, "", True)
            areaEnemigo = rect.inflate(14, 22)
            hover = areaEnemigo.collidepoint(self.posRaton)
            if (self.submenu is not None and self.submenu == "objetivo" and
                    self.cursorSub == i) or hover:
                self._dibujarBlanco(rect)
            self.zona(areaEnemigo, ACC_ATACAR, enemigo.indice)
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
        # Medallón RPG biselado alrededor del retrato del héroe
        marcoRetrato = pygame.Rect(CAJA_JUGADOR.x + 10, CAJA_JUGADOR.y + 8, 56, 56)
        enPeligro = self.combate or (0 < jugador.vida <= int(jugador.vidaMax * 0.30))
        bordeRet = ROJO if enPeligro else DORADO
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.45), marcoRetrato, border_radius=8)
        pygame.draw.rect(self.pantalla, bordeRet, marcoRetrato, 2, border_radius=8)
        self.blitear("heroe", CAJA_JUGADOR.x + 14, CAJA_JUGADOR.y + 12, 3,
                     self._alpha("retrato"), "retrato")
        self.registrar("retrato", pygame.Rect(CAJA_JUGADOR.x + 14, CAJA_JUGADOR.y + 12, 48, 48))
        nombre = self.texto(CAJA_JUGADOR.x + 74, CAJA_JUGADOR.y + 10, jugador.nombre.upper(), 21,
                            DORADO, sombra=TINTA)
        inicio = max(CAJA_JUGADOR.x + 192, nombre.right + 12)
        self.barraVida(pygame.Rect(inicio, CAJA_JUGADOR.y + 10,
                                   min(210, CAJA_JUGADOR.x + 406 - inicio), 34),
                       self._valorMostrado("jugador", jugador.vida), jugador.vidaMax, "VIDA")
        self.texto(CAJA_JUGADOR.right - 16, CAJA_JUGADOR.y + 12,
                   "RELOJ %05d" % self.captura.sala.reloj, 19, CIAN, derecha=True, sombra=TINTA)
        # Atributos con mini-iconos pixel-art
        ax = CAJA_JUGADOR.x + 74
        ay = CAJA_JUGADOR.y + 45
        for icono, txtAtr in (("daga", _atributo("ATR", jugador.ataque, jugador.bonoAtaque)),
                              ("armadura", _atributo("DEF", jugador.defensa, jugador.bonoDefensa)),
                              ("pocion", "VEL %d" % jugador.velocidad)):
            self.blitear(icono, ax, ay - 1, 1)
            rTxt = self.texto(ax + 19, ay, txtAtr, 16, PERLA)
            ax = rTxt.right + 14
        if len(jugador.efectos) > 0:
            # Pastillas coloreadas para efectos activos
            ex = ax + 4
            for ef in jugador.efectos[:2]:
                efUp = str(ef).upper()
                tonoEf = DORADO if "ANTORCHA" in efUp else (
                    ROJO if "VENENO" in efUp else (CIAN if "VEL" in efUp else VERDE)
                )
                efCorto = _recortar(self.fuente(12), efUp, max(40, CAJA_JUGADOR.right - 14 - ex))
                wEf = self.fuente(12).size(efCorto)[0] + 12
                if ex + wEf > CAJA_JUGADOR.right - 8:
                    break
                chipEf = pygame.Rect(ex, ay, wEf, 18)
                pygame.draw.rect(self.pantalla, _oscurece(tonoEf, 0.72), chipEf, border_radius=4)
                pygame.draw.rect(self.pantalla, tonoEf, chipEf, 1, border_radius=4)
                self.texto(chipEf.centerx, chipEf.centery, efCorto, 12, BLANCO, centrado=True)
                ex += wEf + 6

    def _dibujarMinimapa(self):
        self.caja(CAJA_MINI)
        self._encabezado(CAJA_MINI, "MAPA", derecha="SALA %02d  [M]" % self.captura.sala.id)
        celdas = self.captura.celdas
        if len(celdas) == 0:
            return
        visibles = [c for c in celdas if c.visitada or c.avistada]
        if len(visibles) == 0:
            visibles = celdas
        minX = minY = 10 ** 6
        maxX = maxY = -10 ** 6
        for celda in visibles:
            minX = min(minX, celda.x)
            maxX = max(maxX, celda.x)
            minY = min(minY, celda.y)
            maxY = max(maxY, celda.y)
        area = pygame.Rect(CAJA_MINI.x + 12, CAJA_MINI.y + 38, CAJA_MINI.width - 24,
                           CAJA_MINI.height - 62)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.50), area, border_radius=8)
        pygame.draw.rect(self.pantalla, AGUA_CLARA, area, 1, border_radius=8)
        anchoCelda = max(8, min(24, area.width // max(1, maxX - minX + 1)))
        altoCelda = max(8, min(24, area.height // max(1, maxY - minY + 1)))
        lado = min(anchoCelda, altoCelda)
        offsetX = area.centerx - (maxX - minX + 1) * lado / 2.0
        offsetY = area.centery - (maxY - minY + 1) * lado / 2.0
        posVisibles = set((c.x, c.y) for c in visibles)
        for celda in visibles:
            cx = int(offsetX + (celda.x - minX) * lado + (lado - 2) / 2.0)
            cy = int(offsetY + (celda.y - minY) * lado + (lado - 2) / 2.0)
            if (celda.x + 1, celda.y) in posVisibles:
                pygame.draw.line(self.pantalla, AGUA_CLARA, (cx, cy), (cx + lado, cy), 2)
            if (celda.x, celda.y + 1) in posVisibles:
                pygame.draw.line(self.pantalla, AGUA_CLARA, (cx, cy), (cx, cy + lado), 2)
        hoverCelda = None
        for celda in visibles:
            rect = pygame.Rect(offsetX + (celda.x - minX) * lado,
                               offsetY + (celda.y - minY) * lado, lado - 2, lado - 2)
            esHover = rect.collidepoint(self.posRaton)
            if not celda.visitada:
                # Sala avistada pero sin explorar (§3.3 Niebla de guerra)
                pygame.draw.rect(self.pantalla, (38, 44, 68), rect, border_radius=3)
                pygame.draw.rect(self.pantalla, ACERO, rect, 1, border_radius=3)
                if lado >= 14:
                    self.texto(rect.centerx, rect.centery, "?", 11, ACERO, centrado=True)
                continue
            if celda.actual:
                pulso = int(120 + 100 * math.sin(pygame.time.get_ticks() / 220.0))
                tono = (int(pulso * 0.4), pulso, 220)
            elif celda.esSalida:
                tono = (176, 138, 44)
            else:
                tono = (92, 112, 160) if esHover else (74, 88, 128)
            pygame.draw.rect(self.pantalla, tono, rect, border_radius=3)
            if celda.cerrada:
                pygame.draw.rect(self.pantalla, ROJO, rect, 1, border_radius=3)
            elif esHover:
                pygame.draw.rect(self.pantalla, CIAN, rect, 1, border_radius=3)
            if celda.esSalida:
                self.texto(rect.centerx, rect.centery, "S", 13, DORADO, centrado=True)
            if celda.actual:
                self.texto(rect.centerx, rect.centery, "@", 14, BLANCO, centrado=True)
                if math.sin(pygame.time.get_ticks() / 180.0) > 0:
                    pygame.draw.rect(self.pantalla, BLANCO, rect.inflate(2, 2), 1, border_radius=4)
            if esHover:
                hoverCelda = celda
            self.zona(rect, UI_SERVICIO, "ir_a:%d" % celda.idSala)
        jugador = self.captura.jugador
        if hoverCelda is not None:
            pie = "CLIC: IR A SALA %d (%s)" % (hoverCelda.idSala, hoverCelda.nombre)
            self.texto(CAJA_MINI.x + 14, CAJA_MINI.bottom - 22,
                       _recortar(self.fuente(14), pie, CAJA_MINI.width - 28), 14, CIAN)
        else:
            self.texto(CAJA_MINI.x + 14, CAJA_MINI.bottom - 22,
                       "acc %d  bajas %d  [M] mapa  [T] hist" % (jugador.acciones, jugador.derrotados), 13, ACERO)

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
        limite = CAJA_ESTADO.bottom - 42
        y = arriba - 2
        for i, (nombre, sprite, dato, tono, disponible) in enumerate(filas):
            if y > limite:
                self.texto(CAJA_ESTADO.x + 14, limite, "y %d líneas más" % (len(filas) - i), 14,
                           ACERO)
                break
            if sprite is None:
                self.texto(CAJA_ESTADO.x + 14, y, nombre, 13, _aclara(tono, 0.15), sombra=TINTA)
                y += 18
            else:
                rect = pygame.Rect(CAJA_ESTADO.x + 16, y - 3, CAJA_ESTADO.width - 32, 18)
                self.blitear(sprite, rect.x, rect.y - 1, 1)
                sobra = rect.width - 24 - self.fuente(13).size(dato)[0] - 12
                self.texto(rect.x + 20, y,
                           _recortar(self.fuente(14), nombre.upper(), sobra), 14,
                           BLANCO if disponible else APAGADO)
                if len(dato) > 0:
                    self.texto(rect.right - 2, y + 1, dato, 13, tono if disponible else APAGADO,
                               derecha=True)
                y += 19
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
            # Barra rápida interactiva para funciones de Parte II, ayuda y SFX
            sfxLbl = "[F2] SFX:ON" if self.sfx.activo else "[F2] SFX:OFF"
            accesos = (
                ("[M] MAPA", "abrir_mapa", True, DORADO),
                ("[T] HISTORIA", "historia", True, CIAN),
                ("[R] RESOLUB.", "resolubilidad", len(self.resolubilidadTexto) > 0, VERDE),
                ("[H] AYUDA", "abrir_ayuda", True, PERLA),
                (sfxLbl, "toggle_sfx", True, VERDE if self.sfx.activo else ACERO),
            )
            ax = CAJA_TEXTO.x + 20
            ay = CAJA_TEXTO.bottom - 34
            for txtAcc, datoAcc, habAcc, tonoAcc in accesos:
                wAcc = self.fuente(13).size(txtAcc)[0] + 18
                btn = pygame.Rect(ax, ay, wAcc, 22)
                hov = habAcc and btn.collidepoint(self.posRaton)
                self.caja(btn, relleno=_aclara(PANEL, 0.25) if hov else PANEL,
                          borde=BLANCO if hov else (tonoAcc if habAcc else AGUA_CLARA), grosor=1, radio=5)
                self.texto(btn.centerx, btn.centery, txtAcc, 13,
                           BLANCO if hov else (tonoAcc if habAcc else APAGADO), centrado=True)
                self.zona(btn, UI_SERVICIO, datoAcc, habAcc)
                ax += wAcc + 8

    def _dibujarMenu(self):
        self.caja(CAJA_MENU, relleno=PANEL_CLARO)
        entradas = self._entradasMenu()
        if self.submenu is not None:
            entradas = self._entradasSubmenu()
            cursor = min(self.cursorSub, max(0, len(entradas) - 1))
            titulo = {"objetivo": "objetivo", "mover": "dirección",
                      "abrir": "puertas"}.get(self.submenu, "tomar")
        else:
            cursor = min(self.cursorMenu, max(0, len(entradas) - 1))
            titulo = "¿qué haces?"
        arriba = self._encabezado(CAJA_MENU, titulo)
        # 24 px por fila: las seis acciones del menú caben sin que el cursor tenga que desplazarse.
        self._listaEntradas(CAJA_MENU, entradas, cursor, arriba, 24,
                            "x vuelve" if self.submenu is not None else "i bolsa  esc menú")

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
            esHover = rect.collidepoint(self.posRaton)
            if i == cursor:
                self._resaltar(rect, SELECCION)
                self.flecha(rect)
            elif esHover and entrada.habilitada:
                pygame.draw.rect(self.pantalla, BORDE_ACERO, rect, 1, border_radius=6)
            if entrada.habilitada:
                self._tecla(rect, acento)
            centro = rect.y + max(2, (rect.height - fuente.get_linesize()) // 2)
            etiqueta = self.texto(rect.x + 30, centro, entrada.texto.upper(), 17,
                                  BLANCO if (i == cursor or esHover) and entrada.habilitada
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
            esHover = rect.collidepoint(self.posRaton)
            if seleccionado:
                self._resaltar(rect, SELECCION)
                self.flecha(rect)
            elif esHover:
                pygame.draw.rect(self.pantalla, BORDE_ACERO, rect, 1, border_radius=6)
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
        panel = pygame.Rect(280, 120, 420, 420)
        self.caja(panel, relleno=PANEL_CLARO)
        entradas = self._entradasSistema()
        arriba = self._encabezado(panel, "menú del sistema")
        self._listaEntradas(panel, entradas, min(self.cursorSistema, len(entradas) - 1),
                            arriba, 34, "guardado: %s" % self.rutaGuardado)

    def _dibujarBitacora(self):
        panel = pygame.Rect(120, 90, 740, 460)
        self.caja(panel, relleno=PANEL_CLARO)
        arriba = self._encabezado(panel, "bitácora de eventos",
                                  derecha="últimos %d mensajes" % len(self.historial))
        y = arriba + 4
        for mensaje in self.historial[-17:]:
            self.texto(panel.x + 24, y, mensaje, 17, PERLA)
            y += 24
        self.texto(panel.x + 24, panel.bottom - 26, "X / TAB vuelve", 16, ACERO)

    def _cargarHistoria(self, k=None, t=None):
        if self.modelo is None:
            return
        maxAcc = max(1, self.modelo.jugador.acciones + 1)
        maxT = max(0, self.modelo.reloj)
        if k is not None:
            self.historiaAccion = max(1, min(maxAcc, int(k)))
        if t is not None:
            self.historiaTiempo = max(0, min(maxT, int(t)))
        try:
            if self.historiaModo == "tiempo":
                self.historiaTexto = self.modelo.consultarHistoriaTiempo(self.historiaTiempo)
            else:
                self.historiaTexto = self.modelo.consultarHistoriaAccion(self.historiaAccion)
        except Exception as error:
            self.historiaTexto = "Error al consultar historia: %s" % error

    def _dibujarHistoriaModal(self):
        panel = pygame.Rect(90, 62, 800, 536)
        self.caja(panel, relleno=PANEL_CLARO, borde=CIAN)
        maxAcc = max(1, self.modelo.jugador.acciones + 1)
        maxT = max(0, self.modelo.reloj)
        if self.historiaModo == "tiempo":
            tituloDer = "TIEMPO t = %d / %d" % (self.historiaTiempo, maxT)
            progreso = (self.historiaTiempo / maxT) if maxT > 0 else 1.0
        else:
            tituloDer = "ACCIÓN #%d / %d" % (self.historiaAccion, maxAcc)
            progreso = ((self.historiaAccion - 1) / (maxAcc - 1)) if maxAcc > 1 else 1.0
        arriba = self._encabezado(panel, "LÍNEA DE TIEMPO (HISTORIA #k / t)", derecha=tituloDer)

        # Barra visual de línea de tiempo con marcadores de checkpoints dorados
        pista = pygame.Rect(panel.x + 24, arriba + 4, panel.width - 48, 12)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.5), pista, border_radius=6)
        pygame.draw.rect(self.pantalla, AGUA_CLARA, pista, 1, border_radius=6)
        llenoW = max(6, int(pista.width * max(0.0, min(1.0, progreso))))
        pygame.draw.rect(self.pantalla, _mezclar(CIAN, VERDE, 0.25),
                         pygame.Rect(pista.x, pista.y, llenoW, pista.height), border_radius=6)
        lt = getattr(self.modelo, "lineaTiempo", None)
        if lt is not None and hasattr(lt, "_puntosControl"):
            for cp in lt._puntosControl:
                if self.historiaModo == "tiempo":
                    frac = (cp.reloj / maxT) if maxT > 0 else 0.0
                else:
                    frac = (cp.numAccion / maxAcc) if maxAcc > 0 else 0.0
                cx = int(pista.x + pista.width * max(0.0, min(1.0, frac)))
                pygame.draw.circle(self.pantalla, DORADO, (cx, pista.centery), 4)
        curX = int(pista.x + pista.width * max(0.0, min(1.0, progreso)))
        pulsoCur = 6 + int(2 * math.sin(pygame.time.get_ticks() / 160.0))
        pygame.draw.circle(self.pantalla, BLANCO, (curX, pista.centery), pulsoCur)
        pygame.draw.circle(self.pantalla, CIAN, (curX, pista.centery), 4)

        y = pista.bottom + 12
        lineas = self.historiaTexto.splitlines() if self.historiaTexto else ["Sin datos históricos."]
        for linea in lineas[:15]:
            for sub in _envolver(linea, 78):
                if y > panel.bottom - 98:
                    break
                tono = DORADO if sub.startswith("===") else (CIAN if sub.startswith("Jugador:") or sub.startswith("Sala") else PERLA)
                self.texto(panel.x + 24, y, sub, 16, tono)
                y += 20

        # Botones de navegación temporal y alternador de modo (#k vs t)
        if self.historiaModo == "tiempo":
            puedeMenos = self.historiaTiempo > 0
            puedeMas = self.historiaTiempo < maxT
            botones = (
                ("<< t=0", "hist_inicio", puedeMenos, 74),
                ("-100", "hist_delta:-100", puedeMenos, 54),
                ("-25 <", "hist_delta:-25", puedeMenos, 56),
                ("> +25", "hist_delta:25", puedeMas, 56),
                ("+100", "hist_delta:100", puedeMas, 54),
                ("ACTUAL >>", "hist_actual", puedeMas, 88),
                ("MODO: t -> #k", "hist_modo", True, 118),
                ("CERRAR [T]", "volver_escenario", True, 96),
            )
        else:
            puedeMenos = self.historiaAccion > 1
            puedeMas = self.historiaAccion < maxAcc
            botones = (
                ("<< #1", "hist_inicio", puedeMenos, 74),
                ("-5", "hist_delta:-5", puedeMenos, 54),
                ("-1 <", "hist_delta:-1", puedeMenos, 56),
                ("> +1", "hist_delta:1", puedeMas, 56),
                ("+5", "hist_delta:5", puedeMas, 54),
                ("ACTUAL >>", "hist_actual", puedeMas, 88),
                ("MODO: #k -> t", "hist_modo", True, 118),
                ("CERRAR [T]", "volver_escenario", True, 96),
            )
        bx = panel.x + 20
        by = panel.bottom - 50
        for etiqueta, dato, habilitada, ancho in botones:
            rect = pygame.Rect(bx, by, ancho, 32)
            hover = habilitada and rect.collidepoint(self.posRaton)
            esModo = (dato == "hist_modo")
            borde = BLANCO if hover else (DORADO if esModo else (CIAN if habilitada else AGUA_CLARA))
            relleno = _aclara(PANEL, 0.25) if hover else PANEL
            self.caja(rect, relleno=relleno, borde=borde, grosor=2, radio=6)
            self.texto(rect.centerx, rect.centery, etiqueta, 13,
                       DORADO if (esModo and not hover) else (BLANCO if habilitada else APAGADO), centrado=True)
            if dato == "volver_escenario":
                self.zona(rect, UI_IR, "volver")
            else:
                self.zona(rect, UI_SERVICIO, dato, habilitada)
            bx += ancho + 6

    def _dibujarMapaModal(self):
        panel = pygame.Rect(48, 48, 884, 564)
        self.caja(panel, relleno=PANEL_CLARO, borde=DORADO_OSCURO)
        mapa = self.modelo.mapaConocido
        from model.ordenamiento.Selector import ordenar
        exploradas = ordenar(mapa.listaExploradas())
        avistadas = ordenar(mapa.listaAvistadas(self.modelo.salas))
        arriba = self._encabezado(panel, "PLANO DEL MAPA CONOCIDO (CLIC EN SALA PARA IR A)",
                                  derecha="%d exploradas · %d avistadas" % (len(exploradas), len(avistadas)))

        # Columna Izquierda: Plano gráfico interactivo (respetando §3.3: solo exploradas y avistadas)
        areaPlano = pygame.Rect(panel.x + 18, arriba + 6, 510, panel.height - 96)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.55), areaPlano, border_radius=10)
        pygame.draw.rect(self.pantalla, AGUA_CLARA, areaPlano, 2, border_radius=10)

        celdas = [c for c in self.captura.celdas if c.visitada or c.avistada]
        salaInspId = self.mapaSalaSel if self.mapaSalaSel is not None else self.modelo.jugador.sala.id
        if len(celdas) > 0:
            minX = min(c.x for c in celdas)
            maxX = max(c.x for c in celdas)
            minY = min(c.y for c in celdas)
            maxY = max(c.y for c in celdas)
            cols = max(1, maxX - minX + 1)
            filas = max(1, maxY - minY + 1)
            paso = max(24, min(58, min((areaPlano.width - 40) // cols, (areaPlano.height - 40) // filas)))
            ox = areaPlano.centerx - (cols * paso) // 2
            oy = areaPlano.centery - (filas * paso) // 2
            porPos = {(c.x, c.y): c for c in celdas}

            # 1. Pasillos coloreados según estado recordado de la puerta (A=verde, C=rojo, ?=ámbar)
            for c in celdas:
                if not c.visitada:
                    continue
                cx = ox + (c.x - minX) * paso + paso // 2
                cy = oy + (c.y - minY) * paso + paso // 2
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    vec = porPos.get((c.x + dx, c.y + dy))
                    if vec is None:
                        continue
                    estP = mapa.estadoPuertaRecordada(c.idSala, vec.idSala)
                    tonoP = VERDE if estP == "abierta" else (ROJO if estP == "cerrada" else AMARILLO)
                    vx = ox + (vec.x - minX) * paso + paso // 2
                    vy = oy + (vec.y - minY) * paso + paso // 2
                    pygame.draw.line(self.pantalla, tonoP, (cx, cy), ((cx + vx) // 2, (cy + vy) // 2), 3)

            # 2. Nodos de salas exploradas y avistadas
            for c in celdas:
                nodo = pygame.Rect(ox + (c.x - minX) * paso + 4,
                                   oy + (c.y - minY) * paso + 4, paso - 8, paso - 8)
                hov = nodo.collidepoint(self.posRaton)
                if hov:
                    salaInspId = c.idSala
                    self.mapaSalaSel = c.idSala
                if not c.visitada:
                    pygame.draw.rect(self.pantalla, (34, 40, 64), nodo, border_radius=6)
                    pygame.draw.rect(self.pantalla, ACERO, nodo, 1, border_radius=6)
                    self.texto(nodo.centerx, nodo.centery, "?", 15, ACERO, centrado=True)
                    continue
                if c.actual:
                    tonoN = (48, 148, 196)
                    bordeN = BLANCO
                elif c.esSalida:
                    tonoN = (176, 136, 42)
                    bordeN = DORADO
                else:
                    tonoN = SELECCION if hov else (68, 84, 128)
                    bordeN = CIAN if hov else BORDE_ACERO
                pygame.draw.rect(self.pantalla, tonoN, nodo, border_radius=6)
                pygame.draw.rect(self.pantalla, bordeN, nodo, 2 if (c.actual or hov) else 1, border_radius=6)
                etq = "@%d" % c.idSala if c.actual else str(c.idSala)
                self.texto(nodo.centerx, nodo.centery, etq, 13 if paso >= 36 else 11,
                           BLANCO, centrado=True, sombra=TINTA)
                self.zona(nodo, UI_SERVICIO, "ir_a:%d" % c.idSala)

        # Columna Derecha: Inspector de Sala y Salidas Conocidas
        insp = pygame.Rect(areaPlano.right + 14, areaPlano.y, panel.right - areaPlano.right - 32, areaPlano.height)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.35), insp, border_radius=10)
        pygame.draw.rect(self.pantalla, BORDE_ACERO, insp, 1, border_radius=10)
        iy = self._encabezado(insp, "INSPECTOR DE SALA") + 4
        salaInsp = self.modelo.salas.buscar(salaInspId)
        if salaInsp is not None and mapa.estaExplorada(salaInspId):
            esAct = (salaInspId == self.modelo.jugador.sala.id)
            self.texto(insp.x + 14, iy, "SALA #%d %s" % (salaInsp.id, "(ACTUAL)" if esAct else ""),
                       17, DORADO if esAct else CIAN, sombra=TINTA)
            iy += 24
            self.texto(insp.x + 14, iy, _recortar(self.fuente(15), salaInsp.nombre, insp.width - 28), 15, BLANCO)
            iy += 28
            self.texto(insp.x + 14, iy, "SALIDAS RECORDADAS:", 13, ACERO)
            iy += 20
            for s in salaInsp.salidas:
                est = mapa.estadoPuertaRecordada(salaInsp.id, s.destinoId)
                if est == "abierta":
                    estTxt, estCol = "ABIERTA", VERDE
                elif est == "cerrada":
                    estTxt, estCol = "CERRADA", ROJO
                else:
                    estTxt, estCol = "SIN OBSERVAR", AMARILLO
                filaS = pygame.Rect(insp.x + 12, iy, insp.width - 24, 38)
                pygame.draw.rect(self.pantalla, PANEL, filaS, border_radius=5)
                pygame.draw.rect(self.pantalla, estCol, filaS, 1, border_radius=5)
                self.texto(filaS.x + 8, filaS.y + 4, "%s -> Sala %s (costo %d)" % (s.direccion, s.destinoId, s.costo),
                           14, PERLA)
                self.texto(filaS.x + 8, filaS.y + 20, "Puerta: %s" % estTxt, 12, estCol)
                iy += 44
            if not esAct:
                btnIr = pygame.Rect(insp.x + 16, insp.bottom - 48, insp.width - 32, 34)
                hovIr = btnIr.collidepoint(self.posRaton)
                self.caja(btnIr, relleno=_mezclar(PANEL, VERDE, 0.30 if hovIr else 0.16),
                          borde=BLANCO if hovIr else VERDE, grosor=2, radio=6)
                self.texto(btnIr.centerx, btnIr.centery, "VIAJAR A SALA #%d" % salaInsp.id, 14,
                           BLANCO, centrado=True)
                self.zona(btnIr, UI_SERVICIO, "ir_a:%d" % salaInsp.id)
        else:
            self.texto(insp.x + 14, iy, "SALA #%s (AVISTADA)" % salaInspId, 16, AMARILLO)
            iy += 26
            for lin in _envolver("Aún no has entrado a esta sala. Solo sabes que existe detrás de una salida explorada (§3.3).", 32):
                self.texto(insp.x + 14, iy, lin, 14, ACERO)
                iy += 20

        self.texto(panel.x + 22, panel.bottom - 28,
                   "Pasillos: Verde=Abierta | Rojo=Cerrada | Ámbar=Sin observar | Clic en sala: viajar | [M/X] Cerrar",
                   14, ACERO)

    def _dibujarResolubilidadModal(self):
        panel = pygame.Rect(110, 88, 760, 484)
        self.caja(panel, relleno=PANEL_CLARO, borde=VERDE)
        arriba = self._encabezado(panel, "REPORTE DE RESOLUBILIDAD (§3.5)")
        y = arriba + 8
        for linea in (self.resolubilidadTexto or "Sin reporte.").splitlines():
            for sub in _envolver(linea, 74):
                if y > panel.bottom - 44:
                    break
                self.texto(panel.x + 24, y, sub, 16, PERLA)
                y += 22
        self.texto(panel.x + 24, panel.bottom - 28, "X / ESC / Z para volver", 15, ACERO)

    def _dibujarAyudaModal(self):
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((8, 10, 18, 180))
        self.pantalla.blit(capa, (0, 0))
        panel = pygame.Rect(130, 80, 720, 500)
        self.caja(panel, relleno=PANEL_CLARO, borde=DORADO)
        arriba = self._encabezado(panel, "AYUDA Y CONTROLES — CRIPTA PARTE II")
        lineas = (
            ("WASD / Flechas", "Mover cursor o elegir acción en menú"),
            ("Z / Enter", "Confirmar acción / atacar / interactuar"),
            ("X / Esc", "Cancelar submenú / abrir menú sistema"),
            ("I", "Abrir o cerrar Bolsa (ordenar por peso/valor/nombre)"),
            ("M", "Mapa conocido (exploradas, avistadas, clic para ir a)"),
            ("T", "Línea de tiempo (historia #k y tiempo t, Tab alterna modo)"),
            ("R", "Ver reporte de resolubilidad de la cripta"),
            ("Tab / H", "Bitácora (20 eventos) / Mostrar u ocultar ayuda"),
            ("Clic minimapa", "Viaje automático «ir a» a cualquier sala explorada"),
            ("Cazadores", "Borde rojo pulsante + [CAZ R:x]: menor costo hasta ti"),
        )
        y = arriba + 10
        for tecla, desc in lineas:
            self._chip((panel.x + 96, y + 10), tecla, DORADO)
            self.texto(panel.x + 190, y + 2, desc, 16, PERLA)
            y += 38
        self.texto(panel.centerx, panel.bottom - 28, "Pulsa cualquier tecla o haz clic para cerrar", 15, ACERO,
                   centrado=True)

    def _dibujarFinal(self):
        resultado = presentacion.resultadoVisual(self.modelo)
        ticks = pygame.time.get_ticks()
        panel = pygame.Rect(190, 110, 600, 420)
        tono = VERDE if resultado.gano else ROJO
        self.caja(panel, relleno=_mezclar(PANEL, tono, 0.12), borde=tono)
        self._dibujarBrasasAmbiente(panel.inflate(-20, -20), ticks, 18)
        self.texto(panel.centerx, panel.y + 34, resultado.titulo.upper(), 40, tono, centrado=True,
                   sombra=TINTA)

        # Diorama de Victoria / Derrota
        platFin = pygame.Rect(panel.centerx - 110, panel.y + 118, 220, 42)
        self._dibujarPlataformaPixel(self.pantalla, platFin, (28, 34, 58), tono, DORADO_OSCURO)
        bobF = int(3.0 * math.sin(ticks / 240.0))
        if resultado.gano:
            self.blitear("heroe", panel.centerx - 48, panel.y + 68 + bobF, 4)
            self.blitear("llave", panel.centerx + 12, panel.y + 64 - bobF, 3)
        else:
            self.blitear("cazador", panel.centerx - 32, panel.y + 66 + bobF, 4)

        pygame.draw.line(self.pantalla, DORADO_OSCURO, (panel.x + 40, panel.y + 172),
                         (panel.right - 40, panel.y + 172))
        textos = (("acciones realizadas", resultado.acciones),
                  ("enemigos derrotados", resultado.derrotados),
                  ("tiempo virtual final", resultado.tiempoFinal),
                  ("semilla de expedición", self.semilla))
        y = panel.y + 188
        for etiqueta, valor in textos:
            self.texto(panel.x + 60, y, etiqueta.upper(), 18, ACERO)
            self.texto(panel.right - 60, y, str(valor), 18, BLANCO, derecha=True)
            pygame.draw.line(self.pantalla, AGUA_CLARA, (panel.x + 60, y + 24),
                             (panel.right - 60, y + 24))
            y += 34

        btnHist = pygame.Rect(panel.x + 50, panel.bottom - 48, 230, 34)
        hovHist = btnHist.collidepoint(self.posRaton)
        self.caja(btnHist, relleno=_mezclar(PANEL, CIAN, 0.28 if hovHist else 0.14),
                  borde=BLANCO if hovHist else CIAN, radio=6)
        self.texto(btnHist.centerx, btnHist.centery, "VER HISTORIA [T]", 15,
                   BLANCO if hovHist else PERLA, centrado=True)
        self.zona(btnHist, UI_SERVICIO, "historia")

        botonVolver = pygame.Rect(panel.right - 280, panel.bottom - 48, 230, 34)
        hoverVolver = botonVolver.collidepoint(self.posRaton)
        self.caja(botonVolver, relleno=_mezclar(PANEL, tono, 0.30 if hoverVolver else 0.15),
                  borde=BLANCO if hoverVolver else tono, radio=6)
        self.texto(botonVolver.centerx, botonVolver.centery, "VOLVER AL MENÚ [Z]", 15,
                   BLANCO if hoverVolver else PERLA, centrado=True)
        self.zona(botonVolver, UI_SERVICIO, "ir_portada")

    def _dibujarFlotantes(self):
        for entrada in self.flotantes:
            esDano = entrada[0].startswith("-")
            base = ROJO if esDano else VERDE
            factor = min(1.0, entrada[3] / 0.45)
            # Efecto pop-in en el texto flotante de daño
            tam = 28 if (esDano and entrada[3] > 0.95) else 24
            self.texto(entrada[1] + 2, entrada[2] + 2, entrada[0], tam, TINTA, centrado=True)
            self.texto(entrada[1], entrada[2], entrada[0], tam,
                       (int(base[0] * factor), int(base[1] * factor), int(base[2] * factor)),
                       centrado=True)

    def _dibujarParticulas(self):
        for p in self.particulas:
            x, y, _, _, vida, vidaMax, tono, radio = p
            factor = max(0.0, min(1.0, vida / max(0.01, vidaMax)))
            color = (int(tono[0] * factor), int(tono[1] * factor), int(tono[2] * factor))
            pygame.draw.circle(self.pantalla, color, (int(x), int(y)), max(1, int(radio * factor + 0.5)))
        # Trazos de corte diagonal (Sword Slash) sobre objetivos golpeados
        for cx, cy, vidaC, maxC, tonoC in self.cortes:
            progreso = 1.0 - (vidaC / max(0.01, maxC))
            largo = 28
            x0 = int(cx - largo + progreso * 10)
            y0 = int(cy - largo + progreso * 10)
            x1 = int(cx + largo - progreso * 6)
            y1 = int(cy + largo - progreso * 6)
            pygame.draw.line(self.pantalla, BLANCO, (x0, y0), (x1, y1), 4)
            pygame.draw.line(self.pantalla, tonoC, (x0 - 2, y0 + 2), (x1 - 2, y1 + 2), 2)

    def _dibujarDestello(self):
        if self.destello is None:
            return
        tono, resto = self.destello
        alfa = int(95 * min(1.0, resto / 0.25))
        if alfa <= 0:
            return
        capa = pygame.Surface((ESCENARIO.width, ESCENARIO.height), pygame.SRCALPHA)
        capa.fill((tono[0], tono[1], tono[2], alfa))
        self.pantalla.blit(capa, ESCENARIO.topleft)

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
        self.sfx.actualizarMusica(self.escena, self.combate)
        if self.escena == "portada":
            self._dibujarPortada()
        elif self.escena == "titulo":
            self._dibujarTitulo()
        else:
            self._dibujarJuego()
        self._dibujarTransicion()
        pygame.display.flip()

    def ejecutar(self):
        self.iniciar()
        reloj = pygame.time.Clock()
        while not self.terminar:
            dt = reloj.tick(60) / 1000.0
            self.paso(min(dt, 0.05))
        self.apagar()
