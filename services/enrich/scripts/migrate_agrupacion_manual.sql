-- Agrupacion manual persistente de ediciones en obras.
-- Idempotente: puede ejecutarse varias veces sin error.

ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS obra_manual BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS obra_manual_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE IF EXISTS obras
    ADD COLUMN IF NOT EXISTS manual BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE IF EXISTS obras
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now();

INSERT INTO schema_meta (key, value)
VALUES ('schema_version', '8')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
