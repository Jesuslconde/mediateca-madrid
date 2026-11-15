# Tasks

## 1. Modelo y migración

- [x] 1.1 Añadir `enrich_status`, `enrich_attempts`, `enrich_last_attempt_at`, `enrich_last_error`, `tmdb_status`, `tmdb_attempts`, `tmdb_last_attempt_at` y `tmdb_last_error` a `Edicion` en `packages/shared`, con defaults `pending`/`0`, y verificar con `make test-shared` que el modelo importa y los defaults se aplican
- [x] 1.2 Añadir constantes de estados OPAC y TMDB en `mediateca_shared` y subir `SCHEMA_VERSION` a `4`, verificando con las pruebas de `version.py` que una versión distinta falla y la `4` pasa
- [x] 1.3 Crear `services/enrich/scripts/migrate_enriquecimiento_estado.sql` con columnas `IF NOT EXISTS`, backfill de `enrich_status`/`tmdb_status`, índices y `schema_meta.schema_version='4'`, y verificar ejecutando `make migrate` dos veces sobre PostgreSQL sin error y comprobando columnas y versión
- [x] 1.4 Añadir las nuevas variables al `.env.example` si el cambio introduce configuración (no aplica si no hay ninguna) y verificar que `make test-enrich` sigue pasando

## 2. Persistencia del estado en el harvester

- [x] 2.1 Añadir helpers `record_enrich_success`, `record_enrich_failure` y `record_tmdb_outcome` en `catalog/repository.py`, con tests unitarios de transiciones, incremento de intentos y limpieza de error
- [x] 2.2 Registrar el estado OPAC en `harvest_enrichment`, escribiendo el fallo después del `rollback` con una transacción nueva, y verificar con un test que un fallo deja `enrich_status='failed'`, incrementa intentos y guarda el error
- [x] 2.3 Registrar `matched`, `unmatched`, `error` y `skipped` en `_enrich_tmdb` sin tocar `tmdb_enriched_at` salvo en `matched`, y verificar con tests que `unmatched` no actualiza la fecha ni se confunde con `pending`
- [x] 2.4 Verificar con un test que la selección de pendientes del backfill TMDB y del enriquecimiento OPAC no cambia por las columnas nuevas
- [x] 2.5 Verificar con un test que un éxito posterior a un fallo deja `enriched`/`matched`, conserva el contador de intentos y limpia el último error

## 3. Consultas del catálogo

- [x] 3.1 Crear `dashboard/catalog_queries.py` con un `CatalogFilter` y una consulta base que aplique estado OPAC, estado TMDB, desaparición, texto, soporte, año, idioma y país, y verificar con tests cada filtro por separado
- [x] 3.2 Añadir el filtro por biblioteca con `EXISTS` sobre `ejemplares` y verificar con un test que no duplica filas cuando una edición tiene varios ejemplares en la misma biblioteca
- [x] 3.3 Implementar el resumen por estado OPAC/TMDB, total, desaparecidas y total de coincidencias sobre el mismo filtro, y verificar con tests de catálogo vacío y de filtro combinado
- [x] 3.4 Implementar paginación con `page`, `limit` (tope 200) y orden por `TITN`, y verificar con un test que el total no cambia al cambiar de página y que un `limit` fuera de rango se acota

## 4. Página y navegación

- [x] 4.1 Añadir la ruta `GET /catalogo` y `_catalogo_context` en `dashboard/app.py`, reutilizando `_base_context` con `section='catalogo'`, y verificar con un test que responde 200 y que un fallo de base de datos devuelve la vista degradada
- [x] 4.2 Crear `templates/catalogo.html` con resumen, formulario GET de filtros, tabla de columnas y controles de paginación, y verificar con un test que aparecen los estados, las columnas y el total
- [x] 4.3 Añadir "Catálogo" al menú lateral de `base.html` con la sección activa, y verificar con un test que el enlace aparece en las cuatro páginas y se marca activo en `/catalogo`
- [x] 4.4 Verificar con un test que abrir `/catalogo` y aplicar filtros no crea, modifica ni elimina ediciones, trabajos ni configuración
- [x] 4.5 Verificar con un test que un filtro sin resultados muestra el mensaje vacío y que el resumen queda a cero sin dividir por cero

## 5. Documentación e integración

- [x] 5.1 Documentar en `docs/ARCHITECTURE_ENRICH.md` las columnas de estado, su transición, la página `/catalogo` y la migración a `SCHEMA_VERSION` 4, verificando que el comando `make migrate` descrito coincide con el real
- [x] 5.2 Documentar en `services/enrich/README.md` la página de Catálogo, sus filtros y el significado de `enriched`/`failed`/`unmatched`/`error`/`skipped`
- [x] 5.3 Ejecutar `make test-shared`, `make test-enrich` y `make lint` y corregir cualquier fallo

## Workflow follow-up

- Archivar el cambio cuando la revisión del proyecto esté satisfecha.
- Verificar las specs principales actualizadas tras el archivado.
