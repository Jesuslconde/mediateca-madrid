-- Agrupacion manual de obras: marcas persistentes en edicion y obra.
-- Idempotente: puede ejecutarse varias veces sin error.

ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS obra_manual BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE IF EXISTS ediciones
    ADD COLUMN IF NOT EXISTS obra_manual_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_ediciones_obra_manual
    ON ediciones (obra_manual);

DO $$
BEGIN
    IF to_regclass('obras') IS NOT NULL THEN
        ALTER TABLE obras ADD COLUMN IF NOT EXISTS manual BOOLEAN NOT NULL DEFAULT false;
        ALTER TABLE obras ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();
        CREATE INDEX IF NOT EXISTS ix_obras_manual ON obras (manual);
    END IF;
END
$$;

INSERT INTO schema_meta (key, value)
VALUES ('schema_version', '8')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
