from __future__ import annotations

from mediateca_shared.models import Edicion, EdicionPersona, Fuente, Persona
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.catalog.indexer import (
    FACET_FIELDS,
    FILTERABLE_ATTRIBUTES,
    MeiliIndexer,
    build_document,
    build_filters,
    iter_documents,
)
from mediateca.catalog.jobs import create_stub
from mediateca.catalog.parser import parse_detail, parse_file
from mediateca.catalog.repository import upsert_edicion
from mediateca.core.db import Base


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_build_document_incluye_bibliotecas_sin_disponibilidad(dvd_fixture) -> None:
    session = _session()
    edicion = upsert_edicion(session, parse_file(str(dvd_fixture)))
    session.commit()

    document = build_document(edicion)

    assert document["ejemplares"] == 2
    assert len(document["bibliotecas"]) == 2
    assert "b:madrid:RBMALC" in document["ubicaciones"]
    assert "s:madrid:BMALC1" in document["ubicaciones"]
    assert "b:madrid:RBMALCO" in document["ubicaciones"]
    assert "s:madrid:BMALCO1" in document["ubicaciones"]
    assert "B.P.M. Cardenal Cisneros" in document["ubicaciones_texto"]
    assert "Biblioteca José Hierro" in document["ubicaciones_texto"]
    assert "disponible" not in document
    assert "estado" not in document


class _FakeIndex:
    def __init__(self) -> None:
        self.documents: dict[str, dict] = {}
        self.batches: list[list[str]] = []

    def add_documents(self, documents, primary_key="id"):
        self.batches.append([document["id"] for document in documents])
        for document in documents:
            self.documents[document["id"]] = document

    def delete_all_documents(self):
        self.documents.clear()


def _fake_indexer() -> tuple[MeiliIndexer, _FakeIndex]:
    index = _FakeIndex()
    indexer = MeiliIndexer.__new__(MeiliIndexer)
    indexer.client = object()
    indexer.index = index
    indexer.ensure_index = lambda: None  # type: ignore[method-assign]
    return indexer, index


def test_detail_complete_distingue_stub_de_ficha_enriquecida(dvd_fixture) -> None:
    session = _session()
    stub = create_stub(session, "123")
    session.commit()

    stub_document = build_document(stub)

    assert stub_document["detail_complete"] is False
    assert stub_document["is_stub"] is True

    edicion = upsert_edicion(session, parse_file(str(dvd_fixture)))
    session.commit()

    complete = build_document(edicion)

    assert complete["detail_complete"] is True
    assert complete["is_stub"] is False


def test_indexador_excluye_ediciones_no_audiovisuales(dvd_fixture) -> None:
    session = _session()
    upsert_edicion(session, parse_file(str(dvd_fixture)))
    non_video = """
    <html><body>
      <span class="js-TITN">1071730</span>
      <span class="doc_title">La épica</span>
      <span class="js-T300a">56 p. ;</span>
    </body></html>
    """
    upsert_edicion(session, parse_detail(non_video))
    session.commit()

    documents = list(iter_documents(session))

    assert [document["record_id"] for document in documents] == ["madrid:2101557"]


def test_index_titns_solo_actualiza_los_titn_indicados(dvd_fixture) -> None:
    session = _session()
    create_stub(session, "1")
    create_stub(session, "2")
    upsert_edicion(session, parse_file(str(dvd_fixture)))
    session.commit()
    indexer, index = _fake_indexer()

    first = indexer.index_titns(session, ["1"])
    second = indexer.index_titns(session, ["2", "2101557"])
    missing = indexer.index_titns(session, ["no-existe"])

    assert first == 1
    assert second == 2
    assert missing == 0
    assert index.batches == [["madrid_1"], ["madrid_2", "madrid_2101557"]]
    assert set(index.documents) == {"madrid_1", "madrid_2", "madrid_2101557"}


def test_index_titns_envia_lotes_de_200() -> None:
    session = _session()
    for number in range(201):
        create_stub(session, f"{number:04d}")
    session.commit()
    indexer, index = _fake_indexer()

    total = indexer.index_titns(session, [f"{number:04d}" for number in range(201)])

    assert total == 201
    assert [len(batch) for batch in index.batches] == [200, 1]


def test_detail_complete_es_un_atributo_filtrable() -> None:
    assert "detail_complete" in FILTERABLE_ATTRIBUTES
    assert "is_stub" in FILTERABLE_ATTRIBUTES


def test_build_document_incluye_paises_origen(dvd_fixture) -> None:
    session = _session()
    edicion = upsert_edicion(session, parse_file(str(dvd_fixture)))
    edicion.paises_origen = ["ES", "FR"]
    session.commit()

    document = build_document(edicion)

    assert document["paises_origen"] == ["ES", "FR"]


def test_build_document_incluye_lista_vacia_para_sin_tmdb() -> None:
    session = _session()
    stub = create_stub(session, "sin-tmdb")
    session.commit()

    assert build_document(stub)["paises_origen"] == []
    assert build_document(stub)["tmdb_poster_url"] is None
    assert build_document(stub)["tmdb_url"] is None


