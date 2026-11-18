# Pruebas de aceptación y unitarias para Verificación de Resolubilidad (§3.5, FR-021 a FR-028).

import pytest
from model.Resolubilidad import verificarResolubilidad, ResultadoResolubilidad


def _generarEsqueletoLineal(numSalas, puertasCerradas=None):
    """Genera un esqueleto lineal de salas 1 -> 2 -> ... -> numSalas."""
    puertasCerradas = puertasCerradas or {}  # origen -> {"cerrada": True, "llave": "..."}
    esqueleto = []
    for i in range(1, numSalas + 1):
        salidas = {}
        if i < numSalas:
            info = {"sala": i + 1}
            if i in puertasCerradas:
                info.update(puertasCerradas[i])
            salidas["E"] = info
        if i > 1:
            infoO = {"sala": i - 1}
            if (i - 1) in puertasCerradas:
                infoO.update(puertasCerradas[i - 1])
            salidas["O"] = infoO
        esqueleto.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})
    return esqueleto


def test_cripta_resoluble_orden_determinista():
    """Escenario 1: Cripta resoluble produce un orden determinista de llaves."""
    datos = {
        "id": "c-res-1",
        "sala_inicial": 1,
        "sala_salida": 4,
        "llave_salida": "llave_salida"
    }
    esqueleto = _generarEsqueletoLineal(4, {
        2: {"cerrada": True, "llave": "llave_a"},
        3: {"cerrada": True, "llave": "llave_salida"}
    })
    listaLlaves = [
        {"id": "llave_salida", "sala": 3},
        {"id": "llave_a", "sala": 1}
    ]

    # Ejecutar dos veces independientemente
    res1 = verificarResolubilidad(datos, esqueleto, listaLlaves)
    res2 = verificarResolubilidad(datos, esqueleto, listaLlaves)

    assert res1.resoluble is True
    assert res2.resoluble is True
    assert res1.ordenLlaves == ["llave_a", "llave_salida"]
    assert res1.ordenLlaves == res2.ordenLlaves

    rep = res1.reporte()
    assert "RESOLUBLE" in rep
    assert "1) llave_a" in rep
    assert "2) llave_salida" in rep


def test_llave_en_enemigo():
    """Escenario 2: Llave en enemigo se considera ubicada en su sala inicial."""
    datos = {
        "id": "c-enemigo",
        "sala_inicial": 1,
        "sala_salida": 3,
        "llave_salida": "llave_salida"
    }
    esqueleto = _generarEsqueletoLineal(3, {
        2: {"cerrada": True, "llave": "llave_salida"}
    })
    listaLlaves = [
        {"id": "llave_salida", "sala": 1, "enemigo": "inst_ogro_1"}
    ]

    res = verificarResolubilidad(datos, esqueleto, listaLlaves)
    assert res.resoluble is True
    assert res.ordenLlaves == ["llave_salida"]


def test_ciclo_directo_llave_detras_de_su_propia_puerta():
    """Escenario 5: Llave de salida detrás de la única puerta que ella misma abre ([K -> K])."""
    datos = {
        "id": "c-ciclo-1",
        "sala_inicial": 1,
        "sala_salida": 3,
        "llave_salida": "llave_salida"
    }
    esqueleto = _generarEsqueletoLineal(3, {
        1: {"cerrada": True, "llave": "llave_salida"}
    })
    listaLlaves = [
        {"id": "llave_salida", "sala": 2}
    ]

    res = verificarResolubilidad(datos, esqueleto, listaLlaves)
    assert res.resoluble is False
    assert "llave_salida" in res.llavesInalcanzables
    assert len(res.fronteraBloqueada) == 1
    assert res.fronteraBloqueada[0]["llave"] == "llave_salida"
    assert res.fronteraBloqueada[0]["origen"] == 1
    assert res.fronteraBloqueada[0]["destino"] == 2
    assert res.ciclo == ["llave_salida", "llave_salida"]

    rep = res.reporte()
    assert "NO RESOLUBLE" in rep
    assert "Ciclo de dependencia detectado:" in rep
    assert "[ llave_salida -> llave_salida ]" in rep


