# Sintetizador retro de efectos de sonido (SFX) en memoria. No reproduce música.
# Usa únicamente la biblioteca estándar (array, math) y pygame.mixer cuando está disponible.

import array
import math

FRECUENCIA = 22050


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
    """Administra únicamente efectos de sonido cortos (sin música de fondo)."""

    def __init__(self):
        self.disponible = False
        self.activo = True
        self.sonidos = {}

    def iniciar(self, pygame):
        self.sonidos = {}
        self.disponible = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=FRECUENCIA, size=-16, channels=1, buffer=512)
            for nombre, (notas, forma, vol) in RECETAS_SFX.items():
                crudo = _sintetizar(notas, forma, vol)
                self.sonidos[nombre] = pygame.mixer.Sound(buffer=crudo)
            self.disponible = True
        except Exception:
            self.disponible = False
            self.sonidos = {}

    def reproducir(self, nombre):
        if not self.disponible or not self.activo:
            return
        sonido = self.sonidos.get(nombre)
        if sonido is not None:
            try:
                sonido.play()
            except Exception:
                pass

    def alternar(self):
        self.activo = not self.activo
        return self.activo
