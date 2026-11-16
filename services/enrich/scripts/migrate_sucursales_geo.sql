-- Sucursales y ubicacion de bibliotecas.
-- Idempotente: puede ejecutarse varias veces sin error.

CREATE TABLE IF NOT EXISTS schema_meta (
    key VARCHAR(64) PRIMARY KEY,
    value VARCHAR(64) NOT NULL
);

ALTER TABLE IF EXISTS bibliotecas
    ADD COLUMN IF NOT EXISTS codigo_postal VARCHAR(5);

CREATE TABLE IF NOT EXISTS sucursales (
    id SERIAL PRIMARY KEY,
    biblioteca_id INTEGER NOT NULL REFERENCES bibliotecas (id) ON DELETE CASCADE,
    codigo VARCHAR(64) NOT NULL,
    nombre VARCHAR(500) NOT NULL,
    municipio VARCHAR(250),
    direccion TEXT,
    codigo_postal VARCHAR(5),
    latitud DOUBLE PRECISION,
    longitud DOUBLE PRECISION,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_sucursales_codigo
    ON sucursales (codigo);
CREATE INDEX IF NOT EXISTS ix_sucursales_biblioteca_id
    ON sucursales (biblioteca_id);
CREATE INDEX IF NOT EXISTS ix_sucursales_municipio
    ON sucursales (municipio);
CREATE INDEX IF NOT EXISTS ix_sucursales_codigo_postal
    ON sucursales (codigo_postal);

INSERT INTO schema_meta (key, value)
VALUES ('schema_version', '5')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
