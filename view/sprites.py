# Hoja de sprites del view. Datos de presentación: el modelo no conoce ninguno de estos nombres.
#
# Cada sprite es una rejilla de 16x16 escrita como dieciséis cadenas de dieciséis caracteres.
# Un carácter es una tecla de PALETA; '.' queda transparente y el contorno oscuro se añade solo.
#
# La paleta imita los conjuntos de 16 bits de la época SNES: cada material tiene luz, medio,
# sombra y sombra profunda, y la luz cenital cae siempre desde arriba a la izquierda.

MEDIDA = 16

CLAVE = (255, 0, 255)

CONTORNO = (10, 10, 18)

TRANSPARENTE = None

PALETA = {
    # Neutros
    "K": (8, 8, 16),        # tinta: pupilas, ranuras y huecos
    "k": (26, 24, 40),      # sombra profunda
    "g": (62, 60, 84),      # sombra
    "m": (108, 106, 134),   # medio
    "l": (162, 162, 188),   # luz
    "w": (216, 216, 234),   # luz alta
    "W": (250, 250, 255),   # especular
    # Piel
    "S": (252, 214, 166),   # piel luz
    "H": (226, 166, 112),   # piel medio
    "h": (168, 108, 66),    # piel sombra
    "s": (244, 168, 180),   # carne rosada: orejas, hocicos y almohadillas
    # Rojos (gorro, sangre, cera)
    "R": (234, 78, 70),
    "r": (176, 40, 50),
    "e": (108, 22, 36),
    # Verdes (túnica, veneno, hojas)
    "G": (104, 202, 112),
    "T": (48, 142, 76),
    "t": (24, 86, 56),
    "V": (162, 238, 120),   # verde ácido del veneno
    # Cueros y maderas
    "N": (172, 120, 64),
    "n": (118, 74, 36),
    "j": (70, 42, 22),
    # Hueso y pergamino
    "D": (250, 242, 212),
    "M": (208, 192, 152),
    "Q": (146, 128, 98),
    # Metales
    "Z": (216, 226, 244),   # acero luz
    "L": (152, 162, 192),   # acero medio
    "X": (94, 102, 136),    # acero sombra
    "F": (52, 56, 84),      # acero sombra profunda
    # Dorados
    "Y": (255, 228, 122),
    "f": (238, 178, 58),
    "y": (156, 104, 26),
    # Azules y cianes
    "B": (108, 152, 240),
    "C": (48, 88, 190),
    "c": (24, 44, 116),
    "I": (146, 236, 232),
    "i": (56, 166, 172),
    # Púrpuras
    "P": (188, 122, 222),
    "p": (112, 62, 152),
    "v": (62, 32, 96),
    # Fuego
    "O": (255, 180, 74),
    "o": (228, 112, 36),
}


def color(tecla):
    if tecla == ".":
        return TRANSPARENTE
    return PALETA.get(tecla, TRANSPARENTE)


HEROE = (
    "....RRRRRRR.....",
    "...RRRRRRRRR....",
    "..RRRRRRRRRRR...",
    "..RrrrrrrrrR....",
    "..rrrrrrrrrrr...",
    "...SSSSSSSSS....",
    "...SKSSSSSKS....",
    "...SSSSSSSSSS...",
    "....HHSSSSh.....",
    "...GGGGGGGGG....",
    "..GtGGGGGGGtG...",
    "..GtGyyyyGGtG...",
    "..GtGGGGGGGtG...",
    "..HH.GGGGGG.hh..",
    ".....nn..nn.....",
    "....jjnn.jjnn...",
)

HEROE_ESPALDAS = (
    "....RRRRRRR.....",
    "...RRRRRRRRR....",
    "..RRRRRRRRRRR...",
    "..RRRRRRRRRRR...",
    "..RrrrrrrrrrR...",
    "..RRRRRRRRRRR...",
    "..RrrrrrrrrrR...",
    "..nnnnnnnnnnn...",
    "...nnnnnnnnn....",
    "...GGGGGGGGG....",
    "..GtGGGGGGGtG...",
    "..GtGGGGGGGtG...",
    "..GtGyyyyGGtG...",
    "..HH.GGGGGG.hh..",
    ".....nn..nn.....",
    "....jjnn.jjnn...",
)

RATA = (
    "................",
    "................",
    "................",
    "................",
    "..........mmm...",
    ".........mslsm..",
    "m........msllm..",
    ".m......mllllmm.",
    "..m....mlllKllsm",
    "...mmmmlllllllmm",
    "....mllllllllmm.",
    "....mllllllmm...",
    ".....mg.mm.mg...",
    "......g..g..g...",
    "................",
    "................",
)

ESQUELETO = (
    "....DDDDDD......",
    "...DDDDDDDD.....",
    "...DDDDDDDD.....",
    "...DkDDDDkD.....",
    "...DDDDDDDD.....",
    "....DDkkDD......",
    ".....MMMM.......",
    "...DDDDDDDD.....",
    "..D.DDDDDD.D....",
    "..D.DkDDk.D.D...",
    "....DDDDDD......",
    "....MkDDkM......",
    "...DDDDDDDD.....",
    "...D.DMMQ.D.....",
    ".....MM.MM......",
    "....QQ...QQ.....",
)

