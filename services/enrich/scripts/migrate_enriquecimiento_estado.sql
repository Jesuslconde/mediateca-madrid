-- Estado de enriquecimiento por edicion: resultado OPAC y TMDB persistido.
-- Idempotente: puede ejecutarse varias veces sin error.

CREATE TABLE IF NOT EXISTS schema_meta (
    key VARCHAR(64) PRIMARY KEY,
    value VARCHAR(64) NOT NULL
);

ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS enrich_status VARCHAR(16) NOT NULL DEFAULT 'pending';
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS enrich_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS enrich_last_attempt_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS enrich_last_error TEXT;
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS tmdb_status VARCHAR(16) NOT NULL DEFAULT 'pending';
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS tmdb_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS tmdb_last_attempt_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS tmdb_last_error TEXT;

-- Backfill: las fichas ya descargadas cuentan como enriquecidas por el OPAC
-- y las ya sincronizadas con TMDB como emparejadas.
UPDATE ediciones
SET enrich_status = 'enriched'
WHERE detail_fetched_at IS NOT NULL
  AND enrich_status = 'pending';

UPDATE ediciones
SET tmdb_status = 'matched'
WHERE tmdb_enriched_at IS NOT NULL
  AND tmdb_status = 'pending';

CREATE INDEX IF NOT EXISTS ix_ediciones_enrich_status
    ON ediciones (enrich_status);
CREATE INDEX IF NOT EXISTS ix_ediciones_tmdb_status
    ON ediciones (tmdb_status);
CREATE INDEX IF NOT EXISTS ix_ediciones_enrich_status_titn
    ON ediciones (enrich_status, titn);
CREATE INDEX IF NOT EXISTS ix_ediciones_tmdb_status_titn
    ON ediciones (tmdb_status, titn);

INSERT INTO schema_meta (key, value)
VALUES ('schema_version', '4')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
