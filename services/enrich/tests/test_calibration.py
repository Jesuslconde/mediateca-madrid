from __future__ import annotations

import httpx
import pytest
from mediateca_shared.models import Fuente

from mediateca.catalog.calibration import (
    CalibrationError,
    calibrate_source,
    extract_session_pattern,
    extract_video_option,
)


def test_extrae_patron_de_sesion() -> None:
    sid, pattern = extract_session_pattern(
        "https://opac.example/cgi-bin/abnetopac2/SESION123?ACC=101"
    )

    assert sid == "SESION123"
    assert pattern == r"/abnetopac2/([A-Za-z0-9]+)"


def test_extrae_patron_de_sesion_de_opac_anidado() -> None:
    _sid, pattern = extract_session_pattern(
        "https://www.navarra.es/Appsext/opac/abnetcl.exe/SESION123?ACC=101"
    )

    assert pattern == r"/abnetcl.exe/([A-Za-z0-9]+)"


def test_extrae_opcion_de_video_e_ignora_videojuegos() -> None:
    html = """
    <select name="select03">
      <option value="02">Monografías</option>
      <option value="06">Videograbaciones</option>
      <option value="12">Videojuegos</option>
    </select>
    """

    assert extract_video_option(html) == ("06", "Videograbaciones")


def test_extrae_opcion_de_video_sin_accentos() -> None:
    html = """
    <select name="select03">
      <option value="06">Vídeos y DVD-Vídeos</option>
      <option value="07">CD-ROM, disquetes y DVD-ROM</option>
    </select>
    """

    assert extract_video_option(html) == ("06", "Vídeos y DVD-Vídeos")


def test_extrae_opcion_de_peliculas_y_series() -> None:
    html = """
    <select name="select03">
      <option value="02">Libros</option>
      <option value="06">Películas y series</option>
    </select>
    """

    assert extract_video_option(html) == ("06", "Películas y series")


def _client(handler) -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )


def test_calibra_patron_y_video() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/SESION123"):
            return httpx.Response(
                200,
                text=(
                    '<select name="select03">'
                    '<option value="02">Monografías</option>'
                    '<option value="06">Videograbaciones</option>'
                    "</select>"
                ),
                request=request,
            )
        return httpx.Response(
            200,
            text='<html><head><meta http-equiv="Refresh" '
            'content="0; URL=/opac/SESION123?ACC=101"></head></html>',
            request=request,
        )

    fuente = Fuente(
        codigo="aragon",
        nombre="Aragon",
        base_url="https://opac.example",
        opac_path="/opac",
    )
    client = _client(handler)
    try:
        result = calibrate_source(fuente, client=client)
    finally:
        client.close()

    assert result.session_pattern == r"/opac/([A-Za-z0-9]+)"
    assert result.format_value == "06"
    assert result.format_label == "Videograbaciones"


def test_calibracion_sin_video_falla() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text='<select name="select03"><option value="02">Libros</option></select>',
            request=request,
        )

    fuente = Fuente(
        codigo="aragon",
        nombre="Aragon",
        base_url="https://opac.example",
        opac_path="/opac",
    )
    client = _client(handler)
    try:
        with pytest.raises(CalibrationError):
            calibrate_source(fuente, client=client)
    finally:
        client.close()