def test_build_document_incluye_portada_y_enlace_de_tmdb(dvd_fixture) -> None:
    session = _session()
    edicion = upsert_edicion(session, parse_file(str(dvd_fixture)))
    edicion.tmdb_poster_url = "https://image.tmdb.org/t/p/w500/poster.jpg"
    edicion.tmdb_url = "https://www.themoviedb.org/movie/10"
    session.commit()

    document = build_document(edicion)

    assert document["tmdb_poster_url"] == "https://image.tmdb.org/t/p/w500/poster.jpg"
    assert document["tmdb_url"] == "https://www.themoviedb.org/movie/10"


def test_faceta_y_filtro_de_paises_origen() -> None:
    assert "paises_origen" in FACET_FIELDS
    assert "paises_origen" in FILTERABLE_ATTRIBUTES

    filters = build_filters(paises_origen=["ES", "FR"])
    assert filters is not None
    assert 'paises_origen = "ES"' in filters
    assert 'paises_origen = "FR"' in filters
    assert " OR " in filters


def test_filtro_de_ubicacion_por_codigo_y_por_nombre() -> None:
    assert "ubicaciones" in FILTERABLE_ATTRIBUTES
    assert "ubicaciones_texto" in FILTERABLE_ATTRIBUTES

    por_codigo = build_filters(biblioteca="s:madrid:BMALC1")
    assert por_codigo == 'ubicaciones = "s:madrid:BMALC1"'

    por_nombre = build_filters(biblioteca="B.P.M. Cardenal Cisneros")
    assert por_nombre == (
        '(bibliotecas = "B.P.M. Cardenal Cisneros" OR '
        'ubicaciones_texto = "B.P.M. Cardenal Cisneros")'
    )


def test_index_reset_reconstruye_paises_origen(dvd_fixture) -> None:
    session = _session()
    edicion = upsert_edicion(session, parse_file(str(dvd_fixture)))
    edicion.paises_origen = ["ES"]
    session.commit()
    indexer, index = _fake_indexer()
    index.documents["antiguo"] = {"id": "antiguo"}

    total = indexer.index_editions(session, reset=True)

    assert total == 1
    assert "antiguo" not in index.documents
    assert index.documents[edicion.record_id.replace(":", "_")]["paises_origen"] == ["ES"]


def test_index_editions_por_fuente_no_reconstruye_documentos() -> None:
    session = _session()
    madrid = Fuente(codigo="madrid", nombre="Madrid", base_url="https://madrid.example")
    andalucia = Fuente(
        codigo="andalucia", nombre="Andalucía", base_url="https://andalucia.example"
    )
    session.add_all([madrid, andalucia])
    session.flush()

    persona = Persona(nombre="Dirección de prueba", nombre_normalizado="direccion de prueba")
    session.add(persona)
    session.flush()

    for fuente in (madrid, andalucia):
        edicion = Edicion(
            fuente_id=fuente.id,
            record_id=f"{fuente.codigo}:1",
            titn="1",
            titulo="Película de prueba",
            personas=[
                EdicionPersona(persona=persona, rol="director", orden=0),
            ],
        )
        session.add(edicion)
    session.commit()

    indexer, index = _fake_indexer()
    total = indexer.index_editions(session, fuente_id=andalucia.id)

    assert total == 1
    assert list(index.documents) == ["andalucia_1"]
    assert index.documents["andalucia_1"]["personas"] == [
        {"nombre": "Dirección de prueba", "rol": "director"}
    ]


def test_build_document_incluye_referencia_de_obra(dvd_fixture) -> None:
    session = _session()
    edicion = upsert_edicion(session, parse_file(str(dvd_fixture)))
    session.commit()

    document = build_document(edicion)

    assert document["obra_id"] == edicion.obra_id
    assert document["obra_key"] == f"obra:{edicion.obra_id}"
    assert document["obra_titulo"] == edicion.obra.titulo_uniforme


def test_build_document_sin_obra_usa_el_record_id() -> None:
    session = _session()
    stub = create_stub(session, "sin-obra")
    session.commit()

    document = build_document(stub)

    assert document["obra_id"] is None
    assert document["obra_key"] == "edicion:madrid:sin-obra"
    assert document["obra_titulo"] is None


def test_referencia_de_obra_es_filtrable() -> None:
    assert "obra_id" in FILTERABLE_ATTRIBUTES
    assert "obra_key" in FILTERABLE_ATTRIBUTES
    assert "obra_titulo" in FILTERABLE_ATTRIBUTES


def test_index_titns_actualiza_solo_las_ediciones_agrupadas() -> None:
    from mediateca_shared.models import Obra

    from mediateca.catalog.grouping import group_editions_into_obra

    session = _session()
    primera = create_stub(session, "1")
    segunda = create_stub(session, "2")
    tercera = create_stub(session, "3")
    obra = Obra(titulo_uniforme="Agrupada", anio=2024, manual=True)
    session.add(obra)
    session.flush()
    group_editions_into_obra(session, [primera, segunda], obra)
    session.commit()

    indexer, index = _fake_indexer()
    index.documents["madrid_3"] = {
        "id": "madrid_3",
        "obra_key": "edicion:madrid:3",
    }

    total = indexer.index_titns(
        session, [primera.record_id, segunda.record_id]
    )

    assert total == 2
    assert index.documents["madrid_1"]["obra_key"] == f"obra:{obra.id}"
    assert index.documents["madrid_2"]["obra_key"] == f"obra:{obra.id}"
    assert index.documents["madrid_3"] == {
        "id": "madrid_3",
        "obra_key": "edicion:madrid:3",
    }
    assert tercera.obra_id is None
