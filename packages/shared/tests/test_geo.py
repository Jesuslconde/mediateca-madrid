from __future__ import annotations

from mediateca_shared.geo import centroide, haversine_km


def test_haversine_misma_coordenada() -> None:
    assert haversine_km(40.0, -3.0, 40.0, -3.0) == 0.0


def test_haversine_un_grado_de_latitud() -> None:
    # Un grado de latitud son unos 111.19 km.
    distancia = haversine_km(0.0, 0.0, 1.0, 0.0)
    assert abs(distancia - 111.19) < 0.5


def test_haversine_madrid_barcelona() -> None:
    distancia = haversine_km(40.4168, -3.7038, 41.3851, 2.1734)
    assert 490.0 < distancia < 520.0


def test_centroide_conocido() -> None:
    cp = centroide("28015")
    assert cp is not None
    assert cp.municipio == "Madrid"
    assert 40.3 < cp.latitud < 40.6


def test_centroide_con_cero_inicial() -> None:
    cp = centroide("8001")
    assert cp is not None
    assert cp.codigo == "08001"
    assert cp.municipio == "Barcelona"


def test_centroide_desconocido() -> None:
    assert centroide("00000") is None


def test_centroide_vacio() -> None:
    assert centroide(None) is None
    assert centroide("") is None
