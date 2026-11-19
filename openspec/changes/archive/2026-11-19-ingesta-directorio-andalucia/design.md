# Design

## Context

Ver `proposal.md` para la motivación. La ingesta actual de directorios vive en `services/enrich/src/mediateca/catalog/directory.py` y está acoplada al HTML del Directorio de Madrid: `DirectoryClient` recorre fichas, `ParsedSucursal` transporta los campos y `refresh_sucursales` empareja por `SUBC` contra bibliotecas ya existentes. La tarea `branches` y `refresh-branches` reutilizan ese flujo con `only_known=True`.

Andalucía no tiene inventario OPAC (el catálogo devuelve CAPTCHA y no expone OAI ni SRU), así que no hay bibliotecas conocidas contra las que emparejar. Su directorio abierto sí publica 1126 unidades con dirección, código postal, coordenadas y `SUBC`. El reto es reutilizar el flujo y el modelo `Biblioteca`/`Sucursal` sin romper Madrid.

## Goals / Non-Goals

**Goals:**

- Leer el directorio abierto de Andalucía sin scrapear el OPAC y sin persistir el JSON crudo.
- Crear bibliotecas y sucursales andaluzas con identidad estable y datos normalizados.
- Mantener Madrid y su directorio HTML con el comportamiento actual.
- Reutilizar `branches`, `refresh-branches` y el modelo existente.

**Non-Goals:**

- Recolectar registros bibliográficos o ejemplares andaluces.
- Geocodificar direcciones o deduplicar bibliotecas entre Madrid y Andalucía.
- Persistir contacto, horarios, redes sociales o responsables.
- Cambiar el esquema de PostgreSQL, la API o el índice.

## Decisions

### D1. Configuración del directorio en `fuentes.options`

Se añade una clave estructurada `directory` y se conserva `directory_path` para Madrid:

```json
{
  "directory": {
    "kind": "opendata",
    "url": "https://datos.juntadeandalucia.es/api/v0/libraries/all",
    "format": "json",
    "mode": "create",
    "unit_types": ["Biblioteca"]
  }
}
```

`kind` distingue `html` y `opendata`; `mode` distingue `match` (Madrid) y `create` (Andalucía). Si no hay `directory`, se usa `directory_path` como directorio HTML para no migrar Madrid. Alternativa descartada: una tabla nueva de directorios; añade esquema y migración para dos fuentes.

### D2. Factoría de cliente y lector `opendata`

Se introduce una factoría `build_directory_client(fuente)` que devuelve el cliente adecuado. El cliente HTML actual se mantiene y se añade `OpenDataDirectoryClient`, que implementa el mismo contrato mínimo: `iter_records(...)` devuelve `ParsedSucursal | None`. La descarga es una sola petición JSON, con `User-Agent`, timeout, reintentos con backoff y un retardo de cortesía configurable.

Alternativa descartada: ramificar dentro de `DirectoryClient`. Mezclaría parseo HTML y JSON y haría más frágil el flujo de Madrid.

### D3. Identidad de biblioteca y sucursal

La unidad del directorio se traduce a `ParsedSucursal` con esta regla, derivada del `SUBC`:

| `SUBC` | `biblioteca_codigo` | `sucursal_codigo` |
|---|---|---|
| `CA/CA08/218` | `CA/CA08` | `CA/CA08/218` |
| `RBMALC/BMALC1` | `RBMALC` | `RBMALC/BMALC1` |
| `1432` | `1432` | vacío |
| ausente | `icmsId` | vacío |

Se usa el `SUBC` completo como código de sucursal para garantizar unicidad dentro de la fuente; el código de biblioteca agrupa las sucursales de una misma biblioteca. Para unidades sin `SUBC` se usa `icmsId` como código de biblioteca, de modo que las 331 unidades sin enlace al OPAC también tienen identidad estable. Alternativa descartada: usar solo la última parte como código de sucursal; colisiona entre bibliotecas.

### D4. Modo de creación en `refresh_sucursales`

`refresh_sucursales` recibe `create_missing: bool`. Con `False` conserva el comportamiento actual: omite bibliotecas desconocidas. Con `True` crea la `Biblioteca` que falte y, si la ficha tiene sucursal, la `Sucursal` correspondiente. El trabajo `branches` y la CLI pasan `create_missing = (mode == "create")`.

Al crear una `Biblioteca` se usa el municipio como nombre (o el nombre de la unidad si no hay municipio) y se copia la ubicación de la ficha. Si la ficha tiene sucursal, la ubicación operativa vive en la `Sucursal`; la ubicación de la `Biblioteca` queda como respaldo y no se sobrescribe con cada sucursal.

