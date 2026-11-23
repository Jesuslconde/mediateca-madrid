from pathlib import Path

from mediateca.catalog.parser import parse_detail, parse_file, parse_search_results


def test_parsea_dvd(dvd_fixture) -> None:
    parsed = parse_file(str(dvd_fixture))

    assert parsed.titn == "2101557"
    assert parsed.titulo == "20.000 especies de abejas"
    assert parsed.anio == 2023
    assert parsed.duracion_min == 129
    assert parsed.idioma == "spa"
    assert parsed.pais == "sp"
    assert parsed.ean == "8436587701627"
    assert parsed.soportes == ["DVD"]
    assert "Dramas cinematográficos" in parsed.generos
    assert "Cine español" in parsed.materias
    assert len(parsed.enlaces) == 2


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
    assert not hasattr(primero, "disponible")
    assert not hasattr(primero, "estado")

    segundo = parsed.ejemplares[1]
    assert segundo.biblioteca_nombre.startswith("ALCORCÓN")
    assert segundo.signatura == "DVD-V 4421"
    assert segundo.soporte == "DVD"


def test_usa_enlace_permanente_del_opac() -> None:
    html = """
    <html><body>
      <span class="js-TITN">2101557</span>
      <span class="js-ntitl">Titulo de prueba</span>
      <span id="xslike">http://gestiona.comunidad.madrid/biblio_publicas/cgi-bin/abnetopac?TITN=2101557</span>
    </body></html>
    """

    parsed = parse_detail(html, url="https://opac/sesion?ACC=165&DOC=1")

    assert parsed.source_url == (
        "http://gestiona.comunidad.madrid/biblio_publicas/cgi-bin/abnetopac?TITN=2101557"
    )


def test_parsea_bluray(bluray_fixture) -> None:
    parsed = parse_file(str(bluray_fixture))

    assert parsed.titn == "2107423"
    assert parsed.soportes == ["Blu-ray"]
    assert parsed.duracion_min == 129
    assert parsed.ean == "8436587701634"
    assert len(parsed.ejemplares) == 1
    assert parsed.ejemplares[0].soporte == "Blu-ray"
    assert parsed.ejemplares[0].signatura == "BRD-00219"


def test_parsea_listado_de_resultados(search_results_fixture) -> None:
    html = search_results_fixture.read_text(encoding="utf-8")

    resultados = parse_search_results(html)

    assert len(resultados) == 3
    primero = resultados[0]
    assert primero.doc == 1
    assert primero.titn == "2101557"
    assert primero.titulo == "20.000 especies de abejas"
    assert primero.anio == 2023
    assert primero.idioma == "spa"
    assert primero.descripcion_fisica.startswith("1 DVD-Video")
    assert primero.marc["T300a"].startswith("1 DVD-Video")
    assert primero.soportes == ["DVD"]
    assert "Dramas cinematográficos" in primero.generos
    assert "Cine español" in primero.materias
    assert primero.personas[0].nombre == "Urresola Solaguren, Estíbaliz"
    assert primero.personas[0].roles == ["director de cine"]

    assert resultados[1].titn == "2107423"
    assert resultados[1].soportes == ["Blu-ray"]
    assert resultados[1].ean == "8436587701634"

    assert resultados[2].titn == "2109999"
    assert resultados[2].anio == 1998
    assert resultados[2].soportes == ["VHS"]



def test_parse_detail_usa_titulo_completo_y_limpio() -> None:
    html = """
    <html><body>
      <span class="js-TITN">123</span>
      <span class="doc_title js-doc_title js-removePunt" data-punt="/">Historia cinematográfica de la Unión Europea : legislación cinematográfica europea / </span>
      <span class="js-ntitl">Historia cinematográfica de la Unión Europea : </span>
      <dl class="docu_etiq">
        <dt>Título uniforme:</dt>
        <dd>Historia cinematográfica de la Unión Europea (Película cinematográfica)</dd>
      </dl>
    </body></html>
    """

    parsed = parse_detail(html)

    assert parsed.titulo == (
        "Historia cinematográfica de la Unión Europea : legislación cinematográfica europea"
    )
    assert parsed.titulo_uniforme == (
        "Historia cinematográfica de la Unión Europea (Película cinematográfica)"
    )


def test_parse_search_usa_titulo_visible_sin_responsabilidad() -> None:
    html = """
    <ol>
      <li class="c-docs_unit">
        <h3><a href="?ACC=165&amp;DOC=1">
          <span class="c-docs_title">20.000 especies de abejas /</span>
          <span class="c-docs_titleRest">dirección y guión de Estibaliz Urresola</span>
        </a></h3>
        <span class="js-TITN">2101557</span>
        <span class="js-T245">20.000 especies de abejas / dirección y guión de Estibaliz Urresola</span>
      </li>
      <li class="c-docs_unit">
        <h3><a href="?ACC=165&amp;DOC=2">
          <span class="c-docs_title">Imágenes y justicia : el Derecho a través del cine /</span>
        </a></h3>
        <span class="js-TITN">2</span>
      </li>
      <li class="c-docs_unit">
        <h3><a href="?ACC=165&amp;DOC=3">
          <span class="js-T245">Alfredo el Grande /Marcos Ordóñez</span>
        </a></h3>
        <span class="js-TITN">3</span>
      </li>
    </ol>
    """

    resultados = parse_search_results(html)

    assert [resultado.titulo for resultado in resultados] == [
        "20.000 especies de abejas",
        "Imágenes y justicia : el Derecho a través del cine",
        "Alfredo el Grande",
    ]


