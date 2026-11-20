from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from mediateca_shared.models import Edicion, HarvestJob
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.catalog.flaresolverr import (
    FlareSolverrCookie,
    FlareSolverrError,
    FlareSolverrResponse,
)
from mediateca.catalog.harvester import (
    CaptchaRequired,
    Harvester,
    OpacClient,
    SearchItem,
    SearchPage,
    SessionExpired,
)
from mediateca.core.db import Base

ANDALUCIA_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "andalucia"


def _andalucia_html(name: str) -> str:
    return (ANDALUCIA_FIXTURES / name).read_text(encoding="utf-8")


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


class _FakePaginationClient(OpacClient):
    def __init__(self, pages, *, expire: bool = False) -> None:
        super().__init__(delay=0)
        self.session_id = "TEST"
        self._pages = pages
        self._expire = expire
        self._expired = False
        self.searches = 0
        self.requested: list[str] = []

    def search(self, query: str) -> SearchPage:
        self.searches += 1
        return self._pages[0]

    def fetch_search_page(
        self, url: str, query: str, *, recover_session: bool = True
    ) -> SearchPage:
        self.requested.append(url)
        if self._expire and url == "expire" and not self._expired:
            self._expired = True
            raise SessionExpired("sesion caducada")
        return self._pages[1]

    def open_session(self) -> str:
        return "TEST"

    def _doc_page_url(self, doc: int) -> str:
        return f"doc:{doc}"


def _page(*, next_url: str | None, doc: int, html: str = "") -> SearchPage:
    return SearchPage(
        query="*",
        total=3,
        items=[SearchItem(doc=doc, url=f"detail:{doc}")],
        next_url=next_url,
        html=html,
    )


def test_search_all_recorre_varias_paginas() -> None:
    client = _FakePaginationClient(
        [_page(next_url="next", doc=1), _page(next_url=None, doc=2)]
    )

    pages = list(client.search_all("*"))

    assert [page.items[0].doc for page in pages] == [1, 2]
    assert client.requested == ["next"]


def test_search_all_recupera_sesion_con_rebusqueda_y_salto() -> None:
    client = _FakePaginationClient(
        [_page(next_url="expire", doc=1), _page(next_url=None, doc=2)],
        expire=True,
    )

    pages = list(client.search_all("*"))

    assert [page.items[0].doc for page in pages] == [1, 2]
    assert client.searches == 2
    assert client.requested == ["expire", "doc:2"]


class _PageFeedClient:
    def __init__(self, pages: list[SearchPage]) -> None:
        self.delay = 0.0
        self.pages = pages
        self.calls: list[tuple[str, int | None, int | None]] = []

    def search_all(
        self,
        query: str,
        *,
        max_pages: int | None = None,
        start_doc: int | None = None,
    ):
        self.calls.append((query, max_pages, start_doc))
        yield from self.pages


def _search_html(entries: list[tuple[int, str, str]]) -> str:
    items = []
    for doc, titn, titulo in entries:
        items.append(
            f"""
            <li class="c-docs_unit">
              <a class="c-docs_title" href="?ACC=165&amp;DOC={doc}&amp;TITN={titn}">
                {titulo}
              </a>
              <p class="c-docs_marc">
                <span class="js-TITN">{titn}</span>
                <span class="js-T245a">{titulo}</span>
                <span class="js-FEPU">2024</span>
                <span class="js-LENG">spa</span>
                <span class="js-T300a">1 DVD-Video (ca. 90 min) : son., col.</span>
              </p>
            </li>
            """
        )
    return f"<html><body><ul>{''.join(items)}</ul></body></html>"


def test_harvest_discovery_guarda_checkpoint_y_reanuda_sin_duplicar(
    search_results_fixture,
) -> None:
    session = _session()
    html = search_results_fixture.read_text(encoding="utf-8")

    first_client = _PageFeedClient([_page(next_url=None, doc=3, html=html)])
    stats = Harvester(session, client=first_client).harvest_discovery(max_pages=1)

    assert stats["processed"] == 3
    assert session.scalar(select(func.count(Edicion.id))) == 3
    job = session.scalars(select(HarvestJob).order_by(HarvestJob.id.desc())).first()
    assert job is not None
    assert job.cursor_doc == 3
    assert job.cursor_titn == "2109999"
    assert job.status == "completed"

    resume_html = _search_html(
        [
            (3, "2109999", "Cine experimental en VHS"),
            (4, "2110000", "Novedad del catalogo"),
        ]
    )
    second_client = _PageFeedClient([_page(next_url=None, doc=4, html=resume_html)])
    stats = Harvester(session, client=second_client).harvest_discovery(
        cursor_doc=job.cursor_doc,
        cursor_titn=job.cursor_titn,
        max_pages=1,
    )

    assert second_client.calls == [("*", 1, 3)]
    assert stats["processed"] == 1
    assert session.scalar(select(func.count(Edicion.id))) == 4
    nuevo = session.scalars(select(Edicion).where(Edicion.titn == "2110000")).one()
    assert nuevo.discovery_seen_at is not None
    assert nuevo.missing_at is None