def test_ciclo_indirecto_dos_llaves():
    """Escenario 5b: Ciclo indirecto entre dos llaves ([K1 -> K2 -> K1])."""
    datos = {
        "id": "c-ciclo-2",
        "sala_inicial": 1,
        "sala_salida": 4,
        "llave_salida": "llave_salida"
    }
    esqueleto = _generarEsqueletoLineal(4, {
        1: {"cerrada": True, "llave": "K1"},
        2: {"cerrada": True, "llave": "K2"},
        3: {"cerrada": True, "llave": "llave_salida"}
    })
    listaLlaves = [
        {"id": "K2", "sala": 2},
        {"id": "K1", "sala": 3},
        {"id": "llave_salida", "sala": 1}
    ]

    res = verificarResolubilidad(datos, esqueleto, listaLlaves)
    assert res.resoluble is False
    assert "K1" in res.llavesInalcanzables
    assert "K2" in res.llavesInalcanzables
    assert res.ciclo is not None
    assert res.ciclo[0] == res.ciclo[-1]
    assert set(res.ciclo) == {"K1", "K2"}


def test_frontera_bloqueada_y_llaves_inalcanzables_reporte():
    """Prueba de reporte detallado de frontera bloqueada con ubicación de llaves."""
    datos = {
        "id": "c-bloqueada",
        "sala_inicial": 1,
        "sala_salida": 4,
        "llave_salida": "llave_salida"
    }
    esqueleto = _generarEsqueletoLineal(4, {
        2: {"cerrada": True, "llave": "llave_oro"}
    })
    listaLlaves = [
        {"id": "llave_oro", "sala": 3, "enemigo": "dragon_1"},
        {"id": "llave_salida", "sala": 4}
    ]

    res = verificarResolubilidad(datos, esqueleto, listaLlaves)
    assert res.resoluble is False
    assert "llave_oro" in res.llavesInalcanzables
    assert "llave_salida" in res.llavesInalcanzables

    rep = res.reporte()
    assert "NO RESOLUBLE" in rep
    assert "Puerta Sala 2 -> Sala 3 requiere 'llave_oro' (Ubicación: Sala 3 (enemigo dragon_1))" in rep


def test_multiples_puertas_desbloqueadas_por_una_llave():
    """Verifica que el algoritmo incremental despierte múltiples puertas al obtener una llave."""
    datos = {
        "id": "c-multi-puertas",
        "sala_inicial": 1,
        "sala_salida": 4,
        "llave_salida": "llave_maestra"
    }
    esqueleto = [
        {"id": 1, "nombre": "Sala 1", "salidas": {
            "N": {"sala": 2, "cerrada": True, "llave": "llave_maestra"},
            "E": {"sala": 3, "cerrada": True, "llave": "llave_maestra"}
        }},
        {"id": 2, "nombre": "Sala 2", "salidas": {
            "S": {"sala": 1, "cerrada": True, "llave": "llave_maestra"}
        }},
        {"id": 3, "nombre": "Sala 3", "salidas": {
            "O": {"sala": 1, "cerrada": True, "llave": "llave_maestra"},
            "E": {"sala": 4}
        }},
        {"id": 4, "nombre": "Sala 4", "salidas": {
            "O": {"sala": 3}
        }}
    ]
    listaLlaves = [
        {"id": "llave_maestra", "sala": 1}
    ]

    res = verificarResolubilidad(datos, esqueleto, listaLlaves)
    assert res.resoluble is True
    assert res.ordenLlaves == ["llave_maestra"]


def test_sala_salida_requiere_llave_salida_fr028():
    """FR-028: Si la puerta a la salida requiere llave_salida, no basta solo alcanzar la sala."""
    datos = {
        "id": "c-fr028",
        "sala_inicial": 1,
        "sala_salida": 3,
        "llave_salida": "llave_salida"
    }
    esqueleto = _generarEsqueletoLineal(3, {
        2: {"cerrada": True, "llave": "llave_salida"}
    })
    listaLlaves = []

    res = verificarResolubilidad(datos, esqueleto, listaLlaves)
    assert res.resoluble is False


def test_inicio_partida_no_resoluble_sin_forzar(monkeypatch, capsys):
    """Escenario 3: Inicio de partida normal sobre cripta no resoluble se cancela sin --forzar."""
    import main
    from tests.FuentePrueba import FuentePrueba

    fuente = FuentePrueba(ancho=2, alto=2)
    fuente.salas[0]["salidas"]["E"]["cerrada"] = True
    fuente.salas[0]["salidas"]["E"]["llave"] = "llave_fantasma"

    class ArgsMock:
        cripta = "cripta-prueba"
        semilla = 1234
        nombre = "TestBot"
        cacheSize = 25
        log = "test.log"
        forzar = False
        offline = None

    monkeypatch.setattr(main, "construirModelo", lambda *a, **kw: (fuente, None))
    monkeypatch.setattr(fuente, "obtenerLlaves", lambda: {"llaves": []})

    with pytest.raises(SystemExit) as exc:
        main.jugar(ArgsMock(), None)

    assert exc.value.code == 1
    out, _ = capsys.readouterr()
    assert "Partida cancelada: la cripta no es resoluble" in out


