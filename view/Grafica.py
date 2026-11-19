# Vista grafica (pygame) con presentacion estilo Pokemon: escenario, cajas de texto y menus.
#
# La clase solo lee el estado del modelo y envia intenciones al controlador. No cambia reglas:
# toda mutacion pasa por Controlador.ejecutarAccion -> Modelo.ejecutar.

import math
import random

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
LADO_BASE = 16

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
        self.posiciones = []
        self.sacudida = 0.0
        self.salto = None
        self.transicion = 0.0
        self.combate = False
        self.mostrarAyuda = False
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
                superficie = sprites.construir(pygame, nombre, escala)
                self.hojas.append([nombre, escala, superficie])
                self._hojasMap[(nombre, escala)] = superficie

    def apagar(self):
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
        esHeroeJugador = (clave == "jugador" and nombre in ("heroe", "heroe_paso1", "heroe_paso2"))
        self._espejar = (esHeroeJugador and self.mira < 0 and self._activoCaminar())
        try:
            superficie = self.hoja(nombre, escala)
            if (clave is not None and self._destelloActivo(clave)
                    and superficie.get_flags() & pygame.SRCALPHA):
                superficie = self._hojaBlanca(nombre, escala)

            ladoBase = LADO_BASE * escala
            lado = ladoBase
            # Reducir tamaño de héroe y monstruos (excepto en el retrato pequeño del HUD)
            if nombre in self.ACTORES and clave != "retrato":
                lado = max(24, int(ladoBase * self.FACTOR_ACTOR))
                if superficie.get_size() != (lado, lado):
                    superficie = pygame.transform.scale(superficie, (lado, lado))

            dx = dy = 0
            if clave is not None:
                dx, dy = self.desplazamiento(clave)

            # Centrar el sprite reducido dentro de su celda original
            offset = (ladoBase - lado) // 2
            rect = pygame.Rect(int(x + dx + offset), int(y + dy + offset), lado, lado)

            if alpha < 255:
                copia = superficie.copy()
                copia.set_alpha(alpha)
                self.pantalla.blit(copia, rect)
            else:
                self.pantalla.blit(superficie, rect)
            return rect
        finally:
            self._espejar = False

    def _ladoHeroe(self):
        return max(24, int(LADO_BASE * 3 * self.FACTOR_ACTOR))

    def _suelo(self):
        # Área interior transitable estrictamente delimitada por las paredes de la sala
        margenPared = MURO + 10
        return ESCENARIO.inflate(-2 * margenPared, -2 * margenPared)

    def _caminar(self, dt):
        self.moviendo = False
        if not self._activoCaminar() or self.escena != "escenario":
            return
        suelo = self._suelo()
        lado = self._ladoHeroe()
        minX = float(suelo.left)
        maxX = float(max(suelo.left, suelo.right - lado))
        minY = float(suelo.top)
        maxY = float(max(suelo.top, suelo.bottom - lado))

        sala = self.captura.sala.id
        if self.hx is None or sala != self._salaCaminar:
            self._salaCaminar = sala
            self.hx = max(minX, min(maxX, float(suelo.centerx - lado // 2)))
            self.hy = max(minY, min(maxY, float(suelo.bottom - lado - 12)))

        if self.transicion > 0.55 or self.submenu is not None:
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

        # Bloqueo estricto contra las 4 paredes de la sala
        self.hx = max(minX, min(maxX, self.hx + dx * self.VELOCIDAD_CAMINAR * dt))
        self.hy = max(minY, min(maxY, self.hy + dy * self.VELOCIDAD_CAMINAR * dt))

        if dx != 0:
            self.mira = 1 if dx > 0 else -1
        self.moviendo = True
        self.fasePaso += dt

        # Cruzar automáticamente solo al llegar al umbral de una puerta abierta
        objetivo = self._objetivoCercano()
        if objetivo is not None and objetivo[0] == ACC_MOVER:
            dirPuerta = objetivo[1]
            if ((dirPuerta == "N" and dy < 0 and self.hy <= minY + 4) or
                    (dirPuerta == "S" and dy > 0 and self.hy >= maxY - 4) or
                    (dirPuerta == "O" and dx < 0 and self.hx <= minX + 4) or
                    (dirPuerta == "E" and dx > 0 and self.hx >= maxX - 4)):
                self._activar(Entrada("", ACC_MOVER, dirPuerta))

    def _objetivoCercano(self):
        """(accion, dato) del objeto o la puerta junto al heroe, o None."""
        if self.hx is None:
            return None
        sala = self.captura.sala
        suelo = self._suelo()
        lado = self._ladoHeroe()
        heroe = pygame.Rect(int(self.hx), int(self.hy), lado, lado).inflate(20, 20)
        base = ESCENARIO
        puertas = {"N": (base.centerx - 24, base.top),
                   "S": (base.centerx - 24, base.bottom - 48),
                   "E": (base.right - 48, base.centery - 24),
                   "O": (base.left, base.centery - 24)}
        for salida in sala.salidas:
            if salida.direccion in puertas:
                x, y = puertas[salida.direccion]
                if heroe.colliderect(pygame.Rect(x, y, 48, 48)):
                    return (ACC_ABRIR if salida.cerrada else ACC_MOVER, salida.direccion)
        for i in range(len(sala.suelo)):
            x, y = self._posicionSuelo(i, suelo)
            if heroe.colliderect(pygame.Rect(x, y, 32, 32)):
                return (ACC_RECOGER, sala.suelo[i].indice)
        return None
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
        lado = LADO_BASE * escala
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
        self._capturar(tipo in (ACC_ABRIR, ACC_RETROCESO))
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
                    self.controlador.procesar("ir a %d" % destId)
                    self._refrescarCaptura()
                    self.flotantes.append(["Viaje a Sala %d" % destId, ANCHO - 260, 160, 1.0])
            elif entrada.dato == "abrir_ayuda":
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
        if self.escena == "titulo":
            self.transicion = 0.4
            self.escena = "portada"
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
        if tecla in (pygame.K_h, pygame.K_F1):
            self.mostrarAyuda = not self.mostrarAyuda
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

    def _dibujarPortada(self):
        self._lienzo((14, 14, 24))
        ticks = pygame.time.get_ticks()

        # Antorchas en columnas laterales con halos de luz dinámica
        for escala, x, y in ((5, 50, 90), (5, 850, 90)):
            lado = LADO_BASE * escala
            pulso = 0.70 + 0.30 * math.sin(ticks / 220.0 + x)
            capa = self._halo(320).copy()
            capa.set_alpha(int(255 * pulso))
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
                   "MAZMORRA DE EVENTOS DISCRETOS · 3D RENDER EDITION", 18, CIAN,
                   centrado=True, sombra=TINTA)

        # Marco del diorama central estilo portada retro / Pokémon
        areaDiorama = pygame.Rect(100, 195, 780, 280)
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.40), areaDiorama, border_radius=14)
        pygame.draw.rect(self.pantalla, AGUA_CLARA, areaDiorama, 2, border_radius=14)

        # Plataforma 1 (Izquierda): El Explorador / Héroe
        platHeroe = pygame.Rect(140, 395, 190, 50)
        pygame.draw.ellipse(self.pantalla, (24, 30, 52), platHeroe)
        pygame.draw.ellipse(self.pantalla, BORDE_ACERO, platHeroe, 2)
        idleHeroe = int(2.5 * math.sin(ticks / 280.0))
        self._dibujarSombra(195, 335 + idleHeroe, LADO_BASE * 5)
        self.blitear("heroe", 195, 335 + idleHeroe, 5)
        self.texto(235, 452, "EL EXPLORADOR", 16, PERLA, centrado=True, sombra=TINTA)

        # Plataforma 2 (Centro): Pedestal de la Llave Sagrada
        platLlave = pygame.Rect(ANCHO // 2 - 95, 405, 190, 50)
        pygame.draw.ellipse(self.pantalla, (32, 38, 64), platLlave)
        pygame.draw.ellipse(self.pantalla, DORADO_OSCURO, platLlave, 2)

        haloLlave = self._halo(220).copy()
        haloLlave.set_alpha(int(140 + 60 * math.sin(ticks / 240.0)))
        self.pantalla.blit(haloLlave, (ANCHO // 2 - 110, 280 - 110))

        # Llave flotante con oscilación sinusoidal
        floatLlave = int(8.0 * math.sin(ticks / 250.0))
        yLlave = 280 + floatLlave
        self.blitear("llave", ANCHO // 2 - 40, yLlave, 5)

        # Destellos mágicos alrededor de la llave
        for ang, dist in ((0.2, 54), (1.8, 60), (3.4, 48), (4.9, 56)):
            fase = ticks / 300.0 + ang
            brillo = max(0.0, math.sin(fase))
            if brillo > 0.4:
                sx = int(ANCHO // 2 + dist * math.cos(fase * 0.8))
                sy = int(yLlave + 40 + dist * 0.5 * math.sin(fase * 0.8))
                pygame.draw.circle(self.pantalla, CREMA, (sx, sy), 3)
                pygame.draw.circle(self.pantalla, DORADO, (sx, sy), 5, 1)

        self.texto(ANCHO // 2, 456, "LA LLAVE DE SALIDA", 17, DORADO, centrado=True, sombra=TINTA)

        # Plataforma 3 (Derecha): Monstruos de la Mazmorra (Esqueleto + Murciélago)
        platMonstruos = pygame.Rect(650, 395, 200, 50)
        pygame.draw.ellipse(self.pantalla, (28, 24, 44), platMonstruos)
        pygame.draw.ellipse(self.pantalla, (120, 60, 70), platMonstruos, 2)
        idleEsqueleto = int(2.5 * math.sin(ticks / 290.0 + 1.2))
        self._dibujarSombra(680, 335 + idleEsqueleto, LADO_BASE * 5)
        self.blitear("esqueleto", 680, 335 + idleEsqueleto, 5)

        # Murciélago acechando arriba a la derecha con aleteo/flotación
        hoverMurcielago = int(5.0 * math.sin(ticks / 190.0 + 2.0))
        self.blitear("murcielago", 770, 260 + hoverMurcielago, 4)
        self.texto(750, 452, "GUARDIANES Y CAZADORES", 16, ROJO, centrado=True, sombra=TINTA)

        # Banner interactivo pulsante estilo arcade "PRESS START"
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

        self.texto(ANCHO // 2, 38, "CRIPTA", 44, DORADO, centrado=True, sombra=TINTA)
        self.texto(ANCHO // 2, 74, "SELECCIÓN DE EXPEDICIÓN", 18, CIAN, centrado=True, sombra=TINTA)

        # Botón volver a portada
        btnVolver = pygame.Rect(28, 28, 170, 36)
        hoverVolver = btnVolver.collidepoint(self.posRaton)
        self.caja(btnVolver, relleno=_aclara(PANEL, 0.2) if hoverVolver else PANEL,
                  borde=BLANCO if hoverVolver else BORDE_ACERO, radio=8)
        self.texto(btnVolver.centerx, btnVolver.centery, "[X / ESC] PORTADA", 16,
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
                    difTexto, difTono = "★☆☆ FÁCIL", VERDE
                elif i == 1:
                    difTexto, difTono = "★★☆ MEDIA", DORADO
                else:
                    difTexto, difTono = "★★★ DIFÍCIL", ROJO
            else:
                salasCount = parametros.get("salas", "?")
                difRaw = str(parametros.get("dificultad", "media")).lower()
                detalle = "%s salas" % salasCount
                if "facil" in difRaw or "fácil" in difRaw:
                    difTexto, difTono = "★☆☆ FÁCIL", VERDE
                elif "alta" in difRaw or "dificil" in difRaw or "difícil" in difRaw:
                    difTexto, difTono = "★★★ DIFÍCIL", ROJO
                else:
                    difTexto, difTono = "★★☆ MEDIA", DORADO

            self.texto(rect.x + 36, rect.y + 42, detalle, 16, ACERO)
            self._chip((rect.right - 60, rect.centery), difTexto, difTono)
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
            ("•", "Explora la cripta y sortea las trampas ocultas."),
            ("•", "Los cazadores persiguen por la ruta de menor costo."),
            ("•", "Encuentra la Llave y llega a la Salida con vida."),
            ("•", "Usa la Bolsa [I] y el Retroceso ante el peligro.")
        )
        for idx, (vineta, textoPauta) in enumerate(pautas):
            self.texto(cajaMision.x + 20, cajaMision.y + 38 + idx * 26, vineta, 18, DORADO)
            self.texto(cajaMision.x + 36, cajaMision.y + 38 + idx * 26, textoPauta, 15, PERLA)

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
            ("Z / ENTER", "confirmar / interactuar"),
            ("X / ESC",   "cancelar / retroceder / salir"),
            ("I / M",     "abrir bolsa / ver mapa"),
            ("WASD / ◄►", "moverse y navegar menús"),
        )
        for idx, (tClave, descClave) in enumerate(controles):
            px = cajaTeclas.x + 18 + (idx % 2) * 190
            py = arriba + 10 + (idx // 2) * 26
            self._chip((px + 36, py + 8), tClave, DORADO)
            self.texto(px + 82, py + 2, descClave, 14, ACERO)

        # Pie
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
        self._dibujarFlotantes()
        if self.mostrarAyuda:
            self._dibujarAyudaModal()
        self._dibujarTransicion()

    def _dibujarAyudaModal(self):
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((6, 6, 14, 180))
        self.pantalla.blit(capa, (0, 0))
        panel = pygame.Rect(210, 140, 560, 380)
        self.caja(panel, relleno=PANEL_CLARO, borde=DORADO)
        arriba = self._encabezado(panel, "guia rapida de controles", derecha="[H / F1]")
        filas = (
            ("FLECHAS / WASD", "Mover cursor o caminar en modo libre"),
            ("Z / ENTER / ESPACIO", "Confirmar accion o interactuar"),
            ("X / ESC", "Volver atras o abrir menu de sistema"),
            ("I", "Abrir o cerrar la bolsa de objetos"),
            ("C", "Activar / desactivar modo caminar en sala"),
            ("TAB", "Ver historial completo de eventos"),
            ("1 - 4", "Atacar directamente al enemigo en combate"),
        )
        y = arriba + 12
        for teclaStr, descStr in filas:
            self._chip((panel.x + 100, y + 8), teclaStr, DORADO)
            self.texto(panel.x + 210, y + 1, descStr, 15, PERLA)
            y += 36
        self.texto(panel.centerx, panel.bottom - 26, "PULSA CUALQUIER TECLA O CLIC PARA CERRAR",
                   14, ACERO, centrado=True)

    def _dibujarSala(self):
        sala = self.captura.sala
        temblor = self._sacudir()
        base = ESCENARIO.move(temblor)
        self.pantalla.blit(self._escenario(ESCENARIO.width, ESCENARIO.height),
                           (base.x - MARGEN, base.y - MARGEN))
        suelo = base.inflate(-2 * MURO, -2 * MURO)
        self._dibujarSalidas(base, sala)
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
            esCazador = getattr(enemigo, "comportamiento", "") == "cazador"
            tagCaz = " [CAZ]" if esCazador else ""
            etiquetaTexto = "%d) %s%s" % (i + 1, "" if salaLlena else enemigo.nombre.upper(), tagCaz)
            self.texto(etiqueta.x + 2, etiqueta.y,
                       _recortar(self.fuente(17), etiquetaTexto, etiqueta.width - 4), 17,
                       ROJO if esCazador else (BLANCO if enemigo.activo else APAGADO), sombra=TINTA)
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
            costoTexto = " (%d)" % salida.costo if salida.costo != 100 else ""
            autoTexto = " [AUTO %d]" % salida.cierreAutomatico if getattr(salida, "cierreAutomatico", None) is not None else ""
            chipRect = self._chip(pasado, "%s %s%s%s" % (salida.direccion, texto, costoTexto, autoTexto), tono,
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
                x = base.x + 40 + (i % 4) * 140
                y = base.y + 26 + (i // 4) * 74
            else:
                x, y = posiciones[i % 4]
            rect = self._dibujarActor(enemigo.sprite, x, y, escala, self._alpha(enemigo.etiqueta),
                                      enemigo.etiqueta)
            self.registrar(enemigo.etiqueta, rect)
            etiqueta = pygame.Rect(x - 30, max(base.y + 6, y - 30), 96 if compacto else 150, 26)
            esCazador = getattr(enemigo, "comportamiento", "") == "cazador"
            tagCaz = " [CAZ]" if compacto else (" [CAZADOR]" if esCazador else "")
            nombreTexto = ("%d)" % (i + 1) if compacto else "%d) %s" % (i + 1, enemigo.nombre.upper()))
            if esCazador:
                nombreTexto += tagCaz
            self.texto(etiqueta.x + 6, etiqueta.y + 3,
                       nombreTexto,
                       18, ROJO if esCazador else BLANCO, sombra=TINTA)
            self.barraVida(pygame.Rect(x - 30, y + 42 if compacto else y + 64,
                                       96 if compacto else 150, 20 if compacto else 24),
                           self._valorMostrado(enemigo.etiqueta, enemigo.vida),
                           enemigo.vidaMax, "", True)
            areaEnemigo = rect.inflate(14, 22)
            hover = areaEnemigo.collidepoint(self.posRaton)
            if i < 4:
                hkRect = pygame.Rect(rect.centerx - 14, max(base.y + 4, rect.top - 18), 28, 16)
                pygame.draw.rect(self.pantalla, TINTA, hkRect, border_radius=4)
                pygame.draw.rect(self.pantalla, ROJO if hover else BORDE_ACERO, hkRect, 1, border_radius=4)
                self.texto(hkRect.centerx, hkRect.centery, "[%d]" % (i + 1), 13,
                           AMARILLO if hover else BLANCO, centrado=True)
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
        columnas = 2 if total <= 4 else 4
        paso = (suelo.width - 60) // columnas
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
        self._listaEntradas(CAJA_MENU, entradas, cursor, arriba, 24,
                            "x vuelve" if self.submenu is not None else "i bolsa  esc menu")

    def _listaEntradas(self, caja, entradas, cursor, arriba, alto, pie=None):
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
        botonVolver = pygame.Rect(panel.centerx - 130, panel.bottom - 42, 260, 30)
        hoverVolver = botonVolver.collidepoint(self.posRaton)
        self.caja(botonVolver, relleno=_mezclar(PANEL, tono, 0.3 if hoverVolver else 0.15),
                  borde=tono if hoverVolver else DORADO_OSCURO, radio=6)
        self.texto(botonVolver.centerx, botonVolver.y + 5, "VOLVER AL MENÚ [Z]", 16,
                   BLANCO if hoverVolver else PERLA, centrado=True)
        self.zona(botonVolver, UI_SERVICIO, "ir_portada")

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

class VistaGraficaFinal(VistaGrafica):
    """Version final en una sola clase: sprites 3D suaves con volumen e iluminacion ambiental,
    paneles con degradado, barras con dano retardado, menus animados, caminata con movimiento
    de piernas y animacion de apertura de puertas/candados con llave."""

    # --- opciones ---
    # --- opciones ---
    SUAVIZAR = False
    SUAVIDAD = 6
    LADO_MAESTRO = 256
    VELOCIDAD_CAMINAR = 210.0
    FACTOR_ACTOR = 0.85  # Tamaño mediano para el héroe y monstruos (antes 0.65 era muy chico)
    FACTOR_OBJETO = 0.72  # Tamaño mediano para los objetos en el suelo (llaves, dagas, etc.)
    ACTORES = ("heroe", "heroe_espaldas", "heroe_paso1", "heroe_paso2",
               "rata", "esqueleto", "murcielago")
    OBJETOS = ("daga", "pocion", "antidoto", "llave", "antorcha",
               "pergamino", "armadura", "trampa")
    COLOR_RETARDO = (250, 236, 170)
    SPRITES_CON_VOLUMEN = ("heroe", "heroe_espaldas", "heroe_paso1", "heroe_paso2",
                           "rata", "esqueleto", "murcielago")
    TONO_EFECTO = {"veneno": MORADO, "antidoto": VERDE, "antorcha": AMARILLO,
                   "fuego": ROJO, "regeneracion": VERDE, "pocion": VERDE}
    TECLAS_MOVER = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                    pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pulso = [None, 0.0]
        self.menuTiempo = 0.0
        self.menuClave = None
        self.escenaTiempo = 0.0
        self.escenaVista = None
        self.chispas = []
        self.destello = 0.0
        self._retardoActual = None
        self._maestros = {}
        self.modoCaminar = True  # Caminar activo por defecto para moverse libremente por las salas
        self.hx = None
        self.hy = None
        self.mira = 1
        self.moviendo = False
        self.fasePaso = 0.0
        self._salaCaminar = None
        self._espejar = False
        # Animación al abrir puertas/candados: [direccion, tiempoRestante, duracionTotal, conLlave]
        self.animacionPuerta = None

    # ------------------------------------------------------------------ sprites 3D suaves
    def iniciar(self):
        super().iniciar()
        for entrada in self.hojas:
            nombre, escala = entrada[0], entrada[1]
            try:
                if self.SUAVIZAR:
                    nueva = self._suavizar(nombre, escala)
                elif nombre in self.SPRITES_CON_VOLUMEN and escala >= 2:
                    nueva = self._darVolumen(entrada[2], escala)
                else:
                    continue
            except Exception:
                continue
            entrada[2] = nueva
            self._hojasMap[(nombre, escala)] = nueva

    def _darVolumen(self, original, escala):
        """Volumen simple sobre el sprite pixelado (solo si SUAVIZAR es False)."""
        sprite = original.convert_alpha()
        ancho, alto = sprite.get_size()
        silueta = pygame.mask.from_surface(sprite, 127)
        contorno = pygame.mask.from_threshold(sprite, sprites.CONTORNO + (255,), (1, 1, 1, 255))
        interior = silueta.copy()
        interior.erase(contorno, (0, 0))
        grosor = max(1, escala // 2)
        corrida = pygame.mask.Mask((ancho, alto))
        corrida.draw(interior, (grosor, grosor))
        luzMascara = interior.copy()
        luzMascara.erase(corrida, (0, 0))
        luz = luzMascara.to_surface(setcolor=(255, 255, 255, 70), unsetcolor=(0, 0, 0, 0))
        corrida = pygame.mask.Mask((ancho, alto))
        corrida.draw(interior, (-grosor, -grosor))
        sombraMascara = interior.copy()
        sombraMascara.erase(corrida, (0, 0))
        sombra = sombraMascara.to_surface(setcolor=(0, 0, 30, 110), unsetcolor=(0, 0, 0, 0))
        degradado = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        for fila in range(alto):
            alfa = int(64 * fila / float(max(1, alto - 1)))
            pygame.draw.line(degradado, (0, 0, 20, alfa), (0, fila), (ancho, fila))
        relleno = interior.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        degradado.blit(relleno, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        resultado = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        resultado.blit(sprite, (0, 0))
        resultado.blit(degradado, (0, 0))
        resultado.blit(sombra, (0, 0))
        resultado.blit(luz, (0, 0))
        return resultado

    def _suavizar(self, nombre, escala):
        lado = LADO_BASE * escala
        reducida = pygame.transform.smoothscale(self._maestro(nombre), (lado, lado))
        return reducida.convert_alpha()

    def _maestro(self, nombre):
        """Renderizado estilo modelo 3D suave: silueta antialiaseada sin contorno negro,
        volumen esférico por capas, oclusión ambiental inferior y luz especular."""
        maestro = self._maestros.get(nombre)
        if maestro is not None:
            return maestro
        medida = sprites.MEDIDA
        N = self.LADO_MAESTRO
        paso = max(1, N // 48)

        celdas = sprites._celdas(sprites.buscarSprite(nombre), nombre)
        base = pygame.Surface((medida, medida), pygame.SRCALPHA)
        for y in range(medida):
            for x in range(medida):
                tono = celdas[y][x]
                if tono is not None:
                    base.set_at((x, y), (tono[0], tono[1], tono[2], 255))
                else:
                    vecino = (80, 70, 90)
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < medida and 0 <= ny < medida and celdas[ny][nx] is not None:
                            vecino = celdas[ny][nx]
                            break
                    base.set_at((x, y), (vecino[0], vecino[1], vecino[2], 0))

        grande = pygame.transform.smoothscale(base, (N, N))
        chico = pygame.transform.smoothscale(grande, (N // self.SUAVIDAD, N // self.SUAVIDAD))
        suave = pygame.transform.smoothscale(chico, (N, N))

        mascaraDura = pygame.mask.from_surface(suave, 118)
        mascaraBorde = pygame.mask.from_surface(suave, 95)

        forma = pygame.Surface((N, N), pygame.SRCALPHA)
        forma.blit(suave, (0, 0))
        nucleoAlpha = mascaraDura.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        bordeAlpha = mascaraBorde.to_surface(setcolor=(255, 255, 255, 140), unsetcolor=(0, 0, 0, 0))
        alphaFinal = bordeAlpha.copy()
        alphaFinal.blit(nucleoAlpha, (0, 0))
        forma.blit(alphaFinal, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        relleno = nucleoAlpha

        luz = pygame.Surface((N, N), pygame.SRCALPHA)
        sombra = pygame.Surface((N, N), pygame.SRCALPHA)
        for k in range(1, 10):
            d = k * paso
            corrida = pygame.mask.Mask((N, N))
            corrida.draw(mascaraDura, (d, d))
            banda = mascaraDura.copy()
            banda.erase(corrida, (0, 0))
            alfaLuz = max(3, 18 - k * 2)
            luz.blit(banda.to_surface(setcolor=(255, 248, 235, alfaLuz), unsetcolor=(0, 0, 0, 0)),
                     (0, 0))

            corrida = pygame.mask.Mask((N, N))
            corrida.draw(mascaraDura, (-d, -d))
            banda = mascaraDura.copy()
            banda.erase(corrida, (0, 0))
            alfaSombra = max(4, 24 - k * 2)
            sombra.blit(banda.to_surface(setcolor=(18, 12, 36, alfaSombra), unsetcolor=(0, 0, 0, 0)),
                        (0, 0))

        degradado = pygame.Surface((N, N), pygame.SRCALPHA)
        for fila in range(N):
            t = fila / float(N - 1)
            if t < 0.45:
                alfa = int(28 * (1.0 - t / 0.45))
                pygame.draw.line(degradado, (255, 252, 245, alfa), (0, fila), (N, fila))
            else:
                alfa = int(68 * ((t - 0.45) / 0.55))
                pygame.draw.line(degradado, (16, 12, 34, alfa), (0, fila), (N, fila))
        degradado.blit(relleno, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        brillo = pygame.Surface((N, N), pygame.SRCALPHA)
        cx, cy = int(N * 0.38), int(N * 0.28)
        for i in range(12):
            f = (12 - i) / 12.0
            rx, ry = int(N * 0.34 * f), int(N * 0.26 * f)
            pygame.draw.ellipse(brillo, (255, 255, 255, 3 + int(36 * (1.0 - f))),
                                pygame.Rect(cx - rx, cy - ry, 2 * rx, 2 * ry))
        brillo.blit(relleno, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        rimCorrida = pygame.mask.Mask((N, N))
        rimCorrida.draw(mascaraDura, (-paso * 2, -paso * 2))
        rimBanda = mascaraDura.copy()
        rimBanda.erase(rimCorrida, (0, 0))
        rim = rimBanda.to_surface(setcolor=(180, 215, 255, 38), unsetcolor=(0, 0, 0, 0))

        forma.blit(degradado, (0, 0))
        forma.blit(sombra, (0, 0))
        forma.blit(luz, (0, 0))
        forma.blit(rim, (0, 0))
        forma.blit(brillo, (0, 0))
        self._maestros[nombre] = forma
        return forma

    def hoja(self, nombre, escala=3):
        superficie = super().hoja(nombre, escala)
        if superficie is not None:
            factor = None
            if nombre in self.ACTORES and escala >= 3:
                factor = self.FACTOR_ACTOR
            elif nombre in self.OBJETOS and escala >= 2:
                factor = self.FACTOR_OBJETO

            if factor is not None:
                lado = max(20, int(LADO_BASE * escala * factor))
                if superficie.get_size() != (lado, lado):
                    claveEsc = ("spriteMed", nombre, lado)
                    escSurf = self.luces.get(claveEsc)
                    if escSurf is None:
                        escSurf = pygame.transform.scale(superficie, (lado, lado))
                        self._guardar(self.luces, claveEsc, escSurf)
                    superficie = escSurf

        if self._espejar and superficie is not None:
            clave = ("espejo", nombre, escala, id(superficie))
            espejo = self.luces.get(clave)
            if espejo is None:
                espejo = pygame.transform.flip(superficie, True, False)
                self._guardar(self.luces, clave, espejo)
            return espejo
        return superficie

    def _destelloActivo(self, clave):
        for entrada in self.parpadeos:
            if entrada[0] == clave and entrada[1] > 0.36:
                return True
        return False

    def _hojaBlanca(self, nombre, escala):
        """Copia aclarada del sprite: se muestra el primer instante de un golpe."""
        clave = ("blancaE" if self._espejar else "blanca", nombre, escala)
        capa = self.luces.get(clave)
        if capa is None:
            capa = self.hoja(nombre, escala).copy()
            capa.fill((200, 200, 200, 0), special_flags=pygame.BLEND_RGB_ADD)
            self._guardar(self.luces, clave, capa)
        return capa

    def blitear(self, nombre, x, y, escala=3, alpha=255, clave=None):
        esHeroeJugador = (clave == "jugador" and nombre in ("heroe", "heroe_paso1", "heroe_paso2"))
        self._espejar = (esHeroeJugador and self.mira < 0 and self._activoCaminar())
        try:
            superficie = self.hoja(nombre, escala)
            if (clave is not None and self._destelloActivo(clave)
                    and superficie.get_flags() & pygame.SRCALPHA):
                superficie = self._hojaBlanca(nombre, escala)

            ladoBase = LADO_BASE * escala
            ladoReal = superficie.get_width()
            dx = dy = 0
            if clave is not None:
                dx, dy = self.desplazamiento(clave)

            # Si el objeto del suelo fue reducido, centrarlo en su espacio original
            offset = (ladoBase - ladoReal) // 2 if (nombre in self.OBJETOS and escala >= 2) else 0
            rect = pygame.Rect(int(x + dx + offset), int(y + dy + offset), ladoReal, ladoReal)

            if alpha < 255:
                copia = superficie.copy()
                copia.set_alpha(alpha)
                self.pantalla.blit(copia, rect)
            else:
                self.pantalla.blit(superficie, rect)
            return rect
        finally:
            self._espejar = False

    # ------------------------------------------------------------------ texto y paneles
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
            borde.set_alpha(110)
            self.pantalla.blit(borde, rect.move(1, 3))
            borde.set_alpha(255)
            self.pantalla.blit(borde, rect.move(2, 2))
        self.pantalla.blit(superficie, rect)
        return rect

    def caja(self, rect, relleno=PANEL, borde=BORDE_ACERO, grosor=3, radio=10):
        relleno = tuple(c // 4 * 4 for c in relleno)
        borde = tuple(c // 4 * 4 for c in borde)
        self.pantalla.blit(self._sombraCaja(rect.width, rect.height, radio),
                           (rect.x - 6, rect.y - 3))
        clave = (rect.width, rect.height, relleno, borde, grosor, radio)
        cara = self.cajas.get(clave)
        if cara is None:
            cara = self._construirCaja(*clave)
            self._guardar(self.cajas, clave, cara)
        self.pantalla.blit(cara, rect.topleft)
        return rect

    def _sombraCaja(self, ancho, alto, radio):
        clave = ("sombraCaja", ancho, alto, radio)
        capa = self.sombras.get(clave)
        if capa is not None:
            return capa
        capa = pygame.Surface((ancho + 16, alto + 16), pygame.SRCALPHA)
        for i in range(6):
            grosorCapa = 6 - i
            hueco = pygame.Rect(8, 8, ancho, alto).inflate(2 * grosorCapa, 2 * grosorCapa)
            pygame.draw.rect(capa, (0, 0, 0, 10 + i * 9), hueco, border_radius=radio + grosorCapa)
        return self._guardar(self.sombras, clave, capa)

    def _construirCaja(self, ancho, alto, relleno, borde, grosor, radio):
        radio = max(0, min(radio, ancho // 2, alto // 2))
        cara = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        cuerpo = cara.get_rect()
        degradado = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        for fila in range(alto):
            factor = fila / float(max(1, alto - 1))
            tono = _mezclar(_aclara(relleno, 0.10), _oscurece(relleno, 0.22), factor)
            if fila % 3 == 0:
                tono = _oscurece(tono, 0.06)
            pygame.draw.line(degradado, tono, (0, fila), (ancho, fila))
        mascara = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), cuerpo, border_radius=radio)
        degradado.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        cara.blit(degradado, (0, 0))
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

    def _franja(self, ancho):
        clave = ("franja", ancho)
        capa = self.luces.get(clave)
        if capa is None:
            capa = pygame.Surface((ancho, 22), pygame.SRCALPHA)
            pygame.draw.rect(capa, (4, 6, 18, 110), capa.get_rect(), border_radius=6)
            pygame.draw.line(capa, (255, 255, 255, 14), (6, 1), (ancho - 7, 1))
            self._guardar(self.luces, clave, capa)
        return capa

    def _encabezado(self, rect, titulo, derecha=None):
        self.pantalla.blit(self._franja(rect.width - 12), (rect.x + 6, rect.y + 4))
        pygame.draw.polygon(self.pantalla, DORADO,
                            ((rect.x + 16, rect.y + 10), (rect.x + 21, rect.y + 15),
                             (rect.x + 16, rect.y + 20), (rect.x + 11, rect.y + 15)))
        self.texto(rect.x + 28, rect.y + 6, titulo.upper(), 16, DORADO, sombra=TINTA)
        if derecha is not None:
            self.texto(rect.right - 14, rect.y + 6, derecha, 16, CIAN, derecha=True, sombra=TINTA)
        y = rect.y + 27
        pygame.draw.line(self.pantalla, DORADO_OSCURO, (rect.x + 10, y), (rect.right - 11, y))
        pygame.draw.line(self.pantalla, _aclara(DORADO_OSCURO, 0.35), (rect.x + 10, y + 1),
                         (rect.right - 11, y + 1))
        return y + 5

    def _chip(self, centro, cadena, tono, limite=None):
        if "★" in cadena or "☆" in cadena:
            llenas = cadena.count("★")
            palabra = cadena.split(" ", 1)[1] if " " in cadena else cadena
            return self._chipEstrellas((centro[0] - 18, centro[1]), palabra, tono, llenas)
        return super()._chip(centro, cadena, tono, limite)

    def _estrella(self, cx, cy, radio, tono):
        puntos = []
        for k in range(10):
            angulo = -math.pi / 2.0 + k * math.pi / 5.0
            r = radio if k % 2 == 0 else radio * 0.45
            puntos.append((cx + r * math.cos(angulo), cy + r * math.sin(angulo)))
        pygame.draw.polygon(self.pantalla, tono, puntos)

    def _chipEstrellas(self, centro, palabra, tono, llenas):
        superficie = self.fuente(13).render(palabra, True, tono)
        fondo = pygame.Rect(0, 0, 3 * 14 + 6 + superficie.get_width() + 12,
                            superficie.get_height() + 5)
        fondo.center = centro
        pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.45), fondo, border_radius=5)
        pygame.draw.rect(self.pantalla, _mezclar(tono, PANEL, 0.30), fondo, 1, border_radius=5)
        x = fondo.x + 10
        for k in range(3):
            self._estrella(x + 6, fondo.centery, 6, tono if k < llenas else _oscurece(tono, 0.65))
            x += 14
        self.pantalla.blit(superficie, (x + 4, fondo.centery - superficie.get_height() // 2))
        return fondo

    # ------------------------------------------------------------------ barras de vida
    @staticmethod
    def _tonoVidaSuave(valor, maximo):
        if valor <= 0:
            return APAGADO
        ratio = _ratio(valor, maximo)
        if ratio > 0.5:
            return _mezclar(AMARILLO, VERDE, (ratio - 0.5) / 0.5)
        return _mezclar(ROJO, AMARILLO, ratio / 0.5)

    def _valorMostrado(self, clave, real):
        self._retardoActual = self._valorRetardo(clave, real)
        return super()._valorMostrado(clave, real)

    def _valorRetardo(self, clave, real):
        entrada = self._barra(clave)
        if entrada is None:
            return real
        return entrada[3]

    def barraVida(self, rect, valor, maximo, etiqueta="", compacta=False, retardo=None):
        if retardo is None:
            retardo = self._retardoActual
        self._retardoActual = None
        self.caja(rect, relleno=CREMA, borde=TINTA, grosor=3, radio=9)
        hueco = rect.inflate(-16, -16)
        if compacta:
            hueco = rect.inflate(-14, -12)
            hueco.bottom = rect.bottom - 5
        pygame.draw.rect(self.pantalla, _oscurece(CREMA, 0.34), hueco, border_radius=6)
        interior = hueco.width - 4
        ratio = _ratio(valor, maximo)
        if retardo is not None and retardo > valor:
            anchoRetardo = int(interior * _ratio(retardo, maximo))
            if anchoRetardo > 0:
                pygame.draw.rect(self.pantalla, self.COLOR_RETARDO,
                                 pygame.Rect(hueco.x + 2, hueco.y + 2, anchoRetardo,
                                             hueco.height - 4), border_radius=5)
        ancho = int(interior * ratio)
        if ancho > 0:
            tono = self._tonoVidaSuave(valor, maximo)
            if ratio <= 0.25:
                tono = _aclara(tono, 0.12 + 0.12 * math.sin(pygame.time.get_ticks() / 110.0))
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

    # ------------------------------------------------------------------ animacion, golpes y llaves
    def _sincronizarVidas(self):
        claves = [("jugador", self.captura.jugador.vida)]
        for enemigo in self.captura.sala.enemigos:
            claves.append((enemigo.etiqueta, enemigo.vida))
        for clave, valor in claves:
            entrada = self._barra(clave)
            if entrada is None:
                self.barras.append([clave, valor, valor, valor, 0.0])
                continue
            if valor < entrada[2]:
                self._golpe(clave, entrada[2] - valor)
                entrada[4] = 0.45
            elif valor > entrada[2]:
                self._curacion(clave, valor - entrada[2])
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
                self._chispar(entrada[1].centerx, entrada[1].centery,
                              ROJO if clave == "jugador" else AMARILLO)
                break
        if clave == "jugador":
            self.sacudida = 0.4
            self.destello = 0.30

    def _curacion(self, clave, cantidad):
        for entrada in self.posiciones:
            if entrada[0] == clave:
                self.flotantes.append(["+%d" % cantidad, entrada[1].centerx,
                                       max(34, entrada[1].top), 1.2])
                self._chispar(entrada[1].centerx, entrada[1].centery, VERDE)
                break

    def _chispar(self, x, y, tono, cantidad=10):
        for _ in range(cantidad):
            angulo = random.uniform(0.0, 2.0 * math.pi)
            rapidez = random.uniform(60.0, 160.0)
            self.chispas.append([float(x), float(y), math.cos(angulo) * rapidez,
                                 math.sin(angulo) * rapidez - 40.0, 0.45, tono])

    def _coordPuerta(self, direccion):
        base = ESCENARIO
        if direccion == "N":
            return (base.centerx, base.top + 20)
        if direccion == "S":
            return (base.centerx, base.bottom - 20)
        if direccion == "E":
            return (base.right - 20, base.centery)
        if direccion == "O":
            return (base.left + 20, base.centery)
        return base.center

    def _iniciarAnimacionPuerta(self, direccion, conLlave=True):
        """Dispara la cinematica de llave girando, destello y chispas en la puerta."""
        self.animacionPuerta = [direccion, 0.85, 0.85, conLlave]
        px, py = self._coordPuerta(direccion)
        self._chispar(px, py, DORADO, cantidad=16)
        self._chispar(px, py, CIAN, cantidad=8)

    def _enviar(self, tipo, dato=None, investidura=False):
        necesitaLlave = False
        if tipo == ACC_ABRIR and self.captura is not None:
            for s in self.captura.sala.salidas:
                if s.direccion == dato:
                    necesitaLlave = s.necesitaLlave
                    break
        super()._enviar(tipo, dato, investidura)
        if tipo == ACC_ABRIR and dato is not None:
            # Si la puerta efectivamente se abrió, lanzar la animación
            abierta = True
            if self.captura is not None:
                for s in self.captura.sala.salidas:
                    if s.direccion == dato and s.cerrada:
                        abierta = False
                        break
            if abierta:
                self._iniciarAnimacionPuerta(dato, necesitaLlave)

    def _avanzarAnimaciones(self, dt):
        for entrada in self.barras:
            diferencia = entrada[2] - entrada[1]
            if abs(diferencia) < 0.05:
                entrada[1] = entrada[2]
            else:
                entrada[1] += diferencia * min(1.0, dt * 9.0)
            if entrada[3] < entrada[1]:
                entrada[3] = entrada[1]
            if entrada[4] > 0:
                entrada[4] = max(0.0, entrada[4] - dt)
            elif entrada[3] > entrada[1]:
                velocidad = max(8.0, (entrada[3] - entrada[1]) * 2.5)
                entrada[3] = max(entrada[1], entrada[3] - velocidad * dt)
        self.sacudida = max(0.0, self.sacudida - dt)
        self.destello = max(0.0, self.destello - dt)
        self.menuTiempo += dt
        self.escenaTiempo += dt
        if self.pulso[1] > 0:
            self.pulso[1] = max(0.0, self.pulso[1] - dt)
        if self.animacionPuerta is not None:
            self.animacionPuerta[1] = max(0.0, self.animacionPuerta[1] - dt)
            if self.animacionPuerta[1] <= 0.0:
                self.animacionPuerta = None
        for i in range(len(self.parpadeos) - 1, -1, -1):
            self.parpadeos[i][1] -= dt
            if self.parpadeos[i][1] <= 0:
                del self.parpadeos[i]
        for i in range(len(self.flotantes) - 1, -1, -1):
            if len(self.flotantes[i]) < 5:
                self.flotantes[i].append(self.flotantes[i][3])
            self.flotantes[i][2] -= 26 * dt
            self.flotantes[i][3] -= dt
            if self.flotantes[i][3] <= 0:
                del self.flotantes[i]
        for i in range(len(self.chispas) - 1, -1, -1):
            chispa = self.chispas[i]
            chispa[0] += chispa[2] * dt
            chispa[1] += chispa[3] * dt
            chispa[3] += 320.0 * dt
            chispa[4] -= dt
            if chispa[4] <= 0:
                del self.chispas[i]
        if self.transicion > 0:
            self.transicion = max(0.0, self.transicion - dt * 2.0)
        if self.salto is not None:
            self.salto[1] = max(0.0, self.salto[1] - dt)
            if self.salto[1] <= 0:
                self.salto = None
        self._caminar(dt)

    def _capaGolpe(self):
        capa = self.luces.get("golpe")
        if capa is None:
            capa = pygame.Surface((ESCENARIO.width, ESCENARIO.height), pygame.SRCALPHA)
            capa.fill((200, 20, 20, 40))
            for g in range(1, 14):
                alfa = int(200 * (1.0 - g / 14.0))
                pygame.draw.rect(capa, (220, 20, 20, alfa),
                                 capa.get_rect().inflate(-g * 4, -g * 4), 4, border_radius=10)
            self._guardar(self.luces, "golpe", capa)
        return capa

    def _atenuar(self):
        capa = self.luces.get("oscuro")
        if capa is None:
            capa = pygame.Surface((ANCHO, ALTO))
            capa.fill((4, 4, 12))
            self._guardar(self.luces, "oscuro", capa)
        capa.set_alpha(int(150 * min(1.0, self.escenaTiempo / 0.2)))
        self.pantalla.blit(capa, (0, 0))

    def _dibujarAnimacionPuerta(self):
        """Dibuja la llave girando sobre la cerradura, el halo de luz y el destello de apertura."""
        if self.animacionPuerta is None or self.escena != "escenario":
            return
        direccion, restante, total, conLlave = self.animacionPuerta
        progreso = 1.0 - (restante / total)
        cx, cy = self._coordPuerta(direccion)

        # 1. Halo luminoso expansivo en la cerradura
        radioHalo = int(90 + 70 * math.sin(progreso * math.pi))
        halo = self._halo(max(32, radioHalo)).copy()
        halo.set_alpha(int(230 * (1.0 - progreso * 0.7)))
        self.pantalla.blit(halo, (cx - radioHalo // 2, cy - radioHalo // 2))

        # 2. Onda de choque circular dorada/cian al desbloquear
        radioOnda = int(14 + progreso * 46)
        grosorOnda = max(1, int(4 * (1.0 - progreso)))
        pygame.draw.circle(self.pantalla, DORADO if conLlave else CIAN,
                           (cx, cy), radioOnda, grosorOnda)

        # 3. Sprite de llave girando (rotación y escala dinámica)
        if conLlave:
            spriteLlave = self.hoja("llave", 3)
            # Fase 0 -> 0.55: la llave entra y gira 90 grados; Fase 0.55 -> 1.0: se eleva y desvanece
            if progreso < 0.55:
                t = progreso / 0.55
                angulo = -45.0 + 135.0 * t
                escalaDin = 0.85 + 0.35 * math.sin(t * math.pi)
                offsetY = int(-18 * (1.0 - t))
                alfa = 255
            else:
                t = (progreso - 0.55) / 0.45
                angulo = 90.0
                escalaDin = 1.0 + 0.25 * t
                offsetY = int(-26 * t)
                alfa = int(255 * (1.0 - t))

            rotada = pygame.transform.rotozoom(spriteLlave, angulo, escalaDin)
            rotada.set_alpha(max(0, min(255, alfa)))
            rRect = rotada.get_rect(center=(cx, cy + offsetY))
            self.pantalla.blit(rotada, rRect)

        # 4. Etiqueta flotante de estado
        if progreso < 0.85:
            etiqueta = "¡CANDADO ABIERTO!" if conLlave else "¡PUERTA ABIERTA!"
            yTexto = cy - 26 - int(16 * progreso)
            self.texto(cx, yTexto, etiqueta, 15, DORADO if conLlave else CIAN,
                       centrado=True, sombra=TINTA)

    def _dibujarFlotantes(self):
        self._dibujarAnimacionPuerta()
        if self.destello > 0:
            capa = self._capaGolpe()
            capa.set_alpha(int(255 * self.destello / 0.30))
            self.pantalla.blit(capa, ESCENARIO.topleft)
        for chispa in self.chispas:
            lado = 2 + int(4 * chispa[4] / 0.45)
            pygame.draw.rect(self.pantalla, chispa[5],
                             pygame.Rect(int(chispa[0]), int(chispa[1]), lado, lado))
        for entrada in self.flotantes:
            base = ROJO if entrada[0].startswith("-") else VERDE
            restante = entrada[3]
            edad = (entrada[4] - restante) if len(entrada) > 4 else 0.0
            pop = max(0.0, 1.0 - edad / 0.16)
            tam = 24 + int(10 * pop)
            factor = min(1.0, restante / 0.45)
            tono = _mezclar(_aclara(base, 0.55), base, min(1.0, edad / 0.25))
            tono = (int(tono[0] * factor), int(tono[1] * factor), int(tono[2] * factor))
            x = int(entrada[1])
            y = int(entrada[2])
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
                self.texto(x + dx, y + dy, entrada[0], tam, TINTA, centrado=True)
            self.texto(x, y, entrada[0], tam, tono, centrado=True)

    # ------------------------------------------------------------------ HUD del jugador
    def _triangulo(self, cx, cy, arriba, tono):
        if arriba:
            puntos = ((cx - 4, cy + 3), (cx + 4, cy + 3), (cx, cy - 4))
        else:
            puntos = ((cx - 4, cy - 3), (cx + 4, cy - 3), (cx, cy + 4))
        pygame.draw.polygon(self.pantalla, TINTA, [(px + 1, py + 1) for px, py in puntos])
        pygame.draw.polygon(self.pantalla, tono, puntos)

    def _atributoGrafico(self, x, y, etiqueta, valor, bono):
        rotulo = self.texto(x, y + 2, etiqueta, 14, ACERO, sombra=TINTA)
        tono = BLANCO if bono == 0 else (VERDE if bono > 0 else ROJO)
        cifra = self.texto(rotulo.right + 6, y - 1, "%d" % valor, 19, tono, sombra=TINTA)
        derecha = cifra.right
        if bono != 0:
            self._triangulo(derecha + 8, y + 10, bono > 0, tono)
            magnitud = self.texto(derecha + 15, y + 3, "%d" % abs(bono), 13, tono, sombra=TINTA)
            derecha = magnitud.right
        return derecha

    def _insigniaEfecto(self, x, y, nombre):
        tono = CIAN
        for clave, color in self.TONO_EFECTO.items():
            if clave in str(nombre).lower():
                tono = color
                break
        cuadro = pygame.Rect(x, y, 22, 20)
        pygame.draw.rect(self.pantalla, _oscurece(tono, 0.60), cuadro, border_radius=5)
        pygame.draw.rect(self.pantalla, tono, cuadro, 1, border_radius=5)
        self.texto(cuadro.centerx, cuadro.centery - 1, str(nombre)[:1].upper(), 14, tono,
                   centrado=True)
        return cuadro

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
        x = CAJA_JUGADOR.x + 72
        for etiqueta, valor, bono in (("ATR", jugador.ataque, jugador.bonoAtaque),
                                      ("DEF", jugador.defensa, jugador.bonoDefensa),
                                      ("VEL", jugador.velocidad, 0)):
            x = self._atributoGrafico(x, CAJA_JUGADOR.y + 44, etiqueta, valor, bono) + 14
        if len(jugador.efectos) > 0:
            capacidad = max(0, (CAJA_JUGADOR.right - 20 - x) // 26)
            visibles = jugador.efectos if len(jugador.efectos) <= capacidad \
                else jugador.efectos[:max(0, capacidad - 1)]
            for efecto in visibles:
                cuadro = self._insigniaEfecto(x, CAJA_JUGADOR.y + 43, efecto)
                if cuadro.collidepoint(self.posRaton):
                    self._chip((cuadro.centerx, cuadro.bottom + 14), str(efecto).upper(), VERDE)
                x += 26
            if len(visibles) < len(jugador.efectos):
                self.texto(x, CAJA_JUGADOR.y + 46, "+%d" % (len(jugador.efectos) - len(visibles)),
                           14, VERDE, sombra=TINTA)

    # ------------------------------------------------------------------ menus
    def _entradasSubmenu(self):
        entradas = super()._entradasSubmenu()
        if self.submenu == "objetivo":
            for entrada, enemigo in zip(entradas, self.captura.sala.enemigos):
                entrada.ratio = _ratio(enemigo.vida, enemigo.vidaMax)
        return entradas

    def _dibujarMenu(self):
        clave = (self.submenu, self.combate)
        if clave != self.menuClave:
            self.menuClave = clave
            self.menuTiempo = 0.0
        super()._dibujarMenu()

    def _icono(self, cuadro, entrada, tono):
        cx, cy = cuadro.center
        color = _aclara(tono, 0.35)
        clave = entrada.dato if entrada.accion in (UI_IR, UI_SUBMENU, UI_SERVICIO) \
            else entrada.accion
        if clave == ACC_ATACAR or clave == "objetivo":
            pygame.draw.line(self.pantalla, color, (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
            pygame.draw.line(self.pantalla, color, (cx - 4, cy + 4), (cx + 4, cy - 4), 2)
        elif clave == ACC_ESPERAR:
            pygame.draw.polygon(self.pantalla, color, ((cx - 4, cy - 4), (cx + 4, cy - 4), (cx, cy)))
            pygame.draw.polygon(self.pantalla, color, ((cx - 4, cy + 4), (cx + 4, cy + 4), (cx, cy)))
        elif clave == ACC_MOVER or clave == "mover":
            pygame.draw.polygon(self.pantalla, color, ((cx - 4, cy - 4), (cx + 4, cy), (cx - 4, cy + 4)))
        elif clave == ACC_RETROCESO:
            pygame.draw.polygon(self.pantalla, color, ((cx + 4, cy - 4), (cx - 4, cy), (cx + 4, cy + 4)))
        elif clave == ACC_RECOGER or clave == "suelo" or clave == ACC_SOLTAR:
            pygame.draw.polygon(self.pantalla, color, ((cx - 4, cy - 4), (cx + 4, cy - 4), (cx, cy + 2)))
            pygame.draw.line(self.pantalla, color, (cx - 4, cy + 4), (cx + 4, cy + 4), 2)
        elif clave == ACC_ABRIR or clave == "abrir":
            pygame.draw.circle(self.pantalla, color, (cx - 2, cy), 3, 1)
            pygame.draw.line(self.pantalla, color, (cx + 1, cy), (cx + 5, cy), 2)
        elif clave == "bolsa":
            pygame.draw.rect(self.pantalla, color, pygame.Rect(cx - 4, cy - 2, 8, 7), 1)
            pygame.draw.line(self.pantalla, color, (cx - 2, cy - 4), (cx + 2, cy - 4), 1)
        elif clave == ACC_USAR:
            pygame.draw.line(self.pantalla, color, (cx - 4, cy), (cx + 4, cy), 2)
            pygame.draw.line(self.pantalla, color, (cx, cy - 4), (cx, cy + 4), 2)
        else:
            pygame.draw.rect(self.pantalla, color, pygame.Rect(cx - 2, cy - 2, 4, 4))

    def _listaEntradas(self, caja, entradas, cursor, arriba, alto, pie=None):
        huecos = max(1, (caja.bottom - (24 if pie else 8) - arriba) // alto)
        inicio = min(max(0, cursor - huecos + 1), max(0, len(entradas) - huecos))
        fondo = min(len(entradas), inicio + huecos)
        fuente = self.fuente(17)
        recorte = self.pantalla.get_clip()
        self.pantalla.set_clip(caja.inflate(-2, -2))
        for i in range(inicio, fondo):
            entrada = entradas[i]
            rect = pygame.Rect(caja.x + 18, arriba + (i - inicio) * alto, caja.width - 36, alto - 3)
            retraso = (i - inicio) * 0.045
            progreso = max(0.0, min(1.0, (self.menuTiempo - retraso) / 0.2))
            desplazo = int(((1.0 - progreso) ** 2) * 48)
            fila = rect.move(desplazo, 0)
            acento = _tonoEntrada(entrada)
            esHover = rect.collidepoint(self.posRaton)
            presionada = self.pulso[1] > 0 and (
                (self.pulso[0] is None and i == cursor) or
                (self.pulso[0] is not None and self.pulso[0] == rect))
            if presionada:
                fila = fila.move(0, 1)
            if i == cursor:
                self._resaltar(fila, _oscurece(SELECCION, 0.25) if presionada else SELECCION)
                self.flecha(fila)
            elif esHover and entrada.habilitada:
                pygame.draw.rect(self.pantalla, _mezclar(PANEL_CLARO, acento, 0.22), fila,
                                 border_radius=6)
                pygame.draw.rect(self.pantalla, _mezclar(BORDE_ACERO, acento, 0.5), fila, 1,
                                 border_radius=6)
            if entrada.habilitada:
                cuadro = self._tecla(fila, acento)
                self._icono(cuadro, entrada, acento)
            centro = fila.y + max(2, (fila.height - fuente.get_linesize()) // 2)
            etiqueta = self.texto(fila.x + 30, centro, entrada.texto.upper(), 17,
                                  BLANCO if (i == cursor or esHover) and entrada.habilitada
                                  else (PERLA if entrada.habilitada else APAGADO),
                                  sombra=TINTA if entrada.habilitada else None)
            if len(entrada.marca) > 0 and fila.right - 8 - etiqueta.right > 12:
                texto = _recortar(self.fuente(13), entrada.marca.upper(),
                                  fila.right - 8 - etiqueta.right - 10)
                self.texto(fila.right - 8, centro + 2, texto, 13,
                           DORADO if entrada.habilitada else APAGADO, derecha=True)
            ratio = getattr(entrada, "ratio", None)
            if ratio is not None:
                pista = pygame.Rect(fila.x + 30, fila.bottom - 3, fila.width - 38, 2)
                pygame.draw.rect(self.pantalla, _oscurece(PANEL, 0.5), pista)
                llena = pygame.Rect(pista.x, pista.y, int(pista.width * ratio), 2)
                if llena.width > 0:
                    pygame.draw.rect(self.pantalla, self._tonoVidaSuave(ratio, 1.0), llena)
            self.zona(rect, entrada.accion, entrada.dato, entrada.habilitada)
        self.pantalla.set_clip(recorte)
        if len(entradas) == 0:
            self.texto(caja.x + 18, arriba, "nada disponible", 17, APAGADO)
        if pie is not None:
            self.texto(caja.x + 18, caja.bottom - 24, pie, 14, ACERO)
        if len(entradas) > huecos:
            self.texto(caja.right - 14, caja.bottom - 24,
                       "%d/%d" % (min(cursor + 1, len(entradas)), len(entradas)), 14, ACERO,
                       derecha=True)

    # ------------------------------------------------------------------ modo caminar con piernas
    def _activoCaminar(self):
        return self.modoCaminar and self.captura is not None and not self.combate

    def _suelo(self):
        return ESCENARIO.inflate(-2 * MURO, -2 * MURO)

    def _dibujarActor(self, nombre, x, y, escala, alpha=255, clave=None):
        if nombre == "heroe" and clave == "jugador" and self._activoCaminar() \
                and self.hx is not None:
            if self.moviendo:
                ciclo = int(self.fasePaso * 10.0) % 4
                if ciclo == 0:
                    nombre = "heroe_paso1"
                elif ciclo == 2:
                    nombre = "heroe_paso2"
                else:
                    nombre = "heroe"
                rebote = int(3 * abs(math.sin(self.fasePaso * 10.0 * math.pi / 2.0)))
            else:
                rebote = 0
            x, y = self.hx, self.hy - rebote
        elif nombre in self.ACTORES and escala >= 3:
            ladoBase = LADO_BASE * escala
            ladoReal = max(20, int(ladoBase * self.FACTOR_ACTOR))
            offset = (ladoBase - ladoReal) // 2
            x += offset
            y += offset
        return super()._dibujarActor(nombre, x, y, escala, alpha, clave)

    def _caminar(self, dt):
        self.moviendo = False
        if not self._activoCaminar() or self.escena != "escenario":
            return
        suelo = self._suelo()
        sala = self.captura.sala.id
        if self.hx is None or sala != self._salaCaminar:
            self._salaCaminar = sala
            self.hx, self.hy = float(suelo.centerx - 24), float(suelo.bottom - 92)
        if self.transicion > 0.55 or self.submenu is not None:
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
        self.hx = max(suelo.x, min(suelo.right - 48, self.hx + dx * self.VELOCIDAD_CAMINAR * dt))
        self.hy = max(suelo.y, min(suelo.bottom - 44, self.hy + dy * self.VELOCIDAD_CAMINAR * dt))
        if dx != 0:
            self.mira = 1 if dx > 0 else -1
        self.moviendo = True
        self.fasePaso += dt

        # Cruzar automáticamente si toca el borde de una puerta abierta en la dirección que camina
        objetivo = self._objetivoCercano()
        if objetivo is not None and objetivo[0] == ACC_MOVER:
            dirPuerta = objetivo[1]
            if ((dirPuerta == "N" and dy < 0 and self.hy <= suelo.y + 4) or
                (dirPuerta == "S" and dy > 0 and self.hy >= suelo.bottom - 48) or
                (dirPuerta == "O" and dx < 0 and self.hx <= suelo.x + 4) or
                (dirPuerta == "E" and dx > 0 and self.hx >= suelo.right - 52)):
                self._activar(Entrada("", ACC_MOVER, dirPuerta))

    def _objetivoCercano(self):
        """(accion, dato) del objeto o la puerta junto al heroe, o None."""
        if self.hx is None:
            return None
        sala = self.captura.sala
        suelo = self._suelo()
        heroe = pygame.Rect(int(self.hx), int(self.hy), 48, 48).inflate(16, 16)
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
                return (ACC_RECOGER, sala.suelo[i].indice)
        return None

    def _dibujarSala(self):
        super()._dibujarSala()
        if self.escena != "escenario":
            return
        base = ESCENARIO
        if self.modoCaminar:
            self._chip((base.x + 110, base.y + 16), "CAMINANDO · [C] SALIR", AMARILLO,
                       base.inflate(-4, -4))
            if self.hx is not None and self.transicion <= 0.55 and self.submenu is None:
                objetivo = self._objetivoCercano()
                if objetivo is not None:
                    accion, dato = objetivo
                    if accion == ACC_RECOGER:
                        texto, tono = "Z: TOMAR", VERDE
                    elif accion == ACC_ABRIR:
                        texto, tono = "Z: ABRIR", DORADO
                    else:
                        texto, tono = "Z: IR %s" % dato, CIAN
                    self._chip((int(self.hx) + 24, int(self.hy) - 10), texto, tono,
                               base.inflate(-4, -4))
        else:
            self._chip((base.x + 52, base.y + 16), "[C] CAMINAR", ACERO, base.inflate(-4, -4))

    # ------------------------------------------------------------------ entrada
    def _pulsarA(self):
        self.pulso = [None, 0.16]
        if (self._activoCaminar() and self.escena == "escenario" and not self.esperando
                and self.submenu is None):
            objetivo = self._objetivoCercano()
            if objetivo is not None:
                self._activar(Entrada("", objetivo[0], objetivo[1]))
                return
        super()._pulsarA()

    def _manejarEvento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for zona in self.zonas:
                if zona[0].collidepoint(evento.pos):
                    self.pulso = [zona[0], 0.16]
                    break
        if (evento.type == pygame.KEYDOWN and not self.mostrarAyuda
                and self.escena == "escenario"):
            if evento.key == pygame.K_c and self.captura is not None and not self.combate:
                self.modoCaminar = not self.modoCaminar
                self.hx = None
                return
            # En modo caminar, las flechas/WASD mueven al personaje en pantalla;
            # si el modo caminar está desactivado, super()._manejarEvento usa el menú normal.
            if (self._activoCaminar() and self.submenu is None
                    and evento.key in self.TECLAS_MOVER):
                return
        super()._manejarEvento(evento)

    # ------------------------------------------------------------------ escenas
    def _lienzo(self, tono=PIEDRA_OSCURA):
        super()._lienzo(tono)
        if self.escena != self.escenaVista:
            self.escenaVista = self.escena
            self.escenaTiempo = 0.0
            self.menuTiempo = 0.0

    def _dibujarSistema(self):
        self._atenuar()
        super()._dibujarSistema()

    def _dibujarBitacora(self):
        self._atenuar()
        super()._dibujarBitacora()

    def _dibujarFinal(self):
        self._atenuar()
        super()._dibujarFinal()

    def _dibujarTitulo(self):
        self._lienzo((16, 16, 28))
        ticks = pygame.time.get_ticks()

        self.texto(ANCHO // 2, 38, "CRIPTA", 44, DORADO, centrado=True, sombra=TINTA)
        self.texto(ANCHO // 2, 74, "SELECCIÓN DE EXPEDICIÓN", 18, CIAN, centrado=True, sombra=TINTA)

        btnVolver = pygame.Rect(28, 28, 170, 36)
        hoverVolver = btnVolver.collidepoint(self.posRaton)
        self.caja(btnVolver, relleno=_aclara(PANEL, 0.2) if hoverVolver else PANEL,
                  borde=BLANCO if hoverVolver else BORDE_ACERO, radio=8)
        self.texto(btnVolver.centerx, btnVolver.centery, "[X / ESC] PORTADA", 16,
                   BLANCO if hoverVolver else PERLA, centrado=True)
        self.zona(btnVolver, UI_SERVICIO, "ir_portada")

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
                    parametros["ancho"], parametros["alto"], parametros["ancho"] * parametros["alto"])
                if i == 0:
                    difTexto, difTono = "★☆☆ FÁCIL", VERDE
                elif i == 1:
                    difTexto, difTono = "★★☆ MEDIA", DORADO
                else:
                    difTexto, difTono = "★★★ DIFÍCIL", ROJO
            else:
                salasCount = parametros.get("salas", "?")
                difRaw = str(parametros.get("dificultad", "media")).lower()
                detalle = "%s salas" % salasCount
                if "facil" in difRaw or "fácil" in difRaw:
                    difTexto, difTono = "★☆☆ FÁCIL", VERDE
                elif "alta" in difRaw or "dificil" in difRaw or "difícil" in difRaw:
                    difTexto, difTono = "★★★ DIFÍCIL", ROJO
                else:
                    difTexto, difTono = "★★☆ MEDIA", DORADO
            self.texto(rect.x + 36, rect.y + 42, detalle, 16, ACERO)
            self._chip((rect.right - 60, rect.centery), difTexto, difTono)
            self.zona(rect, UI_SERVICIO, "cripta:%d" % i)

        colDerX = 554
        anchoDer = 398

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
        self.texto(btnAzar.centerx, btnAzar.centery, "[R] AL AZAR", 16,
                   DORADO if hoverAzar else CREMA, centrado=True)
        self.zona(btnAzar, UI_SERVICIO, "semilla_azar")
        self.texto(cajaSemilla.x + 24, cajaSemilla.y + 88,
                   "Ajusta con < > o pulsa [R] para azar", 14, APAGADO)

        cajaMision = pygame.Rect(colDerX, 226, anchoDer, 154)
        self.caja(cajaMision)
        self._encabezado(cajaMision, "reglas de supervivencia")
        pautas = (("•", "Sortea las trampas ocultas."),
                  ("•", "Cazadores: ruta de menor costo."),
                  ("•", "Halla la Llave y llega a la Salida."),
                  ("•", "Usa la Bolsa [I] y el Retroceso."))
        for idx, (vineta, textoPauta) in enumerate(pautas):
            self.texto(cajaMision.x + 20, cajaMision.y + 38 + idx * 26, vineta, 18, DORADO)
            self.texto(cajaMision.x + 36, cajaMision.y + 38 + idx * 26, textoPauta, 15, PERLA)

        cajaEmpezar = pygame.Rect(colDerX, 394, anchoDer, 102)
        hoverEmpezar = cajaEmpezar.collidepoint(self.posRaton)
        pulsoVerde = 0.85 + 0.15 * math.sin(ticks / 260.0)
        tonoFondo = _mezclar(PANEL, VERDE, 0.25 if hoverEmpezar else 0.18 * pulsoVerde)
        self.caja(cajaEmpezar, relleno=tonoFondo,
                  borde=VERDE if hoverEmpezar else _mezclar(VERDE, ACERO, 0.4), radio=12)
        self.texto(cajaEmpezar.centerx, cajaEmpezar.y + 26, "¡INICIAR EXPEDICIÓN!", 30, BLANCO,
                   centrado=True, sombra=TINTA)
        self._chip((cajaEmpezar.centerx, cajaEmpezar.y + 70), "PULSA [Z] O [ENTER]", VERDE)
        self.zona(cajaEmpezar, UI_SERVICIO, "empezar")

        cajaTeclas = pygame.Rect(colDerX, 510, anchoDer, 106)
        self.caja(cajaTeclas)
        arriba = self._encabezado(cajaTeclas, "atajos y controles")
        controles = (("Z / ENTER", "confirmar"), ("X / ESC", "volver"),
                     ("W / S", "elegir"), ("A / D", "semilla"),
                     ("I", "bolsa"), ("C", "caminar"))
        for idx, (tClave, descClave) in enumerate(controles):
            px = cajaTeclas.x + 16 + (idx % 2) * 190
            py = arriba + 4 + (idx // 2) * 22
            anchoClave = self.fuente(13).size(tClave)[0]
            self._chip((px + anchoClave // 2 + 6, py + 8), tClave, DORADO)
            self.texto(px + 84, py + 1, descClave, 14, ACERO)

        local = len(self.criptas) > 0 and "ancho" in self.criptas[0][1]
        self.texto(ANCHO // 2, ALTO - 20,
                   "modo demostración local: motor determinista y estructuras propias" if local
                   else "modo conectado / offline: motor determinista y estructuras propias",
                   14, (75, 85, 115), centrado=True)


# Hace que main.py use esta version sin tocarlo. Debe ser la ultima linea del archivo.
VistaGrafica = VistaGraficaFinal


def _ladoHeroe(self):
    return max(24, int(LADO_BASE * 3 * self.FACTOR_ACTOR))


def _suelo(self):
    # Área interior transitable estrictamente delimitada por las paredes de la sala
    margenPared = MURO + 10
    return ESCENARIO.inflate(-2 * margenPared, -2 * margenPared)


def _caminar(self, dt):
    self.moviendo = False
    if not self._activoCaminar() or self.escena != "escenario":
        return
    suelo = self._suelo()
    lado = self._ladoHeroe()
    minX = float(suelo.left)
    maxX = float(max(suelo.left, suelo.right - lado))
    minY = float(suelo.top)
    maxY = float(max(suelo.top, suelo.bottom - lado))

    sala = self.captura.sala.id
    if self.hx is None or sala != self._salaCaminar:
        self._salaCaminar = sala
        self.hx = max(minX, min(maxX, float(suelo.centerx - lado // 2)))
        self.hy = max(minY, min(maxY, float(suelo.bottom - lado - 12)))

    if self.transicion > 0.55 or self.submenu is not None:
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

    # Bloqueo estricto contra las 4 paredes de la sala
    self.hx = max(minX, min(maxX, self.hx + dx * self.VELOCIDAD_CAMINAR * dt))
    self.hy = max(minY, min(maxY, self.hy + dy * self.VELOCIDAD_CAMINAR * dt))

    if dx != 0:
        self.mira = 1 if dx > 0 else -1
    self.moviendo = True
    self.fasePaso += dt

    # Cruzar automáticamente solo al llegar al umbral de una puerta abierta
    objetivo = self._objetivoCercano()
    if objetivo is not None and objetivo[0] == ACC_MOVER:
        dirPuerta = objetivo[1]
        if ((dirPuerta == "N" and dy < 0 and self.hy <= minY + 4) or
                (dirPuerta == "S" and dy > 0 and self.hy >= maxY - 4) or
                (dirPuerta == "O" and dx < 0 and self.hx <= minX + 4) or
                (dirPuerta == "E" and dx > 0 and self.hx >= maxX - 4)):
            self._activar(Entrada("", ACC_MOVER, dirPuerta))


def _objetivoCercano(self):
    """(accion, dato) del objeto o la puerta junto al heroe, o None."""
    if self.hx is None:
        return None
    sala = self.captura.sala
    suelo = self._suelo()
    lado = self._ladoHeroe()
    heroe = pygame.Rect(int(self.hx), int(self.hy), lado, lado).inflate(20, 20)
    base = ESCENARIO
    puertas = {"N": (base.centerx - 24, base.top),
               "S": (base.centerx - 24, base.bottom - 48),
               "E": (base.right - 48, base.centery - 24),
               "O": (base.left, base.centery - 24)}
    for salida in sala.salidas:
        if salida.direccion in puertas:
            x, y = puertas[salida.direccion]
            if heroe.colliderect(pygame.Rect(x, y, 48, 48)):
                return (ACC_ABRIR if salida.cerrada else ACC_MOVER, salida.direccion)
    for i in range(len(sala.suelo)):
        x, y = self._posicionSuelo(i, suelo)
        if heroe.colliderect(pygame.Rect(x, y, 32, 32)):
            return (ACC_RECOGER, sala.suelo[i].indice)
    return None