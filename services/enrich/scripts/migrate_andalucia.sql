-- Alta idempotente de la fuente OPAC de Andalucia.
-- No modifica la identidad ni los datos de Madrid.

CREATE TABLE IF NOT EXISTS fuentes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(64) NOT NULL,
    nombre VARCHAR(500) NOT NULL,
    adapter VARCHAR(32) NOT NULL DEFAULT 'absysnet',
    base_url VARCHAR(500) NOT NULL,
    opac_path VARCHAR(500) NOT NULL DEFAULT '',
    session_pattern VARCHAR(500) NOT NULL DEFAULT '/abnetopac/([A-Za-z0-9]+)',
    format_field VARCHAR(64) NOT NULL DEFAULT 'select03',
    format_value VARCHAR(64) NOT NULL DEFAULT '6',
    enabled BOOLEAN NOT NULL DEFAULT true,
    delay DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    captcha_policy VARCHAR(32) NOT NULL DEFAULT 'pause',
    options JSON NOT NULL DEFAULT '{}'::json,
    paused_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fuentes_codigo ON fuentes (codigo);

INSERT INTO fuentes (
    codigo, nombre, adapter, base_url, opac_path, session_pattern,
    format_field, format_value, enabled, delay, captcha_policy, options
)
VALUES (
    'andalucia',
    'Red de Bibliotecas Públicas de Andalucía',
    'absysnet',
    'https://www.juntadeandalucia.es',
    '/cultura/absys/abnopac/abnetcl.cgi',
    '/abnetcl.cgi/([A-Za-z0-9]+)',
    'select03',
    '05',
    true,
    1.0,
    'pause',
    '{}'::json
)
ON CONFLICT (codigo) DO NOTHING;
