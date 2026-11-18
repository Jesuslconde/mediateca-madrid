-- Listas de favoritos compartidas por enlace.
-- Idempotente: puede ejecutarse varias veces sin error.

CREATE TABLE IF NOT EXISTS listas (
    id UUID PRIMARY KEY,
    token_hash VARCHAR(64) NOT NULL,
    titulo VARCHAR(80) NOT NULL DEFAULT 'Mi lista',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_listas_token_hash
    ON listas (token_hash);
CREATE INDEX IF NOT EXISTS ix_listas_expires_at
    ON listas (expires_at);

CREATE TABLE IF NOT EXISTS lista_items (
    lista_id UUID NOT NULL REFERENCES listas (id) ON DELETE CASCADE,
    titn VARCHAR(32) NOT NULL,
    titulo_snapshot VARCHAR(1000) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    PRIMARY KEY (lista_id, titn)
);

CREATE INDEX IF NOT EXISTS ix_lista_items_lista_added
    ON lista_items (lista_id, added_at);

INSERT INTO schema_meta (key, value)
VALUES ('schema_version', '6')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