def _listing_html(entries: list[tuple[int, str, str, str]]) -> str:
    items = []
    for doc, titn, titulo, t300 in entries:
        items.append(
            f"""
            <li class="c-docs_unit">
              <a class="c-docs_title" href="?ACC=165&amp;DOC={doc}&amp;TITN={titn}">
                {titulo}
              </a>
              <p class="c-docs_marc">
                <span class="js-TITN">{titn}</span>
                <span class="js-T245a">{titulo}</span>
                <span class="js-T300a">{t300}</span>
              </p>
            </li>
            """
        )
    return f"<html><body><ul>{''.join(items)}</ul></body></html>"


def test_discovery_descarta_registros_no_audiovisuales() -> None:
    session = _session()
    html = _listing_html(
        [
            (1, "100", "La épica", "56 p. ; 23 cm + 60 diapositivas col."),
            (2, "101", "Una película", "1 DVD-Video (ca. 90 min)"),
        ]
    )
    client = _PageFeedClient([_page(next_url=None, doc=2, html=html)])

    stats = Harvester(session, client=client).harvest_discovery(max_pages=1)

    assert stats["processed"] == 1
    assert stats["filtered"] == 1
    assert list(session.scalars(select(Edicion.record_id))) == ["madrid:101"]


class _EnrichClient:
    def __init__(self, html: str) -> None:
        self.delay = 0.0
        self.max_retries = 1
        self.html = html

    def fetch_by_titn(self, titn: str):
        return self.html, f"https://opac.example?TITN={titn}"


def test_enrichment_descarta_registros_no_audiovisuales() -> None:
    from mediateca.catalog.jobs import create_stub

    session = _session()
    create_stub(session, "1071730")
    session.commit()
    html = """
    <html><body>
      <span class="js-TITN">1071730</span>
      <span class="doc_title">La épica</span>
      <span class="js-T300a">56 p. ;</span>
    </body></html>
    """

    stats = Harvester(session, client=_EnrichClient(html)).harvest_enrichment(limit=10)

    assert stats["processed"] == 0
    assert stats["filtered"] == 1
    edicion = session.scalars(select(Edicion)).one()
    assert edicion.enrich_status == "skipped"
    assert edicion.detail_fetched_at is not None
    assert edicion.missing_at is not None


class _FakeSolver:
    def __init__(
        self,
        response: FlareSolverrResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def request(self, method, url, *, params=None, data=None, cookies=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "data": data,
                "cookies": cookies,
            }
        )
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _captcha_client(
    solver: _FakeSolver, *, url: str = "http://flare:8191"
) -> OpacClient:
    client = OpacClient(
        delay=0,
        flaresolverr_url=url,
        flaresolverr_client=solver,
    )
    previous = client.client
    client.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text="No soy un robot")
        )
    )
    previous.close()
    return client


def test_opac_client_configura_flaresolverr() -> None:
    client = OpacClient(
        delay=0,
        flaresolverr_url="http://flare:8191",
        flaresolverr_max_timeout_ms=1234,
    )
    try:
        assert client.flaresolverr_url == "http://flare:8191"
        assert client.flaresolverr_max_timeout_ms == 1234
        assert client.captchas == 0
        assert client.captchas_solved == 0
        assert client.captchas_failed == 0
    finally:
        client.close()


def test_resuelve_captcha_get_y_sincroniza_cookies() -> None:
    solver = _FakeSolver(
        FlareSolverrResponse(
            status_code=200,
            text="<html>ficha resuelta</html>",
            url="https://opac.example/final",
            cookies=[
                FlareSolverrCookie(
                    name="sid", value="nuevo", domain="opac.example", path="/"
                )
            ],
            user_agent="FlareSolverr/UA",
        )
    )
    client = _captcha_client(solver)
    client.client.cookies.set("previa", "1", domain="opac.example", path="/")
    try:
        response = client._request(
            "GET", "https://opac.example/buscar", params={"ACC": 101}
        )
        cookies = {cookie.name: cookie.value for cookie in client.client.cookies.jar}
        user_agent = client.client.headers["User-Agent"]
        metrics = {
            "captchas": client.captchas,
            "resueltos": client.captchas_solved,
            "fallidos": client.captchas_failed,
        }
    finally:
        client.close()

    assert response.text == "<html>ficha resuelta</html>"
    assert str(response.url) == "https://opac.example/final"
    assert solver.calls[0]["method"] == "GET"
    assert solver.calls[0]["params"] == {"ACC": 101}
    assert solver.calls[0]["cookies"][0].name == "previa"
    assert cookies["sid"] == "nuevo"
    assert user_agent == "FlareSolverr/UA"
    assert metrics == {"captchas": 1, "resueltos": 1, "fallidos": 0}