def test_parser_absysnet_con_ruta_abnetcl() -> None:
    base = Path(__file__).resolve().parents[1] / "fixtures" / "abnetcl"
    listing = parse_search_results((base / "search_results.html").read_text(encoding="utf-8"))
    assert [item.titn for item in listing] == ["2101557", "2107423", "2109999"]
    assert all("/abnetcl.cgi/" in (item.source_url or "") for item in listing)

    detail = parse_detail(
        (base / "detail_dvd.html").read_text(encoding="utf-8"),
        "https://opac.example/abnetcl.cgi/SESION/NT1?TITN=2101557",
    )
    assert detail.titn == "2101557"
    assert detail.titulo
    assert detail.ejemplares


def test_parser_andalucia_abnetcl_y_videograbaciones() -> None:
    base = Path(__file__).resolve().parents[1] / "fixtures" / "andalucia"
    listing = parse_search_results(
        (base / "search_results.html").read_text(encoding="utf-8")
    )
    assert [item.titn for item in listing] == ["2101557", "2107423", "2109999"]
    assert all("/abnetcl.cgi/" in (item.source_url or "") for item in listing)

    detail = parse_detail(
        (base / "detail_video.html").read_text(encoding="utf-8"),
        "https://www.juntadeandalucia.es/cultura/absys/abnopac/abnetcl.cgi/SESION/NT1?TITN=2101557",
    )
    assert detail.titn == "2101557"
    assert detail.titulo
    assert detail.publicacion or detail.duracion_min
    assert detail.ejemplares


def test_parser_fixture_andaluz_primera_pagina_sin_captcha() -> None:
    base = Path(__file__).resolve().parents[1] / "fixtures" / "andalucia"
    html = (base / "search_results.html").read_text(encoding="utf-8")

    listing = parse_search_results(html)

    assert [item.titn for item in listing] == ["2101557", "2107423", "2109999"]
    assert [item.doc for item in listing] == [1, 2, 3]
    assert [item.titulo for item in listing] == [
        "20.000 especies de abejas",
        "20.000 especies de abejas",
        "Cine experimental en VHS",
    ]
    assert all(
        "/cultura/absys/abnopac/abnetcl.cgi/SESIONANDA/" in (item.source_url or "")
        for item in listing
    )


def test_parser_ejemplares_andaluces_con_columnas_propias() -> None:
    html = """
    <html><body>
      <span class="js-TITN">1071730</span>
      <span class="doc_title">La épica [Material gráfico proyectable] /</span>
      <span class="js-T300a">56 p. ;</span>
      <div class="copias_data">
        <p><span class="bicobi">GR25</span><span class="bidesc">Órgiva</span></p>
        <div class="c-accordion_item" data-sucosu="434">
          <p><span class="sucosu">434</span><span class="sudesc">B.P.M. Órgiva</span></p>
          <table>
            <thead><tr>
              <th>Localización</th><th>Tipo de ejemplar</th><th>Signatura / supl.</th>
              <th>Vol.</th><th>Disponibilidad</th><th>Soporte</th><th>Novedad</th>
            </tr></thead>
            <tbody><tr>
              <td><span class="copias_label">Localización</span><span>Obras literarias</span></td>
              <td><span class="copias_label">Tipo de ejemplar</span><span>Prestable Libros</span></td>
              <td><span class="copias_label">Signatura</span>
                <a data-bc="1000516123" data-sign="860 FRA epi" href="#">860 FRA epi</a>
              </td>
              <td><span class="copias_label">Identificador de volumen</span></td>
              <td class="copias_tableDisp"><span class="copias_label">Disponibilidad</span><span>Disponible</span></td>
              <td><span class="copias_label">Soporte</span></td>
              <td></td>
            </tr></tbody>
          </table>
        </div>
      </div>
    </body></html>
    """

    parsed = parse_detail(html)

    assert parsed.titulo == "La épica"
    assert parsed.soportes == []
    assert len(parsed.ejemplares) == 1
    ejemplar = parsed.ejemplares[0]
    assert ejemplar.localizacion == "Obras literarias"
    assert ejemplar.signatura == "860 FRA epi"
    assert ejemplar.codigo_barras == "1000516123"
    assert ejemplar.tipo_ejemplar == "Prestable Libros"
    assert ejemplar.soporte is None


