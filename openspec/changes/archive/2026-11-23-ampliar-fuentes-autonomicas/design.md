# Design

## Context

Ver `proposal.md` para la motivación. El estado actual y lo que confirmó el spike:

- `jobs._opac_client` siempre construye `OpacClient.from_fuente(fuente)` y `Harvester` usa el parser AbsysNet (`parse_search_results`, `parse_detail`, cursores `DOC`/`TITN`, `fetch_by_titn`).
- `Fuente` y `FuenteProfile` ya son por fuente: `base_url`, `opac_path`, `session_pattern`, `format_field`, `format_value`, `delay`, `options` y `enabled`.
- El scheduler recorre `enabled_fuentes()` y encola discover/enrich/index por fuente; una fila habilitada entra sola.
- `upsert_edicion` crea bibliotecas a partir de los ejemplares y guarda `sucursal_codigo`/`sucursal_nombre` en el ejemplar. Sin ejemplares, la edición se guarda igual.
- La API serializa `source_url` con `FuenteProfile.source_url(titn)` = `{opac_url}?TITN={titn}`.
- **Spike CCBIP (realizado)**:
  - El formulario de Novedades (`FORM=5`, `xsqf99=1`, `select05=02`, `select03=06`, `subcat`) devuelve videograbaciones y totales grandes: CLM 71.720, Galicia 56.545, Cataluña 48.401, Canarias 43.275, Baleares 11.565; todas las comunidades 429.585. Actualización del CCBIP: junio de 2026.
  - La paginación usa `ACC=161&DOC=N`, la ficha `ACC=165&DOC=N` y el enriquecimiento `?TITN=<titn>&FORM=1`.
  - `parse_search_results` y `parse_detail` actuales funcionan sobre el HTML del CCBIP y devuelven `TITN`, título, año, idioma, país y soportes. La ficha no devuelve ejemplares.
  - La búsqueda `*` no sirve para descubrir: devuelve un subconjunto pequeño (60.773 en todo el catálogo) y `a` devuelve 7,8 millones. El formulario de Novedades es el correcto.
  - La URL permanente está en `<link rel="canonical" href="...?TITN=...">`; el parser actual lee `#xslike` y obtiene `TITN=0`.
  - No hace falta Z39.50 ni FlareSolverr: el `OpacClient` actual, con la forma de petición adecuada, ya funciona.

## Goals / Non-Goals

**Goals:**

- Dar de alta 10 fuentes AbsysNet reutilizando el pipeline actual, sin cambiar el comportamiento de Madrid y Andalucía.
- Cubrir los 5 huecos (CLM, Galicia, Cataluña, Baleares, Canarias) con 5 fuentes de cobertura CCBIP, sin ejemplares.
- Extender el perfil de fuente con un modo de descubrimiento y un modo cobertura, sin adaptadores nuevos.
- Calibrar por fuente el patrón de sesión y el código de vídeo.
- Permitir ediciones sin bibliotecas tenedoras y mostrar su enlace oficial en el portal.

**Non-Goals:**

- Adaptadores para Koha (CLM, Galicia), Sierra (Cataluña, Baleares) u ODA (Canarias).
- Ingestar ejemplares, sucursales o disponibilidad de las fuentes de cobertura.
- Directorio y geolocalización completos para las 10 redes AbsysNet; se añadirán por fuente cuando exista una fuente de datos.
- Frescura o "novedades" del CCBIP; su catálogo tiene desfase.
- Cliente Z39.50, FlareSolverr o migración de esquema.

## Decisions

### D1. Sin adaptador nuevo: extensión del perfil AbsysNet

No se crea un registro de adaptadores. `fuente.adapter` sigue siendo `absysnet` para las 15 fuentes nuevas. Se añaden dos opciones de perfil:

- `options.discovery`: `"avanzada"` (valor actual: `FORM=2`, `xsqf01="*"`, `select03`, `subcat`) o `"novedades"` (CCBIP: `FORM=5`, `xsqf99=1`, `select05=02`, `select03=06`, `subcat`).
- `options.coverage`: `true` en las fuentes de cobertura; no exige ejemplares ni directorio.

