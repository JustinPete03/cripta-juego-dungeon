import os
import math
import wave
import struct

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sonidos")
os.makedirs(CARPETA, exist_ok=True)
FREC = 44100


def guardar_wav(nombre, muestras):
    ruta = os.path.join(CARPETA, nombre)
    with wave.open(ruta, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(FREC)
        datos = b"".join(struct.pack("<h", max(-32767, min(32767, int(m)))) for m in muestras)
        f.writeframes(datos)
    print("Creado:", ruta)


def nota_a_hz(midi):
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def sintetizar_pista(secuencia, tempo_bpm, volumen=0.28):
    """Genera una pista polifónica suave (melodía + bajo) con envolvente ADSR."""
    seg_por_pulso = 60.0 / tempo_bpm
    muestras = []
    for melodia, bajo, pulsos in secuencia:
        dur = pulsos * seg_por_pulso
        total = int(FREC * dur)
        hz_mel = nota_a_hz(melodia) if melodia else 0.0
        hz_baj = nota_a_hz(bajo) if bajo else 0.0

        for i in range(total):
            t = i / float(FREC)
            # Envolvente suave para evitar clics
            ataque = min(1.0, i / (FREC * 0.02))
            caida = max(0.0, 1.0 - (i / float(total)) * 0.55)
            env = ataque * caida

            val = 0.0
            if hz_mel > 0:
                # Onda triangular + armónico suave para timbre de arpa/flauta retro
                fase = (t * hz_mel) % 1.0
                tri = 4.0 * abs(fase - 0.5) - 1.0
                sen = math.sin(2.0 * math.pi * hz_mel * t)
                val += (0.65 * tri + 0.35 * sen) * 0.65
            if hz_baj > 0:
                val += math.sin(2.0 * math.pi * hz_baj * t) * 0.45

            muestras.append(val * env * 32767 * volumen)
    return muestras


def sintetizar_sfx(tipo):
    muestras = []
    if tipo == "golpe":
        dur = 0.18
        for i in range(int(FREC * dur)):
            t = i / float(FREC)
            env = (1.0 - i / (FREC * dur)) ** 2
            hz = 160.0 * (1.0 - t * 3.5)
            val = math.sin(2.0 * math.pi * max(40.0, hz) * t)
            muestras.append(val * env * 18000)
    elif tipo == "puerta":
        notas = [60, 64, 67, 72]  # Acorde mayor brillante
        for n in notas:
            hz = nota_a_hz(n)
            for i in range(int(FREC * 0.09)):
                t = i / float(FREC)
                env = 1.0 - (i / (FREC * 0.09))
                val = math.sin(2.0 * math.pi * hz * t)
                muestras.append(val * env * 14000)
    elif tipo == "objeto":
        for n in (72, 79):
            hz = nota_a_hz(n)
            for i in range(int(FREC * 0.08)):
                t = i / float(FREC)
                env = 1.0 - (i / (FREC * 0.08))
                val = math.sin(2.0 * math.pi * hz * t)
                muestras.append(val * env * 14000)
    return muestras


if __name__ == "__main__":
    # 1. Música de Título (épica y misteriosa en La menor)
    titulo = [
        (69, 45, 1.0), (72, 45, 1.0), (76, 45, 1.0), (79, 45, 1.0),
        (77, 41, 1.5), (76, 41, 0.5), (72, 41, 1.0), (69, 41, 1.0),
        (71, 43, 1.0), (74, 43, 1.0), (76, 43, 1.5), (74, 43, 0.5),
        (72, 40, 2.0), (71, 40, 2.0),
    ]
    guardar_wav("musica_titulo.wav", sintetizar_pista(titulo, tempo_bpm=105))

    # 2. Música de Mazmorra (ambiental lenta de exploración)
    mazmorra = [
        (62, 38, 1.5), (65, 38, 0.5), (69, 38, 1.0), (67, 38, 1.0),
        (65, 34, 1.5), (62, 34, 0.5), (60, 34, 2.0),
        (64, 36, 1.0), (67, 36, 1.0), (69, 36, 1.5), (65, 36, 0.5),
        (62, 38, 3.0), (0, 38, 1.0),
    ]
    guardar_wav("musica_mazmorra.wav", sintetizar_pista(mazmorra, tempo_bpm=82))

    # 3. Música de Combate (rápida y tensa)
    combate = [
        (62, 38, 0.5), (62, 38, 0.5), (65, 38, 0.5), (69, 38, 0.5),
        (68, 37, 0.5), (65, 37, 0.5), (62, 37, 0.5), (65, 37, 0.5),
        (67, 39, 0.5), (67, 39, 0.5), (70, 39, 0.5), (74, 39, 0.5),
        (73, 40, 1.0), (69, 40, 1.0),
    ]
    guardar_wav("musica_combate.wav", sintetizar_pista(combate, tempo_bpm=148))

    # 4. Efectos de sonido
    for sfx in ("golpe", "puerta", "objeto"):
        guardar_wav(sfx + ".wav", sintetizar_sfx(sfx))