def test_inicio_partida_no_resoluble_con_forzar(monkeypatch, capsys):
    """Escenario 4: Con --forzar se muestra advertencia pero no se cancela."""
    import main
    from tests.FuentePrueba import FuentePrueba

    fuente = FuentePrueba(ancho=2, alto=2)
    fuente.salas[0]["salidas"]["E"]["cerrada"] = True
    fuente.salas[0]["salidas"]["E"]["llave"] = "llave_fantasma"

    class ModeloMock:
        def iniciarPartida(self): pass

    class ControladorMock:
        def __init__(self, *args, **kwargs):
            self.termino = True
            self.nombre = ""
            self.idCripta = ""
            self.versionCripta = ""
        def bucleInteractivo(self): pass

    class ArgsMock:
        cripta = "cripta-prueba"
        semilla = 1234
        nombre = "TestBot"
        cacheSize = 25
        log = "test.log"
        forzar = True
        offline = None

    monkeypatch.setattr(main, "construirModelo", lambda *a, **kw: (fuente, ModeloMock()))
    monkeypatch.setattr(fuente, "obtenerLlaves", lambda: {"llaves": []})
    fuente.cache = type("CacheMock", (), {"versionCatalogo": "v1"})()
    fuente.reporte = lambda: "Reporte mock"
    monkeypatch.setattr("controller.ControladorJuego.Controlador", ControladorMock)
    monkeypatch.setattr("adapters.bitacoraReplay.GestorBitacoraReplay.iniciarNuevaBitacora", lambda *a: None)

    main.jugar(ArgsMock(), None)
    out, _ = capsys.readouterr()
    assert "ADVERTENCIA: Iniciando partida forzada sobre cripta no resoluble" in out


def test_ciclos_cadenas_largas_500_y_5000_determinista():
    """R-01: Verificación de ciclos en cadenas de 2, 500 y 5000 llaves sin desbordar pila."""
    def _crearCadenaCiclo(n):
        esqueleto = []
        salidas1 = {"E": {"sala": 2, "cerrada": True, "llave": "k_1"}}
        esqueleto.append({"id": 1, "nombre": "S1", "salidas": salidas1})
        listaLlaves = []

        for i in range(2, n + 2):
            salidas = {"O": {"sala": i - 1, "cerrada": True, "llave": f"k_{i-1}"}}
            if i <= n:
                salidas["E"] = {"sala": i + 1, "cerrada": True, "llave": f"k_{i}"}
                listaLlaves.append({"id": f"k_{i}", "sala": i})
            else:
                listaLlaves.append({"id": "k_1", "sala": i})
            esqueleto.append({"id": i, "nombre": f"S{i}", "salidas": salidas})

        datos = {"id": f"c-ciclo-{n}", "sala_inicial": 1, "sala_salida": n + 1, "llave_salida": "k_salida"}
        listaLlaves.append({"id": "k_salida", "sala": n + 1})
        return datos, esqueleto, listaLlaves

    for n in (2, 500, 5000):
        datos, esqueleto, llaves = _crearCadenaCiclo(n)
        res1 = verificarResolubilidad(datos, esqueleto, llaves)
        res2 = verificarResolubilidad(datos, esqueleto, llaves)

        assert res1.resoluble is False
        assert res1.ciclo is not None
        assert len(res1.ciclo) == n + 1
        assert res1.ciclo[0] == res1.ciclo[-1]
        # Determinismo estricto entre ejecuciones
        assert res1.ciclo == res2.ciclo


