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
    assert detect_soportes("1 disco (DVD-ROM) :") == []
    assert detect_soportes("1 disco (CD-ROM) ;") == []
    assert detect_soportes("1 disco (CD-DA)(ca. 109 min.) : DDD ;") == []
    assert detect_soportes("2 cedés ;") == []


def test_detecta_dvd_video_aunque_incluya_dvd_rom() -> None:
    assert detect_soportes("1 disco compacto (DVD-Vídeo y DVD-ROM) :") == ["DVD"]
    assert detect_soportes(
        "12 discos compactos (DVD-Vídeo + DVD-ROM)(ca. 45 min. cada uno) :"
    ) == ["DVD"]


def test_detecta_variantes_andaluzas() -> None:
    assert detect_soportes("1 videodisco (101 min.) :") == ["DVD"]
    assert detect_soportes("1 disco óptico ;") == ["DVD"]
    assert detect_soportes("1 CD-Video ;") == ["DVD"]
    assert detect_soportes("1 disco (Video-CD) :") == ["DVD"]
    assert detect_soportes("1 disco (132 min.) ;") == ["DVD"]
    assert detect_soportes("126 min. :") == ["DVD"]
    assert detect_soportes("1 casete (117 min.) :", tipo_documento="Videograbaciones") == [
        "VHS"
    ]
    assert detect_soportes("1 disco.", tipo_documento="Videograbaciones") == ["DVD"]
    assert detect_soportes("1 disco :", tipo_documento="Videograbaciones") == ["DVD"]
    assert detect_soportes("4 Discos.", tipo_documento="Videograbaciones") == ["DVD"]
    assert detect_soportes("12 discos +", tipo_documento="Videograbaciones") == ["DVD"]


def test_resuelve_soportes_contradictorios() -> None:
    assert detect_soportes("1 videocasete (DVD) (100 min) :") == ["DVD"]
    assert detect_soportes("1 videodisco (Blu-ray) (ca. 95 min.) :") == ["Blu-ray"]
    assert detect_soportes("Blu ray + DVD") == ["Blu-ray", "DVD"]
    assert detect_soportes("1 videocasete VHS + DVD") == ["DVD", "VHS"]


def test_detecta_videocasetes_y_video() -> None:
    assert detect_soportes("1 videocasete (ca. 104 min.) :") == ["VHS"]
    assert detect_soportes("36 vídeocasetes (ca. 60 min.) :") == ["VHS"]
    assert detect_soportes("1 videocassete vVHS) (118 min.) :") == ["VHS"]
    assert detect_soportes("1 Video") == ["VHS"]
    assert detect_soportes("1 vídeo (83 min.) :") == ["VHS"]


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
    assert detect_audiovisual("1 disco (CD-DA)(ca. 109 min.)") is False
    assert detect_audiovisual("80 diapositivas", ["VHS"]) is False
    assert detect_audiovisual("1 DVD-Video + 60 diapositivas") is True


def test_detecta_audiovisual_con_soporte_generico() -> None:
    assert detect_audiovisual("1 disco (132 min.)") is True
    assert detect_audiovisual("1 disco.", None, "Videograbaciones") is True
    assert detect_audiovisual("1 videocasete (BETA)") is True
    assert detect_audiovisual("1 Video") is True


def test_audiovisual_desconocido_sin_datos() -> None:
    assert detect_audiovisual() is None
    assert detect_audiovisual("", []) is None