`OpacClient.search` elige la forma de la petición según `options.discovery`. El resto del flujo (sesión, paginación, detalle, parser) no cambia. Alternativas descartadas: un adaptador `ccbip` nuevo (el parser actual ya funciona) y Z39.50 (sin cliente disponible y sin necesidad, según el spike).

### D2. Las 10 redes AbsysNet son configuración, no código

Cada red se siembra con `adapter=absysnet`, `options.discovery="avanzada"` y su perfil. El pipeline no cambia. La única incertidumbre es la variante de AbsysNet y el código de vídeo, que se resuelven con calibración y un fixture por red.

Semillas (los patrones marcados "a calibrar" se confirman en el spike S1):

| codigo | base_url | opac_path | session_pattern | select03 |
|---|---|---|---|---|
| aragon | `https://bibliotecas.aragon.es` | `/cgi-bin/opac` | a calibrar | a calibrar |
| asturias | `https://absys.asturias.es` | `/cgi-bin/opacbp` | a calibrar | a calibrar |
| cantabria | `https://slpc.cantabria.es` | `/cgi-bin/abnetopac2` | `/abnetopac2/([A-Za-z0-9]+)` | a calibrar |
| castilla-leon | `https://rabel.jcyl.es` | `/cgi-bin/abnetopac` | `/abnetopac/([A-Za-z0-9]+)` | a calibrar |
| extremadura | `http://catalogo.bibliotecas.juntaex.es` | `/cgi-bin/abnetopac` | `/abnetopac/([A-Za-z0-9]+)` | a calibrar |
| la-rioja | `https://catalogo-blr.larioja.org` | `/cgi-bin/opac` | a calibrar | a calibrar |
| murcia | `https://catalogobrmu.carm.es` | `/cgi-bin/abnetopac/` | `/abnetopac/([A-Za-z0-9]+)` | a calibrar |
| navarra | `https://www.navarra.es` | `/Appsext/opac/abnetcl.exe` | `/abnetcl\.exe/([A-Za-z0-9]+)` | a calibrar |
| pais-vasco | `https://www.katalogoak.euskadi.eus` | `/cgi-bin_q81a/abnetclop` | a calibrar | a calibrar |
| valencia | `https://xlpv.gva.es` | `/cginet-bin/abnetop` | a calibrar | a calibrar |

Asturias y Extremadura no aplican `select03` en la busqueda avanzada; usan el formulario de Novedades (`options.discovery="novedades"`, `select05` y `search_extra` con los campos ocultos del formulario). Murcia usa `options.detail_on_discovery=true` porque su OPAC no resuelve la ficha por `TITN`; el descubrimiento obtiene la ficha desde la URL del listado en la misma sesion. El resto usa `avanzada`.

Se siembran deshabilitadas y se habilitan tras calibrar y validar con un descubrimiento pequeño. Alternativa descartada: habilitarlas todas en la migración por el volumen y el riesgo de bloqueo.

### D3. Fuentes de cobertura CCBIP con 5 fuentes

Cinco filas con `adapter=absysnet`, `base_url=https://catalogos.cultura.gob.es`, `opac_path=/CCBIP/cgi-ccbip/abnetopac`, `session_pattern=/abnetopac/([A-Za-z0-9]+)`, `format_field=select03`, `format_value=06`, `options.discovery="novedades"`, `options.coverage=true` y `options.subcat`:

| codigo | nombre | subcat | vídeos (spike) |
|---|---|---|---|
| castilla-la-mancha | Red de Bibliotecas Públicas de Castilla-La Mancha | `BPCLM` | 71.720 |
| galicia | Rede de Bibliotecas de Galicia | `BPGAL` | 56.545 |
| cataluna | Biblioteques Públiques de Catalunya (ARGUS) | `BPCAT` | 48.401 |
| baleares | Illes Balears | `BPEMAO_A` | 11.565 |
| canarias | Red de Bibliotecas de Canarias (BICA) | `BPCANA` | 43.275 |

Descubrimiento: `POST /NT1?ACC=131` con `FORM=5`, `xsqf99=1`, `START=1`, `xindex=`, `xindty=`, `xindbt=`, `xexact=`, `subcat`, `select05=02`, `select03=06`. Paginación `ACC=161&DOC=N`; ficha `ACC=165&DOC=N`; enriquecimiento `?TITN=<titn>&FORM=1`.

