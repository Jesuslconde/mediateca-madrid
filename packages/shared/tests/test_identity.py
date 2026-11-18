from __future__ import annotations

import pytest

from mediateca_shared.identity import (
    RecordIdError,
    compose_record_id,
    normalize_location_code,
    parse_record_id,
)


def test_compone_y_parsea_record_id() -> None:
    assert compose_record_id("madrid", "2101557") == "madrid:2101557"
    assert parse_record_id("madrid:2101557") == ("madrid", "2101557")


def test_titn_suelto_se_resuelve_como_madrid() -> None:
    assert parse_record_id("2101557") == ("madrid", "2101557")


@pytest.mark.parametrize("value", ["", ":", "madrid:", ":123", "Madrid:1", "a:b:c"])
def test_identificador_invalido(value: str) -> None:
    with pytest.raises(RecordIdError):
        parse_record_id(value)


def test_normaliza_codigos_de_ubicacion_historicos() -> None:
    assert normalize_location_code("b:RBMALC") == "b:madrid:RBMALC"
    assert normalize_location_code("s:BMALC1") == "s:madrid:BMALC1"
    assert normalize_location_code("b:madrid:RBMALC") == "b:madrid:RBMALC"
    assert normalize_location_code("B.P.M. Centro") == "B.P.M. Centro"
