from mediateca_shared.soportes import (
    canonical_soporte,
    detect_soportes,
    soporte_principal,
)


def test_detecta_dvd() -> None:
    assert detect_soportes("1 DVD-Video (ca. 129 min) : son., col. ; 12 cm") == ["DVD"]


def test_detecta_bluray_desde_ejemplar() -> None:
    assert detect_soportes(None, ["Vídeo (Blu-Ray)"]) == ["Blu-ray"]


def test_normaliza_variantes_bluray() -> None:
    assert detect_soportes("1 disco BluRay") == ["Blu-ray"]
    assert detect_soportes("Blu ray + DVD") == ["Blu-ray", "DVD"]


def test_detecta_4k_uhd() -> None:
    assert detect_soportes("1 disco 4K Ultra HD Blu-ray") == ["4K UHD", "Blu-ray"]


def test_excluye_dvd_rom() -> None:
    assert detect_soportes("1 DVD-ROM") == []


def test_canonical_soporte() -> None:
    assert canonical_soporte("Vídeo (DVD)") == "DVD"
    assert canonical_soporte("Vídeo (Blu-Ray)") == "Blu-ray"


def test_soporte_principal() -> None:
    assert soporte_principal(["DVD"]) == "DVD"
    assert soporte_principal(["DVD", "Blu-ray"]) == "Varios"
    assert soporte_principal([]) is None
