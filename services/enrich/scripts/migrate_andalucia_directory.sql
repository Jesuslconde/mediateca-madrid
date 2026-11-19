-- Configuracion del directorio abierto de la fuente Andalucia.
-- Idempotente: se puede ejecutar varias veces sin duplicar la clave.
-- No modifica el perfil OPAC ni los datos de Madrid.

UPDATE fuentes
SET options = (
    options::jsonb || '{"directory": {
        "kind": "opendata",
        "url": "https://datos.juntadeandalucia.es/api/v0/libraries/all",
        "format": "json",
        "mode": "create",
        "unit_types": ["Biblioteca"]
    }}'::jsonb
)::json
WHERE codigo = 'andalucia';