Enlace oficial: se lee `<link rel="canonical">` de la ficha; si no existe, se usa el `?TITN=` del perfil. El `#xslike` actual no es fiable en el CCBIP.

### D4. Modo cobertura

`options.coverage=true` implica: se guardan metadatos y URL, y no se crean ejemplares. `upsert_edicion` ya soporta ediciones sin ejemplares y la lista de bibliotecas queda vacía. El directorio no es obligatorio; el trabajo `branches` no se programa para estas fuentes. No se requiere cambio de esquema.

### D5. Identidad y enlace

Se mantiene `record_id = <fuente>:<titn>` y la unicidad `(fuente_id, titn)`. El `TITN` del CCBIP es numérico y cumple `[A-Za-z0-9._-]` (por ejemplo `18` o `5946466`); no se relaja la validación existente.

### D6. Calibración idempotente

Comando `mediateca calibrate-source --fuente <codigo>`:

1. Abre el OPAC y sigue la redirección de sesión para extraer el patrón real.
2. Lee el formulario avanzado y localiza la opción de videograbaciones en `select03`.
3. Actualiza `session_pattern` y `format_value` de esa fuente.
4. Si no encuentra el código, informa y no modifica el perfil.

Para las fuentes CCBIP fija `06` y el patrón de sesión del OPAC. Alternativa descartada: sembrar los valores a mano por las 10 variantes y el riesgo de error.

### D7. Despliegue por oleadas

Semillas deshabilitadas → calibrar → descubrimiento de validación (`--max-pages 1 --limit N`) → habilitar → indexar esa fuente. Después, la siguiente. Para cobertura: implementar `options.discovery="novedades"` y el modo cobertura → validar una comunidad → habilitar las cinco de una en una. Sin migración destructiva: para revertir basta deshabilitar la fuente y conservar sus datos.

## Risks / Trade-offs

- **Cambio del formulario de Novedades del CCBIP**: el flujo depende de los campos observados (`FORM=5`, `select05=02`, `select03=06`). Mitigación: fixture de la respuesta, test de calibración y validación por comunidad antes de habilitar.
- **Desfase del CCBIP**: actualizado en junio de 2026. Mitigación: documentar la fecha y no usarlo para "novedades"; las 10 redes AbsysNet aportan frescura.
- **URL canónica**: el parser actual obtiene `?TITN=0` de `#xslike`. Mitigación: leer `<link rel="canonical">` y, si falta, construir el `?TITN=` con el `TITN`.
- **Variantes de AbsysNet**: el markup o los campos del formulario pueden diferir. Mitigación: calibración y fixture por red; si una red no encaja, se excluye de la oleada y se documenta.
- **Volumen y bloqueo**: 10 catálogos completos a 1 req/s. Mitigación: habilitación por oleadas, `delay`, límites y scheduler por fuente.
- **Sin ejemplares en cobertura**: el portal no puede filtrar por biblioteca esas fuentes. Es el comportamiento acordado; se compensa con el enlace oficial.
- **Sin directorio en las 10**: no habrá geolocalización; los ejemplares conservan biblioteca y sucursal de la ficha. Se puede añadir directorio por fuente más adelante.

## Migration Plan

1. Añadir las migraciones de semillas idempotentes (`migrate_fuentes_autonomicas.sql` y `migrate_fuentes_cobertura.sql`), sin tocar `SCHEMA_VERSION`.
2. Extender `OpacClient.search` con `options.discovery` y el modo cobertura, manteniendo `"avanzada"` como comportamiento actual.
3. Calibrar y habilitar las 10 fuentes AbsysNet una a una, reindexando cada una.
4. Corregir la URL canónica del parser y validar el descubrimiento de una comunidad CCBIP; habilitar las 5 fuentes una a una.
5. Verificar aislamiento: un fallo de una fuente no altera trabajos ni cursores de otra.
6. Reversión: deshabilitar la fuente afectada; los datos se conservan y no hay migración destructiva.

## Open Questions

Ninguna bloqueante. El spike resolvió la ruta: se reutiliza el `OpacClient` actual con el formulario de Novedades del CCBIP. Queda como trabajo de implementación corregir la URL canónica y añadir el fixture de la respuesta.