Alternativa descartada: un trabajo nuevo `directory`. Reutilizar `branches` evita duplicar cola, dashboard y CLI; la diferencia se expresa como política de la fuente.

### D5. Normalización

La normalización vive en el lector `opendata`, antes de construir `ParsedSucursal`:

- `postcode`: entero o cadena; se convierte a cadena y se rellena con ceros a la izquierda hasta cinco dígitos. Si falta o no es válido, queda vacío.
- `latitude` / `longitude`: se sustituye la coma por punto, se parsea a `float` y se valida el rango. Si falta una de las dos o el valor es inválido, ambas quedan vacías.
- `address_name` se guarda como `direccion`; `municipality_name` como `municipio`; `name` como `nombre`.
- `responsable_name`, `email`, `phone`, `fax`, `web`, `horario` y redes sociales se leen pero no se persisten: el modelo no tiene esas columnas y `responsable_name` es dato personal.
- Se detecta `bibliobús` o `móvil` en el nombre para marcar la unidad como móvil y no usar sus coordenadas.

Alternativa descartada: parsear `address_name` para separar calle, código postal y municipio. El formato no es homogéneo y el código postal y el municipio ya vienen en campos propios.

### D6. Filtro y cobertura

El lector filtra por `unit_types`, con `["Biblioteca"]` por defecto. Las unidades excluidas se contabilizan como omitidas. El resumen añade `libraries_created` y `branches_created` a las métricas actuales (`records`, `with_subc`, `with_postal_code`, `with_coordinates`, `branches_matched`, `libraries_updated`, `omitted`, `mobile`).

### D7. Migración

Se añade `services/enrich/scripts/migrate_andalucia_directory.sql`. El runner descubre `migrate_*.sql` por orden alfabético, así que el archivo se aplica con `make migrate` e `init` sin cambiar el runner. La migración hace un merge idempotente sobre `fuentes.options`:

```sql
UPDATE fuentes
SET options = (options::jsonb || '{"directory": {...}}'::jsonb)::json
WHERE codigo = 'andalucia';
```

No toca `enabled`, el perfil OPAC ni ninguna otra fuente. Si la fuente no existiera, la migración no falla y no crea una fuente incompleta.

### D8. Rollback

Para revertir, se puede quitar la clave `directory` de `fuentes.options` o dejar la fuente en `enabled=false`. Las bibliotecas y sucursales creadas se conservan: no hay borrado automático. Si se quisiera limpiar, se eliminarían solo las filas de `fuente=andalucia`, sin tocar ediciones ni ejemplares (que no se crean en este cambio).

## Risks / Trade-offs

- **Cambios en el esquema del dataset** → pruebas de contrato con un fixture JSON y un test que falle si faltan campos clave (`id`, `icmsId`, `name`, `catalogue`).
- **Código postal con tipos mixtos** → normalización explícita y pruebas con entero, cadena con cero inicial y ausente.
- **`SUBC` duplicados** → se usa el `SUBC` completo como código de sucursal y se registra un aviso si se repite; el filtro por defecto excluye los centros de documentación, donde están la mayoría de las colisiones.
- **Bibliotecas creadas sin catálogo** → son filas de directorio, no ediciones; cuando exista un canal OPAC futuro, el emparejamiento por `SUBC` las reutilizará sin duplicar.
- **Cambio de semántica de `branches`** → la política se declara por fuente y se cubre con escenarios y pruebas para `match` y `create`.
- **Datos personales** → `responsable_name` no se persiste; el fixture de pruebas usa datos públicos del dataset y no se guarda el payload crudo.
- **Licencia del dataset** → se documenta la URL de condiciones; el sistema no redistribuye el JSON original.

## Migration Plan

1. Aplicar `make migrate` (o dejar que `init` lo haga) y verificar que `fuentes.options` de `andalucia` contiene `directory`.
2. Ejecutar `make branches fuente=andalucia` (o `refresh-branches --fuente andalucia`) con un límite pequeño y revisar el resumen.
3. Verificar que Madrid conserva sus sucursales y que sus actualizaciones siguen en modo `match`.
4. Ejecutar la actualización completa y comprobar el número de bibliotecas y sucursales andaluzas.

Rollback: retirar la clave `directory`, deshabilitar la fuente o eliminar las filas creadas para `andalucia`. No hay reindexado ni migración de datos históricos.

## Open Questions

Ninguna que bloquee el diseño. La inclusión de centros de documentación queda como opción de configuración y el grado de detalle de contacto queda fuera de esta capacidad.
