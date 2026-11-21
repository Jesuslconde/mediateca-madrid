from mediateca_shared.titles import (
    clean_title,
    split_responsibility,
    strip_all_brackets,
    strip_form_qualifier,
    strip_material_qualifier,
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


def test_quita_calificadores_de_material_conocidos() -> None:
    assert strip_material_qualifier(
        "La cocina fácil de Ferran Adrià [DVD-Vídeo]"
    ) == "La cocina fácil de Ferran Adrià"
    assert strip_material_qualifier(
        "Pilates [DVD-Vídeo] : guía esencial"
    ) == "Pilates : guía esencial"
    assert strip_material_qualifier(
        "La caja [DVD-Vídeo] = [A caixa]"
    ) == "La caja = [A caixa]"
    assert strip_material_qualifier(
        "Curro Jiménez [DVD-Vídeo] [tercera temporada]"
    ) == "Curro Jiménez [tercera temporada]"
    assert strip_material_qualifier(
        "Star Wars [DVD-Vídeo]. Episodio V"
    ) == "Star Wars. Episodio V"
    assert strip_material_qualifier(
        "Atención, pastillas [Archivo de ordenador]"
    ) == "Atención, pastillas"
    assert strip_material_qualifier(
        "La épica [Material gráfico proyectable] /"
    ) == "La épica"


def test_quita_variantes_de_calificadores_de_material() -> None:
    assert strip_material_qualifier("Título [DVD]") == "Título"
    assert strip_material_qualifier("Título [Vídeo]") == "Título"
    assert strip_material_qualifier("Título [video]") == "Título"
    assert strip_material_qualifier("Título [Vídeo-DVD]") == "Título"
    assert strip_material_qualifier("Título [Video DVD]") == "Título"
    assert strip_material_qualifier("Título [DVD-Video]") == "Título"
    assert strip_material_qualifier("Título [DVD-Vídeos]") == "Título"
    assert strip_material_qualifier("Título [Blu-ray]") == "Título"
    assert strip_material_qualifier("Título [Blu-ray disc]") == "Título"
    assert strip_material_qualifier("Título [VHS]") == "Título"
    assert strip_material_qualifier("Título [Videograbación]") == "Título"
    assert strip_material_qualifier("Título [Videograbacíón]") == "Título"
    assert strip_material_qualifier("Título [Grabación sonora]") == "Título"
    assert strip_material_qualifier("Título [Recurso electrónico]") == "Título"
    assert strip_material_qualifier("Título [Disco versátil digital]") == "Título"
    assert strip_material_qualifier("Título [DVD-Vídeo + Grabación sonora]") == "Título"
    assert strip_material_qualifier("Título [Vídeo (DVD)]") == "Título"
    assert strip_material_qualifier("Título [Película : vídeo]") == "Título"
    assert strip_material_qualifier("Título [DVD-BOOK]") == "Título"
    assert strip_material_qualifier("Título [4K UHD]") == "Título"
    assert strip_material_qualifier("Título [DVD-P]") == "Título"
    assert strip_material_qualifier("Título [DVD´S]") == "Título"
    assert strip_material_qualifier("Título [DCD-Vídeo]") == "Título"
    assert strip_material_qualifier("Título [DVD-Víedo]") == "Título"
    assert strip_material_qualifier("Título [DVD-Vído]") == "Título"
    assert strip_material_qualifier("Título [DVD-Víde]") == "Título"
    assert strip_material_qualifier("Título [DVD-Vdeo]") == "Título"
    assert strip_material_qualifier("Título [Blu-ray Dis]") == "Título"
    assert strip_material_qualifier("Título [Videocasetes]") == "Título"
    assert strip_material_qualifier("Título [Videograbacin]") == "Título"
    assert strip_material_qualifier("Título [videojuego]") == "Título"
    assert strip_material_qualifier("Título [(Dvd-Video)]") == "Título"
    assert strip_material_qualifier("Título [Video - Audiovisual]") == "Título"
    assert strip_material_qualifier(
        "[Presentación del libro Atmósferas [DVD] : 100 relatos]"
    ) == "[Presentación del libro Atmósferas : 100 relatos]"


def test_conserva_corchetes_que_no_son_calificador_de_material() -> None:
    for titulo in (
        "[Rec]",
        "[A caixa]",
        "[Rebel without a cause]",
        "Curro Jiménez [tercera temporada]",
        "La década de los 60 (1) [y] (2)",
        "Madrileña bonita [1856-1956]",
        "Diapositivas [sobre la Biblioteca Municipal de Jerez]",
        "[P]",
        "(500) Days of Summer",
        "Título (2020)",
        "Título (Película cinematográfica)",
        "Título (The Child)",
    ):
        assert strip_material_qualifier(titulo) == titulo


def test_quita_calificadores_de_material_entre_parentesis() -> None:
    assert strip_material_qualifier("Lunnis (DVD) Videograbaciones") == "Lunnis"
    assert strip_material_qualifier("La muchacha de Londres (DVD-Video)") == (
        "La muchacha de Londres"
    )
    assert strip_material_qualifier("Frozen (Video): una aventura de Olaf") == (
        "Frozen : una aventura de Olaf"
    )
    assert strip_material_qualifier("El caso O'hara (DVD)") == "El caso O'hara"
    assert strip_material_qualifier("Turandot (videograbación) : Drama lírico") == (
        "Turandot : Drama lírico"
    )
    assert strip_material_qualifier("Curro Lucena (Videograbación-DVD)") == (
        "Curro Lucena"
    )
    assert strip_material_qualifier("El corredor del laberinto (videodisco)") == (
        "El corredor del laberinto"
    )


def test_corrige_corchetes_desbalanceados_y_separadores() -> None:
    assert strip_material_qualifier("La leyenda de Bruce Lee.]") == (
        "La leyenda de Bruce Lee"
    )
    assert strip_material_qualifier("Rebelde sin causa = Goodfellas]") == (
        "Rebelde sin causa = Goodfellas"
    )
    assert strip_material_qualifier(
        "Battlestar galactica [ : temporada uno"
    ) == "Battlestar galactica : temporada uno"
    assert strip_material_qualifier("Los Picapiedra ; ]. Volumen 1") == (
        "Los Picapiedra. Volumen 1"
    )
    assert strip_material_qualifier(
        "Los pitufos. [(Dvd-Video)]. 8, ¡Pitufeando!"
    ) == "Los pitufos. 8, ¡Pitufeando!"
    assert strip_material_qualifier(
        "Bailando con lobos: una historia... de América"
    ) == "Bailando con lobos: una historia... de América"
    assert strip_material_qualifier(
        "La fuerza de uno = ]The power of one"
    ) == "La fuerza de uno = The power of one"


def test_quita_calificador_multimedia() -> None:
    assert strip_material_qualifier(
        "Concierto lírico-coral [Multimedia] : Auditorio Manuel de Falla"
    ) == "Concierto lírico-coral : Auditorio Manuel de Falla"


def test_strip_all_brackets_solo_para_candidatos() -> None:
    assert strip_all_brackets("(500) Days of Summer") == "Days of Summer"
    assert strip_all_brackets("[Rec]") is None
    assert strip_all_brackets(
        "La caja [DVD-Vídeo] = [A caixa]"
    ) == "La caja"
    assert strip_all_brackets(
        "Curro Jiménez [DVD-Vídeo] [tercera temporada]"
    ) == "Curro Jiménez"