MURCIELAGO = (
    "................",
    "..v..........v..",
    ".vPv...vv...vPv.",
    ".vPPPvvPPvvPPPv.",
    ".vPPPPpPPpPPPPv.",
    ".vPPPpPRRpPPPvv.",
    "..vPppRWWRppPv..",
    "...pppRRRppp....",
    "....pRRRRRp.....",
    ".....pWWWp......",
    "......ppp.......",
    ".....v...v......",
    "................",
    "................",
    "................",
    "................",
)

DAGA = (
    "........ZZ......",
    ".......ZWZ......",
    ".......ZWZ......",
    ".......ZWL......",
    ".......ZWL......",
    ".......ZWL......",
    ".......ZWL......",
    "......ZWLL......",
    ".....YYffYY.....",
    "......YffY......",
    "......NnnN......",
    "......NnnN......",
    "......nNNn......",
    "......NnnN......",
    ".....YYffYY.....",
    "......YYff......",
)

POCION = (
    ".....jjjj.......",
    ".....jNNNj......",
    ".....jjjj.......",
    "....ccBBcc......",
    "...cBWBBBcc.....",
    "..cBBBBBBBBc....",
    "..cBBCCBBBcc....",
    "..cBBCCBBBcc....",
    "..cBBBBBBBcc....",
    "..cBBBBBBcc.....",
    "...ccBBBBc......",
    "....ccccc.......",
    "................",
    "................",
    "................",
    "................",
)

ANTIDOTO = (
    ".....jjjj.......",
    ".....jNNNj......",
    ".....jjjj.......",
    "....ttVVtt......",
    "...tVWVVVvt.....",
    "..tVVVVVVVVt....",
    "..tVVttVVVVt....",
    "..tVttttVVVt....",
    "..tVVttVVVVt....",
    "..tVVVVVVVVt....",
    "...ttVVVVtt.....",
    "....tttttt......",
    "................",
    "................",
    "................",
    "................",
)

LLAVE = (
    "................",
    "..YYYYYY........",
    ".YYffffYY.......",
    ".YYf..fYY.......",
    ".YYf..fYY.......",
    ".YYffffYY.......",
    "..YYYYYY........",
    "....YYff........",
    "....YYff........",
    "....YYff........",
    "....YYff........",
    "....YYffff......",
    "....YYff..ff....",
    "....YYff..ff....",
    "....YYffff......",
    "................",
)

ANTORCHA = (
    ".......OO.......",
    "......OYYO......",
    ".....OYWWYO.....",
    ".....OYWYYO.....",
    "....oOYWYYOo....",
    "...ooOYYYYOoo...",
    "...ooOoYYYYoo...",
    "....ooOooOoo....",
    ".....ffLLff.....",
    "......fLLf......",
    "......NnnN......",
    "......NnnN......",
    "......jNNj......",
    "......NnnN......",
    "......jNNj......",
    "......jjjj......",
)

PERGAMINO = (
    "................",
    "..QQQQQQQQQQQ...",
    ".QDDDDDDDDDDDQ..",
    ".QDMMMMMMMMMDQ..",
    ".QDMQQQQQQQMDQ..",
    ".QDMMMMMMMMMDQ..",
    ".QDMQQQQQQQMDQ..",
    ".QDMMMMMMMMMDQ..",
    ".QDMQQQQQMMMDQ..",
    ".QDMMMMMMMMMDQ..",
    ".QDDDDDeeeDDDQ..",
    "..QQQQDeeDQQQ...",
    ".....DeeeD......",
    "................",
    "................",
    "................",
)

ARMADURA = (
    "................",
    "......RRRR......",
    ".....ZWWWWX.....",
    "....ZWLLLLWX....",
    "....ZLkLLkLX....",
    "....ZLLLLLLX....",
    ".....XFFFFX.....",
    "..ZZZLLLLXXX....",
    ".ZZWWLLLLLXXX...",
    ".ZLWWLLLLLXXX...",
    ".XLWWLLLLLXXX...",
    ".XXXLLLLLLXXX...",
    "..XXLfLLfLXX....",
    "....LLLLLL......",
    "....LL..LL......",
    "...XXX..XXX.....",
)

TRAMPA = (
    "................",
    "................",
    "................",
    "....Z...Z...Z...",
    "....ZW..ZW..ZW..",
    "....ZLW.ZLW.ZLW.",
    "....ZLLWZLLWZLLW",
    "..XXXXXXXXXXXX..",
    ".XLLLLLLLLLLLLX.",
    ".XLFFLLLLFFLFFX.",
    ".XLLLLLLLLLLLLX.",
    "..XXXXXXXXXXXX..",
    "...XX......XX...",
    "....XXXXXXXX....",
    "................",
    "................",
)

