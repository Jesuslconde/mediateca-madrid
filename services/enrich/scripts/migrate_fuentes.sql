-- Dimension de fuente OPAC e identidad global de edicion.
-- Idempotente: puede ejecutarse varias veces sin error.

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
CREATE INDEX IF NOT EXISTS ix_fuentes_enabled ON fuentes (enabled);

INSERT INTO fuentes (
    codigo, nombre, adapter, base_url, opac_path, session_pattern,
    format_field, format_value, enabled, delay, captcha_policy, options
)
VALUES (
    'madrid',
    'Madrid',
    'absysnet',
    'https://gestiona.comunidad.madrid',
    '/biblio_publicas/cgi-bin/abnetopac',
    '/abnetopac/([A-Za-z0-9]+)',
    'select03',
    '6',
    true,
    1.0,
    'pause',
    '{"directory_path": "/directorio_publicacion/i18n/comunidades"}'::json
)
ON CONFLICT (codigo) DO NOTHING;

ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS fuente_id INTEGER REFERENCES fuentes (id) ON DELETE RESTRICT;
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS record_id VARCHAR(160);

ALTER TABLE IF EXISTS bibliotecas
    ADD COLUMN IF NOT EXISTS fuente_id INTEGER REFERENCES fuentes (id) ON DELETE RESTRICT;
ALTER TABLE IF EXISTS sucursales
    ADD COLUMN IF NOT EXISTS fuente_id INTEGER REFERENCES fuentes (id) ON DELETE RESTRICT;
ALTER TABLE IF EXISTS ejemplares
    ADD COLUMN IF NOT EXISTS fuente_id INTEGER REFERENCES fuentes (id) ON DELETE RESTRICT;
ALTER TABLE IF EXISTS harvest_jobs
    ADD COLUMN IF NOT EXISTS fuente_id INTEGER REFERENCES fuentes (id) ON DELETE RESTRICT;

-- Backfill: todo el catalogo historico pertenece a Madrid.
UPDATE ediciones
SET fuente_id = (SELECT id FROM fuentes WHERE codigo = 'madrid')
WHERE fuente_id IS NULL;

UPDATE ediciones
SET record_id = 'madrid:' || titn
WHERE record_id IS NULL;

ALTER TABLE IF EXISTS ediciones ALTER COLUMN fuente_id SET NOT NULL;
ALTER TABLE IF EXISTS ediciones ALTER COLUMN record_id SET NOT NULL;

UPDATE bibliotecas
SET fuente_id = (SELECT id FROM fuentes WHERE codigo = 'madrid')
WHERE fuente_id IS NULL;

UPDATE sucursales
SET fuente_id = bibliotecas.fuente_id
FROM bibliotecas
WHERE sucursales.biblioteca_id = bibliotecas.id
  AND sucursales.fuente_id IS NULL;

UPDATE sucursales
SET fuente_id = (SELECT id FROM fuentes WHERE codigo = 'madrid')
WHERE fuente_id IS NULL;

UPDATE ejemplares
SET fuente_id = ediciones.fuente_id
FROM ediciones
WHERE ejemplares.edicion_id = ediciones.id
  AND ejemplares.fuente_id IS NULL;

UPDATE ejemplares
SET fuente_id = (SELECT id FROM fuentes WHERE codigo = 'madrid')
WHERE fuente_id IS NULL;

UPDATE harvest_jobs
SET fuente_id = (SELECT id FROM fuentes WHERE codigo = 'madrid')
WHERE fuente_id IS NULL
  AND job_type <> 'index';

ALTER TABLE IF EXISTS bibliotecas ALTER COLUMN fuente_id SET NOT NULL;
ALTER TABLE IF EXISTS sucursales ALTER COLUMN fuente_id SET NOT NULL;
ALTER TABLE IF EXISTS ejemplares ALTER COLUMN fuente_id SET NOT NULL;

