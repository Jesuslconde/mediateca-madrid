from mediateca_shared.soportes import (
    canonical_soporte,
    detect_audiovisual,
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


def test_detecta_material_audiovisual() -> None:
    assert detect_audiovisual("1 DVD-Video (ca. 129 min)") is True
    assert detect_audiovisual(None, ["Vídeo (VHS)"]) is True
    assert detect_audiovisual("1 videocasete sin formato") is True
    assert detect_audiovisual("1 videograbación (90 min)") is True


def test_descarta_material_no_audiovisual() -> None:
    assert detect_audiovisual("56 p. ; 23 cm + 60 diapositivas col.") is False
    assert detect_audiovisual("1 DVD-ROM") is False
    assert detect_audiovisual(None, ["Prestable Libros"]) is False


def test_audiovisual_desconocido_sin_datos() -> None:
    assert detect_audiovisual() is None
    assert detect_audiovisual("", []) is None
