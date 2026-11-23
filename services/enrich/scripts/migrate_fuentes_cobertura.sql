-- Alta idempotente de las cinco fuentes de cobertura del CCBIP.
-- Reutilizan el adaptador AbsysNet con descubrimiento por Novedades.
-- Se crean deshabilitadas: se validan y habilitan por oleadas.

INSERT INTO fuentes (
    codigo, nombre, adapter, base_url, opac_path, session_pattern,
    format_field, format_value, enabled, delay, captcha_policy, options
)
VALUES
    (
        'castilla-la-mancha',
        'Red de Bibliotecas Publicas de Castilla-La Mancha',
        'absysnet',
        'https://catalogos.cultura.gob.es',
        '/CCBIP/cgi-ccbip/abnetopac',
        '/abnetopac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "novedades", "coverage": true, "subcat": "BPCLM"}'::json
    ),
    (
        'galicia',
        'Rede de Bibliotecas de Galicia',
        'absysnet',
        'https://catalogos.cultura.gob.es',
        '/CCBIP/cgi-ccbip/abnetopac',
        '/abnetopac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "novedades", "coverage": true, "subcat": "BPGAL"}'::json
    ),
    (
        'cataluna',
        'Biblioteques Publiques de Catalunya (ARGUS)',
        'absysnet',
        'https://catalogos.cultura.gob.es',
        '/CCBIP/cgi-ccbip/abnetopac',
        '/abnetopac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "novedades", "coverage": true, "subcat": "BPCAT"}'::json
    ),
    (
        'baleares',
        'Illes Balears',
        'absysnet',
        'https://catalogos.cultura.gob.es',
        '/CCBIP/cgi-ccbip/abnetopac',
        '/abnetopac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "novedades", "coverage": true, "subcat": "BPEMAO_A"}'::json
    ),
    (
        'canarias',
        'Red de Bibliotecas de Canarias (BICA)',
        'absysnet',
        'https://catalogos.cultura.gob.es',
        '/CCBIP/cgi-ccbip/abnetopac',
        '/abnetopac/([A-Za-z0-9]+)',
        'select03',
        '06',
        false,
        1.0,
        'pause',
        '{"discovery": "novedades", "coverage": true, "subcat": "BPCANA"}'::json
    )
ON CONFLICT (codigo) DO NOTHING;