def test_parser_ejemplares_andaluces_lee_el_soporte() -> None:
    html = """
    <html><body>
      <span class="js-TITN">533</span>
      <span class="doc_title">101 dálmatas</span>
      <span class="js-T300a">1 videocasete (VHS) (108 min.)</span>
      <div class="copias_data">
        <p><span class="bicobi">GR11</span><span class="bidesc">Loja</span></p>
        <div class="c-accordion_item" data-sucosu="418">
          <table>
            <thead><tr>
              <th>Localización</th><th>Tipo de ejemplar</th><th>Signatura</th>
              <th>Vol.</th><th>Disponibilidad</th><th>Soporte</th>
            </tr></thead>
            <tbody><tr>
              <td><span class="copias_label">Localización</span><span>Audiovisuales</span></td>
              <td><span class="copias_label">Tipo de ejemplar</span><span>Prestable no Librario</span></td>
              <td><span class="copias_label">Signatura</span>
                <a data-bc="1000" data-sign="VHS 12" href="#">VHS 12</a>
              </td>
              <td><span class="copias_label">Vol.</span></td>
              <td><span class="copias_label">Disponibilidad</span><span>Disponible</span></td>
              <td><span class="copias_label">Soporte</span><span>Vídeo (VHS)</span></td>
            </tr></tbody>
          </table>
        </div>
      </div>
    </body></html>
    """

    parsed = parse_detail(html)

    assert parsed.soportes == ["VHS"]
    assert parsed.ejemplares[0].soporte == "VHS"
    assert parsed.ejemplares[0].signatura == "VHS 12"


def test_parser_limpia_calificadores_de_material_en_ficha() -> None:
    html = """
    <html><body>
      <span class="js-TITN">1001622</span>
      <span class="doc_title">La cocina fácil de Ferran Adrià [DVD-Vídeo].</span>
      <span class="js-ntitl">La cocina fácil de Ferran Adrià [</span>
    </body></html>
    """

    parsed = parse_detail(html)

    assert parsed.titulo == "La cocina fácil de Ferran Adrià"


def test_parser_limpia_calificadores_de_material_en_listado() -> None:
    html = """
    <html><body>
      <ul class="c-docs">
        <li class="c-docs_unit">
          <div class="c-docs_header">
            <a class="c-docs_title" href="?ACC=165&amp;DOC=1&amp;TITN=1">Pilates [DVD-Vídeo] : guía esencial</a>
          </div>
          <p class="c-docs_marc"><span class="js-TITN">1</span></p>
        </li>
      </ul>
    </body></html>
    """

    parsed = parse_search_results(html)

    assert len(parsed) == 1
    assert parsed[0].titulo == "Pilates : guía esencial"


def test_parser_conserva_corchetes_que_forman_parte_del_titulo() -> None:
    html = """
    <html><body>
      <span class="js-TITN">200</span>
      <span class="doc_title">[Rec]</span>
    </body></html>
    """

    parsed = parse_detail(html)

    assert parsed.titulo == "[Rec]"


def test_parsea_listado_aragon(aragon_search_fixture) -> None:
    parsed = parse_search_results(aragon_search_fixture.read_text(encoding="utf-8"))

    assert len(parsed) == 2
    assert all(item.titn and item.titulo and item.soportes for item in parsed)


def test_parsea_listado_valencia(valencia_search_fixture) -> None:
    parsed = parse_search_results(valencia_search_fixture.read_text(encoding="utf-8"))

    assert len(parsed) == 2
    assert all(item.titn and item.titulo and item.soportes for item in parsed)


def test_parsea_listado_pais_vasco(pais_vasco_search_fixture) -> None:
    parsed = parse_search_results(pais_vasco_search_fixture.read_text(encoding="utf-8"))

    assert len(parsed) == 2
    assert all(item.titn and item.titulo and item.soportes for item in parsed)


def test_parsea_novedades_ccbip(ccbip_novedades_fixture) -> None:
    parsed = parse_search_results(ccbip_novedades_fixture.read_text(encoding="utf-8"))

    assert len(parsed) == 2
    assert all(item.titn and item.titulo and item.soportes for item in parsed)


def test_parsea_ficha_ccbip_usa_url_permanente(ccbip_detail_fixture) -> None:
    parsed = parse_detail(
        ccbip_detail_fixture.read_text(encoding="utf-8"),
        "http://catalogos.cultura.gob.es/CCBIP/cgi-ccbip/abnetopac/SESION/NT1?TITN=18&FORM=1",
    )

    assert parsed.titn == "18"
    assert parsed.titulo.startswith("007")
    assert parsed.soportes == ["DVD"]
    assert parsed.ejemplares == []
    assert parsed.source_url == (
        "http://catalogos.cultura.gob.es:80/CCBIP/cgi-ccbip/abnetopac?TITN=18"
    )


def test_canonical_tiene_prioridad_sobre_xslike() -> None:
    html = """
    <html><head>
      <link rel="canonical" href="https://opac.example/abnetopac?TITN=123">
    </head><body>
      <span class="js-TITN">123</span>
      <span class="doc_title">Titulo</span>
      <span id="xslike">https://opac.example/abnetopac?TITN=0</span>
    </body></html>
    """

    parsed = parse_detail(html, "https://opac.example/sesion?TITN=123")

    assert parsed.source_url == "https://opac.example/abnetopac?TITN=123"
