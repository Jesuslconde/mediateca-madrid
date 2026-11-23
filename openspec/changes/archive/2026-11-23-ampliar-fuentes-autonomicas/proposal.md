# Proposal

## Why

El catálogo solo ingesta Madrid y Andalucía, así que el portal deja fuera 15 comunidades autónomas y las 2 ciudades autónomas. Necesitamos ampliar la cobertura de títulos reutilizando el pipeline AbsysNet que ya funciona donde sea posible y una fuente de cobertura para los casos que no encajan, sin asumir disponibilidad física: la comprobación se resuelve con un enlace al catálogo oficial.

## What Changes

- Se dan de alta **10 fuentes AbsysNet por red**, con el mismo adaptador que Madrid y Andalucía: Aragón, Asturias, Cantabria, Castilla y León, Extremadura, La Rioja, Murcia, Navarra, País Vasco y Comunidad Valenciana.
- Cada fuente AbsysNet se calibra por separado: `base_url`, `opac_path`, `session_pattern`, `format_field`/`format_value` (`select03`) y directorio opcional. No se asume que el código de vídeo de Madrid (`6`) o Andalucía (`05`) valga para las demás.
- Se añaden **5 fuentes de cobertura CCBIP**, una por hueco que no sigue AbsysNet: Castilla-La Mancha, Galicia, Cataluña, Baleares y Canarias. Reutilizan el mismo adaptador AbsysNet, con un **modo de descubrimiento "novedades"** y `options.coverage=true`.
- El descubrimiento de cobertura usa el formulario de Novedades del CCBIP (`FORM=5`, `select03=06`, `select05=02`, `subcat`), no la búsqueda `*`. El spike confirmó que el cliente, la paginación y el parser actuales sirven contra el CCBIP.
- Se introduce el modo de fuente **"cobertura"**: una edición puede existir sin ejemplares ni bibliotecas tenedoras. El portal la muestra igualmente con su enlace al catálogo oficial.
- No se añade un adaptador nuevo ni un registro de adaptadores: se extiende el perfil de fuente con el modo de descubrimiento y el modo cobertura. El `adapter=absysnet` de Madrid y Andalucía no cambia.
- Se añade un comando idempotente de calibración por fuente que descubre y guarda el patrón de sesión y el código de formato de vídeo.
- Se mantiene intacto el comportamiento de Madrid y Andalucía.
- **Fuera de alcance**: adaptadores específicos para Koha, Sierra u ODA. Los 5 huecos se cubren vía CCBIP; si el CCBIP no cubriera algún fondo, se valorará un adaptador propio en otro cambio. Tampoco se ingieren ejemplares ni disponibilidad de las fuentes de cobertura, ni se usa Z39.50: el spike demostró que no es necesario.

## Capabilities

### New Capabilities

- Ninguna.

### Modified Capabilities

- `fuentes-opac`: registro de las 10 fuentes AbsysNet y de las 5 fuentes de cobertura; modo de descubrimiento y modo cobertura por fuente; enlace permanente y aislamiento también para fuentes de cobertura.
- `ingesta-catalogo`: descubrimiento por el formulario de Novedades y enriquecimiento sin ejemplares para las fuentes de cobertura; calibración del filtro de formato y del patrón de sesión por fuente.
- `portal-web`: presentación de ediciones de fuentes de cobertura con título, soportes y enlace oficial, aunque no tengan bibliotecas tenedoras.

## Impact

- `services/enrich`: `catalog/fuentes.py`, `catalog/harvester.py`, `catalog/parser.py`, `catalog/jobs.py`, `cli.py`, semillas `scripts/migrate_*.sql` y pruebas.
- `packages/shared`: `FuenteProfile` y el modelo `Fuente` (sin cambios de esquema; `adapter` y `options` ya existen).
- `services/api`: sin cambios de contrato; `source_url` ya se serializa por edición. Posible ajuste de facetas cuando una fuente no tiene bibliotecas.
- `apps/web`: estado vacío de bibliotecas para fuentes de cobertura y enlace al catálogo oficial.
- Infraestructura: sin migración de esquema; las fuentes son filas nuevas y `SCHEMA_VERSION` no cambia. Sin dependencias nuevas: no hace falta cliente Z39.50 ni FlareSolverr para el CCBIP.