PUERTA_CERRADA = (
    "....NNNNNNNN....",
    "..NNnnnnnnnnNN..",
    ".NnjjjjjjjjjjnN.",
    ".NjnjjnjjnjnjjN.",
    ".NnjjjjjjjjjjnN.",
    ".NjnjjnjjnjnjjN.",
    ".NnjjjjjjjjjjnN.",
    ".XXXXXXXXXXXXXX.",
    ".NjnjjYfjjjjjNN.",
    ".NnjjjffffjjjjN.",
    ".NjnjjYfjjjjjNN.",
    ".NnjjjjjjjjjjnN.",
    ".NjnjjnjjnjnjjN.",
    ".NnjjjjjjjjjjnN.",
    "..NNnnnnnnnnNN..",
    "....NNNNNNNN....",
)

PASAJE = (
    "................",
    "...gggggggggg...",
    "..gllllllllllg..",
    ".glkgggggggglg..",
    ".glggkkkkkgglg..",
    ".glggkKKKKgglg..",
    ".glggkKKKKgglg..",
    ".glggkKKKKgglg..",
    ".glggkKKKKgglg..",
    ".glggkKKKKgglg..",
    ".glggkKKKKgglg..",
    ".glggkKKKKgglg..",
    ".glggkKKKKgglg..",
    ".glggkKKKKgglg..",
    "..glgkkkkkglg...",
    "...gggggggggg...",
)

SALIDA = (
    "................",
    "...gggggggggg...",
    "..gllllllllllg..",
    ".glYYYYYYYYYlg..",
    ".glYfffffffYlg..",
    ".glYfWWWWWfYlg..",
    ".glYfWkkkWfYlg..",
    ".glYfWkkkWfYlg..",
    ".glYfWkkkWfYlg..",
    ".glYfWkkkWfYlg..",
    ".glYfWkkkWfYlg..",
    ".glYfWWWWWfYlg..",
    ".glYfffffffYlg..",
    ".glYYYYYYYYYlg..",
    "..gllllllllllg..",
    "...gggggggggg...",
)

NOMBRES = ("heroe", "heroe_espaldas", "rata", "esqueleto", "murcielago", "daga", "pocion",
           "antidoto", "llave", "antorcha", "pergamino", "armadura", "trampa",
           "puerta_cerrada", "pasaje", "salida")

CUERPOS = (HEROE, HEROE_ESPALDAS, RATA, ESQUELETO, MURCIELAGO, DAGA, POCION, ANTIDOTO,
           LLAVE, ANTORCHA, PERGAMINO, ARMADURA, TRAMPA, PUERTA_CERRADA, PASAJE, SALIDA)

AVISOS = []


def buscarSprite(nombre):
    for i in range(len(NOMBRES)):
        if NOMBRES[i] == nombre:
            return CUERPOS[i]
    return HEROE


def construir(pygame, nombre, escala=3):
    """Devuelve una Surface con colorkey, lista para blitear y para fundir con set_alpha."""
    celdas = _celdas(buscarSprite(nombre), nombre)
    _anadirContorno(celdas)
    lado = MEDIDA * escala
    superficie = pygame.Surface((lado, lado))
    superficie.fill(CLAVE)
    superficie.set_colorkey(CLAVE)
    for y in range(MEDIDA):
        for x in range(MEDIDA):
            tono = celdas[y][x]
            if tono is TRANSPARENTE:
                continue
            pygame.draw.rect(superficie, tono,
                             pygame.Rect(x * escala, y * escala, escala, escala))
    return superficie


def _celdas(cuerpo, nombre="sprite"):
    """Rejilla MEDIDA x MEDIDA con el color de cada pixel."""
    celdas = [[TRANSPARENTE] * MEDIDA for _ in range(MEDIDA)]
    for y, fila in enumerate(cuerpo):
        if y >= MEDIDA:
            break
        if len(fila) != MEDIDA:
            AVISOS.append("%s fila %d mide %d (se recorta o rellena a %d)"
                          % (nombre, y, len(fila), MEDIDA))
        for x in range(MEDIDA):
            tecla = fila[x] if x < len(fila) else "."
            if tecla != "." and tecla not in PALETA:
                AVISOS.append("%s usa la tecla desconocida %r en (%d,%d)" % (nombre, tecla, x, y))
            celdas[y][x] = color(tecla)
    return celdas


def _anadirContorno(celdas):
    """Borde oscuro de un pixel alrededor de la silueta: el sprite se lee sobre el suelo claro."""
    vacio = []
    for y in range(MEDIDA):
        for x in range(MEDIDA):
            if celdas[y][x] is not TRANSPARENTE:
                continue
            if ((x > 0 and celdas[y][x - 1] is not TRANSPARENTE) or
                    (x + 1 < MEDIDA and celdas[y][x + 1] is not TRANSPARENTE) or
                    (y > 0 and celdas[y - 1][x] is not TRANSPARENTE) or
                    (y + 1 < MEDIDA and celdas[y + 1][x] is not TRANSPARENTE)):
                vacio.append((x, y))
    for x, y in vacio:
        celdas[y][x] = CONTORNO
