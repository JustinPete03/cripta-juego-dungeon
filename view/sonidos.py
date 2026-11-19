# Sintetizador retro de efectos de sonido (SFX) y música ambiental chiptune en memoria.
# Usa únicamente la biblioteca estándar (array, math) y pygame.mixer cuando está disponible.

import array
import math

FRECUENCIA = 22050


def _notaAHz(midi):
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def _sintetizarPista(secuencia, tempoBpm, volumen=0.14):
    """Genera un buffer PCM 16-bit mono polifónico (melodía + bajo) con envolvente suave."""
    segPorPulso = 60.0 / tempoBpm
    muestras = array.array("h")
    escalaVol = 32767.0 * max(0.0, min(1.0, volumen))
    dosPi = 2.0 * math.pi
    for melodia, bajo, pulsos in secuencia:
        dur = pulsos * segPorPulso
        total = max(1, int(FRECUENCIA * dur))
        hzMel = _notaAHz(melodia) if melodia else 0.0
        hzBaj = _notaAHz(bajo) if bajo else 0.0
        ataqueLim = max(1.0, FRECUENCIA * 0.02)
        invTotal = 1.0 / float(total)
        for i in range(total):
            t = i / float(FRECUENCIA)
            ataque = min(1.0, i / ataqueLim)
            caida = max(0.0, 1.0 - (i * invTotal) * 0.55)
            env = ataque * caida
            val = 0.0
            if hzMel > 0.0:
                fase = (t * hzMel) % 1.0
                tri = 4.0 * abs(fase - 0.5) - 1.0
                sen = math.sin(dosPi * hzMel * t)
                val += (0.65 * tri + 0.35 * sen) * 0.65
            if hzBaj > 0.0:
                val += math.sin(dosPi * hzBaj * t) * 0.45
            muestras.append(max(-32767, min(32767, int(val * env * escalaVol))))
    return muestras.tobytes()


RECETAS_MUSICA = {
    # 1. Música de Título (épica y misteriosa en La menor)
    "musica_titulo": (
        (
            (69, 45, 1.0), (72, 45, 1.0), (76, 45, 1.0), (79, 45, 1.0),
            (77, 41, 1.5), (76, 41, 0.5), (72, 41, 1.0), (69, 41, 1.0),
            (71, 43, 1.0), (74, 43, 1.0), (76, 43, 1.5), (74, 43, 0.5),
            (72, 40, 2.0), (71, 40, 2.0),
        ),
        105,
        0.13,
    ),
    # 2. Música de Mazmorra (ambiental lenta de exploración)
    "musica_mazmorra": (
        (
            (62, 38, 1.5), (65, 38, 0.5), (69, 38, 1.0), (67, 38, 1.0),
            (65, 34, 1.5), (62, 34, 0.5), (60, 34, 2.0),
            (64, 36, 1.0), (67, 36, 1.0), (69, 36, 1.5), (65, 36, 0.5),
            (62, 38, 3.0), (0, 38, 1.0),
        ),
        82,
        0.12,
    ),
    # 3. Música de Combate (rápida y tensa)
    "musica_combate": (
        (
            (62, 38, 0.5), (62, 38, 0.5), (65, 38, 0.5), (69, 38, 0.5),
            (68, 37, 0.5), (65, 37, 0.5), (62, 37, 0.5), (65, 37, 0.5),
            (67, 39, 0.5), (67, 39, 0.5), (70, 39, 0.5), (74, 39, 0.5),
            (73, 40, 1.0), (69, 40, 1.0),
        ),
        148,
        0.14,
    ),
}


def _ondaCuadrada(t, freq):
    return 1.0 if math.sin(2.0 * math.pi * freq * t) >= 0.0 else -1.0


def _ondaTriangular(t, freq):
    fase = (freq * t) % 1.0
    return 4.0 * fase - 1.0 if fase < 0.5 else 3.0 - 4.0 * fase


