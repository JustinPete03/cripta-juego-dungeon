"""Benchmark de 2.10: cancelar un efecto con la referencia directa a su evento
(lo implementado) frente a buscar su evento en la agenda y cancelarlo (alternativa descartada).

Usa la Agenda real de Justin. El modelo es el modelo falso de las pruebas, que imita
los métodos de Modelo; cuando se pueda, cambiarlo por el Modelo real."""
import gc
import time

from model.Constantes import EV_ENEMIGO
from model.Entidades import Enemigo
from model.efectos import EfectosJuego, VENENO
from model.ordenamiento.insertion import insertion_sort
from tests.modelo_falso import ModeloFalso


def preparar(n):
    """Agenda con n eventos de relleno y dos efectos de veneno al final (peor caso
    de búsqueda): uno sobre el jugador y otro sobre un enemigo."""
    efectos = EfectosJuego()
    m = ModeloFalso(efectos)
    for i in range(n):
        m.programarEvento(1 + i, EV_ENEMIGO, None)
    m.reloj = n + 1000                    # los efectos quedan después de todo el relleno
    rata = Enemigo("e-1", "ent_rata", "Rata", "guardián", 12, 12, 5, 1, 100)
    efectos.aplicarVeneno(m, m.jugador, 2)
    efectos.aplicarVeneno(m, rata, 2)
    return m, efectos, rata


def mediana(valores):
    ordenados = insertion_sort(valores)
    return ordenados[len(ordenados) // 2]


def medir(n, repeticiones=51):
    t_directo = []
    t_busqueda = []
    for _ in range(repeticiones):
        m, efectos, rata = preparar(n)
        gc.collect()
        gc.disable()                      # evita pausas del recolector dentro de la medición
        try:
            # A: referencia directa guardada en el efecto
            efecto = efectos._buscar(VENENO, m.jugador)
            t0 = time.perf_counter()
            efectos.cancelar(m, efecto)
            t_directo.append(time.perf_counter() - t0)

            # B: el efecto no guarda su evento: se busca en la agenda por propietario
            efecto = efectos._buscar(VENENO, rata)
            t0 = time.perf_counter()
            encontrado = None
            for evento in m.agenda.pendientesValidos():
                if evento.propietario is efecto:
                    encontrado = evento
                    break
            m.cancelarEvento(encontrado)
            t_busqueda.append(time.perf_counter() - t0)
            assert encontrado is not None
        finally:
            gc.enable()

    print(f"n={n:6d} | cancelar directo={mediana(t_directo) * 1e6:9.2f} µs  "
          f"buscando={mediana(t_busqueda) * 1e6:10.2f} µs   (mediana de {repeticiones})")


def ejecutar(tamanos=(100, 1000, 10000)):
    for n in tamanos:
        medir(n)


def main():
    ejecutar()


if __name__ == "__main__":
    main()