-- Sustituye las unicidades globales por las compuestas por fuente.
ALTER TABLE IF EXISTS ediciones DROP CONSTRAINT IF EXISTS ediciones_titn_key;
ALTER TABLE IF EXISTS bibliotecas DROP CONSTRAINT IF EXISTS bibliotecas_codigo_key;
ALTER TABLE IF EXISTS sucursales DROP CONSTRAINT IF EXISTS sucursales_codigo_key;
ALTER TABLE IF EXISTS ejemplares DROP CONSTRAINT IF EXISTS uq_ejemplar_external_key;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_ediciones_fuente_titn'
          AND conrelid = 'ediciones'::regclass
    ) THEN
        ALTER TABLE ediciones
            ADD CONSTRAINT uq_ediciones_fuente_titn UNIQUE (fuente_id, titn);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_ediciones_record_id'
          AND conrelid = 'ediciones'::regclass
    ) THEN
        ALTER TABLE ediciones
            ADD CONSTRAINT uq_ediciones_record_id UNIQUE (record_id);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_bibliotecas_fuente_codigo'
          AND conrelid = 'bibliotecas'::regclass
    ) THEN
        ALTER TABLE bibliotecas
            ADD CONSTRAINT uq_bibliotecas_fuente_codigo UNIQUE (fuente_id, codigo);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_sucursales_fuente_codigo'
          AND conrelid = 'sucursales'::regclass
    ) THEN
        ALTER TABLE sucursales
            ADD CONSTRAINT uq_sucursales_fuente_codigo UNIQUE (fuente_id, codigo);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_ejemplar_fuente_external_key'
          AND conrelid = 'ejemplares'::regclass
    ) THEN
        ALTER TABLE ejemplares
            ADD CONSTRAINT uq_ejemplar_fuente_external_key
            UNIQUE (fuente_id, external_key);
    END IF;
END
$$;

-- Elimina los indices unicos globales heredados: la unicidad es por fuente.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'ix_bibliotecas_codigo'
          AND indexdef ~ '^CREATE UNIQUE INDEX'
    ) THEN
        DROP INDEX ix_bibliotecas_codigo;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'ix_sucursales_codigo'
          AND indexdef ~ '^CREATE UNIQUE INDEX'
    ) THEN
        DROP INDEX ix_sucursales_codigo;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'ix_ediciones_titn'
          AND indexdef ~ '^CREATE UNIQUE INDEX'
    ) THEN
        DROP INDEX ix_ediciones_titn;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_bibliotecas_codigo ON bibliotecas (codigo);
CREATE INDEX IF NOT EXISTS ix_sucursales_codigo ON sucursales (codigo);
CREATE INDEX IF NOT EXISTS ix_ediciones_titn ON ediciones (titn);

CREATE INDEX IF NOT EXISTS ix_ediciones_fuente_id ON ediciones (fuente_id);
CREATE INDEX IF NOT EXISTS ix_bibliotecas_fuente_id ON bibliotecas (fuente_id);
CREATE INDEX IF NOT EXISTS ix_sucursales_fuente_id ON sucursales (fuente_id);
CREATE INDEX IF NOT EXISTS ix_ejemplares_fuente_id ON ejemplares (fuente_id);
CREATE INDEX IF NOT EXISTS ix_harvest_jobs_fuente_id ON harvest_jobs (fuente_id);
CREATE INDEX IF NOT EXISTS ix_harvest_jobs_fuente_status
    ON harvest_jobs (fuente_id, status);

-- Listas: la identidad del elemento pasa de TITN a record_id.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'lista_items' AND column_name = 'titn'
    ) THEN
        ALTER TABLE lista_items ADD COLUMN IF NOT EXISTS record_id VARCHAR(160);
        UPDATE lista_items
        SET record_id = 'madrid:' || titn
        WHERE record_id IS NULL;
        ALTER TABLE lista_items ALTER COLUMN record_id SET NOT NULL;
        ALTER TABLE lista_items DROP CONSTRAINT IF EXISTS lista_items_pkey;
        ALTER TABLE lista_items
            ADD CONSTRAINT lista_items_pkey PRIMARY KEY (lista_id, record_id);
        ALTER TABLE lista_items DROP COLUMN titn;
    END IF;
END
$$;

INSERT INTO schema_meta (key, value)
VALUES ('schema_version', '7')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