def _sintetizar(notas, forma="cuadrada", volumen=0.25):
    """Genera un buffer PCM 16-bit mono a partir de una secuencia (freqInicio, freqFin, durSeg)."""
    muestras = array.array("h")
    amplitudMax = int(32767 * max(0.0, min(1.0, volumen)))
    for f0, f1, dur in notas:
        total = max(1, int(FRECUENCIA * dur))
        for i in range(total):
            frac = i / total
            t = i / FRECUENCIA
            freq = f0 + (f1 - f0) * frac
            # Envolvente suave de ataque y caída para evitar clics.
            ataque = min(1.0, i / max(1, int(total * 0.08)))
            caida = max(0.0, 1.0 - frac ** 1.3)
            env = ataque * caida
            if forma == "ruido":
                val = math.sin(12.9898 * i + 78.233 * freq) * 43758.5453
                onda = 2.0 * (val - math.floor(val)) - 1.0
            elif forma == "tri":
                onda = _ondaTriangular(t, freq)
            elif forma == "seno":
                onda = math.sin(2.0 * math.pi * freq * t)
            else:
                onda = _ondaCuadrada(t, freq)
            muestras.append(int(amplitudMax * env * onda))
    return muestras.tobytes()


RECETAS_SFX = {
    "paso":      (((160, 110, 0.055),), "tri", 0.22),
    "menu":      (((520, 680, 0.040),), "tri", 0.16),
    "alerta":    (((280, 210, 0.08), (200, 150, 0.09)), "cuadrada", 0.22),
    "golpe":     (((240, 75, 0.09), (110, 50, 0.07)), "ruido", 0.30),
    "abrir":     (((330, 520, 0.06), (520, 740, 0.08)), "cuadrada", 0.22),
    "recoger":   (((523, 659, 0.055), (659, 880, 0.075)), "tri", 0.24),
    "usar":      (((440, 660, 0.07), (660, 990, 0.11)), "seno", 0.25),
    "retroceso": (((780, 440, 0.09), (580, 320, 0.11)), "tri", 0.25),
    "victoria":  (((523, 523, 0.08), (659, 659, 0.08), (784, 784, 0.08), (1046, 1046, 0.20)), "tri", 0.24),
    "derrota":   (((392, 349, 0.11), (311, 261, 0.13), (220, 146, 0.22)), "cuadrada", 0.22),
}


class BancoSonidos:
    """Administra efectos de sonido (SFX) y música ambiental chiptune en bucle."""

    def __init__(self):
        self.disponible = False
        self.activo = True
        self.sonidos = {}
        self.pistas = {}
        self.pistaActual = None

    def iniciar(self, pygame):
        self.sonidos = {}
        self.pistas = {}
        self.pistaActual = None
        self.disponible = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=FRECUENCIA, size=-16, channels=1, buffer=512)
            for nombre, (notas, forma, vol) in RECETAS_SFX.items():
                crudo = _sintetizar(notas, forma, vol)
                self.sonidos[nombre] = pygame.mixer.Sound(buffer=crudo)
            for nombre, (secuencia, tempo, vol) in RECETAS_MUSICA.items():
                crudoPista = _sintetizarPista(secuencia, tempo, vol)
                self.pistas[nombre] = pygame.mixer.Sound(buffer=crudoPista)
            self.disponible = True
        except Exception:
            self.disponible = False
            self.sonidos = {}
            self.pistas = {}

    def reproducir(self, nombre):
        if not self.disponible or not self.activo:
            return
        sonido = self.sonidos.get(nombre)
        if sonido is not None:
            try:
                sonido.play()
            except Exception:
                pass

    def actualizarMusica(self, escena, enCombate=False):
        if not self.disponible:
            return
        if not self.activo:
            self.detenerMusica()
            return
        if escena in ("portada", "titulo"):
            objetivo = "musica_titulo"
        elif escena == "final":
            self.detenerMusica()
            return
        elif enCombate:
            objetivo = "musica_combate"
        else:
            objetivo = "musica_mazmorra"

        if objetivo == self.pistaActual:
            return
        self.detenerMusica()
        pista = self.pistas.get(objetivo)
        if pista is not None:
            try:
                pista.play(loops=-1)
                self.pistaActual = objetivo
            except Exception:
                self.pistaActual = None

    def detenerMusica(self):
        for pista in self.pistas.values():
            try:
                pista.stop()
            except Exception:
                pass
        self.pistaActual = None

    def alternar(self):
        self.activo = not self.activo
        if not self.activo:
            self.detenerMusica()
        return self.activo