def test_resuelve_captcha_post_conservando_el_formulario() -> None:
    solver = _FakeSolver(
        FlareSolverrResponse(
            status_code=200,
            text="<html>busqueda resuelta</html>",
            url="https://opac.example/buscar",
        )
    )
    client = _captcha_client(solver)
    try:
        response = client._request(
            "POST",
            "https://opac.example/buscar",
            data={"ACC": "131", "xsqf01": "cine"},
        )
    finally:
        client.close()

    assert response.text == "<html>busqueda resuelta</html>"
    assert solver.calls[0]["method"] == "POST"
    assert solver.calls[0]["data"] == {"ACC": "131", "xsqf01": "cine"}
    assert client.captchas_solved == 1


def test_sin_url_de_flaresolverr_el_captcha_falla(monkeypatch) -> None:
    from mediateca.core.config import settings

    monkeypatch.setattr(settings, "flaresolverr_url", None)
    solver = _FakeSolver()
    client = _captcha_client(solver, url="")
    try:
        with pytest.raises(CaptchaRequired):
            client._request("GET", "https://opac.example/buscar")
    finally:
        client.close()

    assert solver.calls == []
    assert client.captchas == 1
    assert client.captchas_solved == 0
    assert client.captchas_failed == 1


def test_error_de_flaresolverr_falla_sin_bucle() -> None:
    solver = _FakeSolver(error=FlareSolverrError("no disponible"))
    client = _captcha_client(solver)
    try:
        with pytest.raises(CaptchaRequired):
            client._request("GET", "https://opac.example/buscar")
    finally:
        client.close()

    assert len(solver.calls) == 1
    assert client.captchas == 1
    assert client.captchas_solved == 0
    assert client.captchas_failed == 1


def test_respuesta_de_flaresolverr_que_sigue_siendo_captcha() -> None:
    solver = _FakeSolver(
        FlareSolverrResponse(
            status_code=200,
            text="No soy un robot",
            url="https://opac.example/buscar",
        )
    )
    client = _captcha_client(solver)
    try:
        with pytest.raises(CaptchaRequired):
            client._request("GET", "https://opac.example/buscar")
    finally:
        client.close()

    assert len(solver.calls) == 1
    assert client.captchas == 1
    assert client.captchas_solved == 0
    assert client.captchas_failed == 1


def _response_with(text: str) -> httpx.Response:
    return httpx.Response(
        200,
        text=text,
        request=httpx.Request("GET", "https://opac.example/buscar"),
    )


def test_listado_andaluz_con_texto_de_ayuda_no_es_captcha() -> None:
    client = OpacClient(delay=0)
    try:
        client._check_response(_response_with(_andalucia_html("search_results.html")))
        assert client.captchas == 0
    finally:
        client.close()


def test_pagina_con_marcador_de_recaptcha_es_captcha() -> None:
    client = OpacClient(delay=0)
    try:
        with pytest.raises(CaptchaRequired):
            client._check_response(
                _response_with(
                    '<html><body><div class="g-recaptcha" '
                    'data-sitekey="clave"></div></body></html>'
                )
            )
        assert client.captchas == 1
    finally:
        client.close()


def test_pagina_minima_solo_con_la_frase_es_captcha() -> None:
    client = OpacClient(delay=0)
    try:
        with pytest.raises(CaptchaRequired):
            client._check_response(_response_with("No soy un robot"))
        assert client.captchas == 1
    finally:
        client.close()


def test_pagina_de_madrid_sin_captcha_no_cambia_los_contadores(
    search_results_fixture,
) -> None:
    client = OpacClient(delay=0)
    try:
        client._check_response(
            _response_with(search_results_fixture.read_text(encoding="utf-8"))
        )
        assert client.captchas == 0
    finally:
        client.close()


