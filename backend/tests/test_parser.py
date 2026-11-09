from mediateca.catalog.parser import parse_file


def test_parsea_dvd(dvd_fixture) -> None:
    parsed = parse_file(str(dvd_fixture))

    assert parsed.titn == "2101557"
    assert parsed.titulo.startswith("20.000 especies de abejas")
    assert parsed.anio == 2023
    assert parsed.duracion_min == 129
    assert parsed.idioma == "spa"
    assert parsed.pais == "sp"
    assert parsed.ean == "8436587701627"
    assert parsed.soportes == ["DVD"]
    assert "Dramas cinematográficos" in parsed.generos
    assert "Cine español" in parsed.materias
    assert len(parsed.enlaces) == 2
    assert parsed.disponible is True


def test_parser_extrae_personas_y_roles(dvd_fixture) -> None:
    parsed = parse_file(str(dvd_fixture))
    roles = {role for persona in parsed.personas for role in persona.roles}
    nombres = {persona.nombre for persona in parsed.personas}

    assert "director de cine" in roles
    assert "guionista" in roles
    assert "actor" in roles
    assert "Urresola Solaguren, Estíbaliz" in nombres
    assert "Otero, Sofía (2013-)" in nombres


def test_parser_extrae_ejemplares(dvd_fixture) -> None:
    parsed = parse_file(str(dvd_fixture))

    assert len(parsed.ejemplares) == 2
    primero = parsed.ejemplares[0]
    assert primero.biblioteca_nombre.startswith("ALCALÁ DE HENARES")
    assert primero.sucursal_nombre == "B.P.M. Cardenal Cisneros"
    assert primero.signatura == "DVD-V 10879"
    assert primero.soporte == "DVD"
    assert primero.disponible is True

    segundo = parsed.ejemplares[1]
    assert segundo.biblioteca_nombre.startswith("ALCORCÓN")
    assert segundo.estado == "Prestado"
    assert segundo.disponible is False


def test_parsea_bluray(bluray_fixture) -> None:
    parsed = parse_file(str(bluray_fixture))

    assert parsed.titn == "2107423"
    assert parsed.soportes == ["Blu-ray"]
    assert parsed.duracion_min == 129
    assert parsed.ean == "8436587701634"
    assert len(parsed.ejemplares) == 1
    assert parsed.ejemplares[0].soporte == "Blu-ray"
    assert parsed.ejemplares[0].signatura == "BRD-00219"
    assert parsed.ejemplares[0].disponible is True