def test_multifuente_frontera_ancha_lineal():
    """R-02: Recorrido multifuente único sobre frontera con múltiples puertas bloqueadas."""
    # Estructura: Sala 1 conecta al Norte con Sala 2 (cerrada con K1),
    # al Sur con Sala 3 (cerrada con K2), al Este con Sala 4 (cerrada con K3),
    # y al Oeste con Sala 5 (cerrada con K4).
    # Detrás de cada una hay una cadena de salas con llaves dependientes.
    esqueleto = []
    salidas1 = {
        "N": {"sala": 2, "cerrada": True, "llave": "K1"},
        "S": {"sala": 3, "cerrada": True, "llave": "K2"},
        "E": {"sala": 4, "cerrada": True, "llave": "K3"},
        "O": {"sala": 5, "cerrada": True, "llave": "K4"},
    }
    esqueleto.append({"id": 1, "nombre": "S1", "salidas": salidas1})

    # Salas 2, 3, 4, 5
    esqueleto.append({"id": 2, "nombre": "S2", "salidas": {"S": {"sala": 1, "cerrada": True, "llave": "K1"}, "N": {"sala": 6}}})
    esqueleto.append({"id": 3, "nombre": "S3", "salidas": {"N": {"sala": 1, "cerrada": True, "llave": "K2"}, "S": {"sala": 7}}})
    esqueleto.append({"id": 4, "nombre": "S4", "salidas": {"O": {"sala": 1, "cerrada": True, "llave": "K3"}, "E": {"sala": 8}}})
    esqueleto.append({"id": 5, "nombre": "S5", "salidas": {"E": {"sala": 1, "cerrada": True, "llave": "K4"}, "O": {"sala": 9}}})

    # Salas 6, 7, 8, 9
    esqueleto.append({"id": 6, "nombre": "S6", "salidas": {"S": {"sala": 2}}})
    esqueleto.append({"id": 7, "nombre": "S7", "salidas": {"N": {"sala": 3}}})
    esqueleto.append({"id": 8, "nombre": "S8", "salidas": {"O": {"sala": 4}}})
    esqueleto.append({"id": 9, "nombre": "S9", "salidas": {"E": {"sala": 5}}})

    # Llaves en salas profundas formando dependencias
    listaLlaves = [
        {"id": "K1", "sala": 7},  # K1 está detrás de K2
        {"id": "K2", "sala": 8},  # K2 está detrás de K3
        {"id": "K3", "sala": 9},  # K3 está detrás de K4
        {"id": "K4", "sala": 6},  # K4 está detrás de K1 -> Ciclo K1-K2-K3-K4-K1!
        {"id": "llave_salida", "sala": 6}
    ]

    datos = {"id": "c-frontera-4", "sala_inicial": 1, "sala_salida": 6, "llave_salida": "llave_salida"}

    res = verificarResolubilidad(datos, esqueleto, listaLlaves)
    assert res.resoluble is False
    assert len(res.fronteraBloqueada) == 4
    assert res.ciclo is not None
    assert len(res.ciclo) == 5  # 4 llaves en el ciclo + cierre
    assert res.ciclo[0] == res.ciclo[-1]


def test_cli_verificar_resoluble(monkeypatch, capsys):
    """FR-026 / US-1 Escenario 6: python main.py --verificar con cripta resoluble sale con 0 sin interfaz."""
    import sys
    import main
    from tests.FuentePrueba import FuentePrueba

    fuente = FuentePrueba(ancho=2, alto=2)
    monkeypatch.setattr(main, "crearCliente", lambda args: None)
    monkeypatch.setattr("adapters.ProveedorRed.ProveedorRed", lambda *a, **kw: fuente)

    monkeypatch.setattr(sys, "argv", ["main.py", "--verificar", "cripta-prueba"])
    main.main()

    out, _ = capsys.readouterr()
    assert "=== REPORTE DE RESOLUBILIDAD: RESOLUBLE ===" in out


def test_cli_verificar_no_resoluble(monkeypatch, capsys):
    """FR-026 / US-1 Escenario 6: python main.py --verificar con cripta no resoluble sale con código 1."""
    import sys
    import main
    from tests.FuentePrueba import FuentePrueba

    fuente = FuentePrueba(ancho=2, alto=2)
    fuente.salas[0]["salidas"]["E"]["cerrada"] = True
    fuente.salas[0]["salidas"]["E"]["llave"] = "llave_fantasma"
    monkeypatch.setattr(main, "crearCliente", lambda args: None)
    monkeypatch.setattr("adapters.ProveedorRed.ProveedorRed", lambda *a, **kw: fuente)
    monkeypatch.setattr(fuente, "obtenerLlaves", lambda: {"llaves": []})

    monkeypatch.setattr(sys, "argv", ["main.py", "--verificar", "cripta-bloqueada"])
    with pytest.raises(SystemExit) as exc:
        main.main()

    assert exc.value.code == 1
    out, _ = capsys.readouterr()
    assert "=== REPORTE DE RESOLUBILIDAD: NO RESOLUBLE ===" in out
