from mediateca_shared.titles import (
    clean_title,
    split_responsibility,
    strip_form_qualifier,
)


def test_quita_puntuacion_isdn_final() -> None:
    assert clean_title("La abuela /") == "La abuela"
    assert clean_title("Pintores y reyes del Prado :") == "Pintores y reyes del Prado"
    assert clean_title("Best Seller ;") == "Best Seller"
    assert clean_title("Cancionero de Castilla ,") == "Cancionero de Castilla"
    assert clean_title("Título.") == "Título"
    assert clean_title("Ángel =") == "Ángel"


def test_conserva_signos_del_titulo() -> None:
    assert clean_title("¿Qué pasa?") == "¿Qué pasa?"
    assert clean_title("¡Viva!") == "¡Viva!"
    assert clean_title("Título [DVD]") == "Título [DVD]"
    assert clean_title("Título (2020)") == "Título (2020)"


def test_normaliza_espacios_y_caracteres_invisibles() -> None:
    assert clean_title("  La   abuela  ") == "La abuela"
    assert clean_title("La\u00a0abuela") == "La abuela"
    assert clean_title("La\u200babuela") == "La abuela"
    assert clean_title("La\u00adabuela") == "La abuela"


def test_quita_calificadores_de_forma() -> None:
    assert strip_form_qualifier("Un amor (Película cinematográfica)") == "Un amor"
    assert (
        strip_form_qualifier("Mediterraneo (Película cinematográfica : 2021)")
        == "Mediterraneo"
    )
    assert strip_form_qualifier("Angel (Película cinematográfica: 1937)") == "Angel"
    assert (
        strip_form_qualifier("The Prado Museum. A Collection of Wonders (Documental)")
        == "The Prado Museum. A Collection of Wonders"
    )


def test_conserva_parentesis_que_no_son_calificador() -> None:
    assert strip_form_qualifier("Título (2020)") == "Título (2020)"
    assert strip_form_qualifier("Título (versión del director)") == (
        "Título (versión del director)"
    )


def test_separa_responsabilidad_con_y_sin_espacio() -> None:
    assert split_responsibility("20.000 especies de abejas / dirección") == (
        "20.000 especies de abejas"
    )
    assert split_responsibility("Alfredo el Grande /Marcos Ordóñez") == (
        "Alfredo el Grande"
    )
    assert split_responsibility("AC/DC") == "AC/DC"
    assert split_responsibility(None) is None


def test_titulo_vacio() -> None:
    assert clean_title(None) is None
    assert clean_title("   ") is None
    assert clean_title(" / ") is None
