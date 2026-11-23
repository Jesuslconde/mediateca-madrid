-- Alta idempotente de las diez fuentes AbsysNet autonomicas.
-- Se crean deshabilitadas: se calibran y habilitan por oleadas.
-- No modifica Madrid ni Andalucia.

INSERT INTO fuentes (
    codigo, nombre, adapter, base_url, opac_path, session_pattern,
    format_field, format_value, enabled, delay, captcha_policy, options
)
VALUES
    (
        'aragon',
        'Red de Bibliotecas de Aragon',
        'absysnet',
        'https://bibliotecas.aragon.es',
        '/cgi-bin/opac',
        '/opac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "avanzada"}'::json
    ),
    (
        'asturias',
        'Red de Bibliotecas de Asturias',
        'absysnet',
        'https://absys.asturias.es',
        '/cgi-bin/opacbp',
        '/opacbp/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "novedades", "select05": "00", "search_extra": {"xsoi99": "9", "groupb": "B", "groups": "S", "groupg": "BG", "xstype": "COPI"}}'::json
    ),
    (
        'cantabria',
        'Sistema de Lectura Publica de Cantabria',
        'absysnet',
        'https://slpc.cantabria.es',
        '/cgi-bin/abnetopac2',
        '/abnetopac2/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "avanzada"}'::json
    ),
    (
        'castilla-leon',
        'Red de Bibliotecas de Castilla y Leon (RABEL)',
        'absysnet',
        'https://rabel.jcyl.es',
        '/cgi-bin/abnetopac',
        '/abnetopac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "avanzada"}'::json
    ),
    (
        'extremadura',
        'Red de Bibliotecas de Extremadura',
        'absysnet',
        'https://catalogo.bibliotecas.juntaex.es',
        '/cgi-bin/abnetopac',
        '/abnetopac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "novedades", "select05": "01", "search_extra": {"xsoi99": "9", "groupb": "B", "groups": "S", "groupg": "BG", "xstype": "COPI"}}'::json
    ),
    (
        'la-rioja',
        'Red de Lectura Publica de La Rioja',
        'absysnet',
        'https://catalogo-blr.larioja.org',
        '/cgi-bin/opac',
        '/opac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "avanzada", "verify_tls": false}'::json
    ),
    (
        'murcia',
        'Red de Bibliotecas Publicas de la Region de Murcia',
        'absysnet',
        'https://catalogobrmu.carm.es',
        '/cgi-bin/abnetopac',
        '/abnetopac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "avanzada", "detail_on_discovery": true}'::json
    ),
    (
        'navarra',
        'Red de Bibliotecas Publicas de Navarra',
        'absysnet',
        'https://www.navarra.es',
        '/Appsext/opac/abnetcl.exe',
        '/abnetcl.exe/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "avanzada"}'::json
    ),
    (
        'pais-vasco',
        'Red de Lectura Publica de Euskadi (RLPE)',
        'absysnet',
        'https://www.katalogoak.euskadi.eus',
        '/cgi-bin_q81a/abnetclop',
        '/abnetclop/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "avanzada"}'::json
    ),
    (
        'valencia',
        'Red Electronica de Lectura Publica Valenciana',
        'absysnet',
        'https://xlpv.gva.es',
        '/cginet-bin/abnetop',
        '/abnetop/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "avanzada"}'::json
    )
ON CONFLICT (codigo) DO NOTHING;