def test_flaresolverr_con_texto_de_ayuda_no_cuenta_como_fallido() -> None:
    solver = _FakeSolver(
        FlareSolverrResponse(
            status_code=200,
            text=_andalucia_html("search_results.html"),
            url="https://www.juntadeandalucia.es/cultura/absys/abnopac/abnetcl.cgi/SESIONANDA/NT2",
        )
    )
    client = _captcha_client(solver)
    try:
        client._request("GET", "https://www.juntadeandalucia.es/cultura/absys/abnopac/abnetcl.cgi/SESIONANDA/NT2")
        metrics = {
            "captchas": client.captchas,
            "resueltos": client.captchas_solved,
            "fallidos": client.captchas_failed,
        }
    finally:
        client.close()

    assert metrics == {"captchas": 1, "resueltos": 1, "fallidos": 0}


def test_descubrimiento_del_fixture_andaluz_crea_stubs_sin_captcha() -> None:
    from mediateca_shared.models import Fuente

    session = _session()
    andalucia = Fuente(
        codigo="andalucia",
        nombre="Andalucía",
        base_url="https://www.juntadeandalucia.es",
        opac_path="/cultura/absys/abnopac/abnetcl.cgi",
        session_pattern=r"/abnetcl\.cgi/([A-Za-z0-9]+)",
        format_field="select03",
        format_value="05",
    )
    session.add(andalucia)
    session.commit()

    listing = _andalucia_html("search_results.html")

    def handler(request: httpx.Request) -> httpx.Response:
        if "SESIONANDA" not in str(request.url):
            return httpx.Response(
                200,
                text=(
                    '<a href="/cultura/absys/abnopac/abnetcl.cgi/'
                    'SESIONANDA/NT1">Inicio</a>'
                ),
            )
        return httpx.Response(200, text=listing)

    client = OpacClient.from_fuente(
        andalucia,
        delay=0,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    try:
        stats = Harvester(
            session, fuente=andalucia, client=client
        ).harvest_discovery(max_pages=1)
    finally:
        client.close()

    assert stats["processed"] == 3
    assert stats["captchas"] == 0
    assert session.scalar(select(func.count(Edicion.id))) == 3
    record_ids = set(session.scalars(select(Edicion.record_id)))
    assert record_ids == {
        "andalucia:2101557",
        "andalucia:2107423",
        "andalucia:2109999",
    }


def test_perfil_opac_andalucia_usa_abnetcl_y_videograbaciones() -> None:
    from mediateca_shared.models import Fuente

    andalucia = Fuente(
        codigo="andalucia",
        nombre="Andalucía",
        base_url="https://www.juntadeandalucia.es",
        opac_path="/cultura/absys/abnopac/abnetcl.cgi",
        session_pattern=r"/abnetcl\.cgi/([A-Za-z0-9]+)",
        format_field="select03",
        format_value="05",
    )
    madrid = Fuente(
        codigo="madrid",
        nombre="Madrid",
        base_url="https://gestiona.comunidad.madrid",
        opac_path="/biblio_publicas/cgi-bin/abnetopac",
        session_pattern=r"/abnetopac/([A-Za-z0-9]+)",
        format_field="select03",
        format_value="6",
    )

    andalucia_client = OpacClient.from_fuente(andalucia)
    madrid_client = OpacClient.from_fuente(madrid)
    override = OpacClient.from_fuente(andalucia, delay=0.5)
    try:
        assert override.delay == 0.5
        assert andalucia_client.base_url == "https://www.juntadeandalucia.es"
        assert andalucia_client.path == "/cultura/absys/abnopac/abnetcl.cgi"
        assert andalucia_client.session_pattern == r"/abnetcl\.cgi/([A-Za-z0-9]+)"
        assert andalucia_client.format_field == "select03"
        assert andalucia_client.format_value == "05"

        andalucia_response = httpx.Response(
            200,
            request=httpx.Request(
                "GET",
                "https://www.juntadeandalucia.es/cultura/absys/abnopac/abnetcl.cgi/SESIONANDA",
            ),
            text="",
        )
        madrid_response = httpx.Response(
            200,
            request=httpx.Request(
                "GET",
                "https://gestiona.comunidad.madrid/biblio_publicas/cgi-bin/abnetopac/SESIONMADRID",
            ),
            text="",
        )
        assert andalucia_client._extract_session(andalucia_response) == "SESIONANDA"
        assert madrid_client._extract_session(madrid_response) == "SESIONMADRID"
        assert andalucia_client._extract_session(madrid_response) is None
        assert madrid_client._extract_session(andalucia_response) is None

        andalucia_client.session_id = "ANDA"
        madrid_client.session_id = "MADRID"
        assert andalucia_client.captchas == madrid_client.captchas == 0
    finally:
        andalucia_client.close()
        madrid_client.close()
        override.close()
