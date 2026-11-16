# Tasks

## 1. Modelo compartido y migración

- [x] 1.1 Añadir `Sucursal` y `Biblioteca.codigo_postal` en `packages/shared/src/mediateca_shared/models.py`; verificar con `python -c "from mediateca_shared.models import Sucursal, Biblioteca"` y `make test-enrich`.
- [x] 1.2 Añadir `UbicacionOut` y `EjemplarOut.ubicacion` en `packages/shared/src/mediateca_shared/schemas.py`; verificar la importación y la validación con un ejemplar de prueba.
- [x] 1.3 Añadir la relación viewonly `Ejemplar.sucursal` por `sucursal_codigo` y cargarla con `selectinload`; verificar el mapeo y una consulta en SQLite.
- [x] 1.4 Crear `services/enrich/scripts/migrate_sucursales_geo.sql` y subir `SCHEMA_VERSION` a `5`; verificar que `make migrate` es idempotente y que `schema_meta.schema_version` queda en `5`.
- [x] 1.5 Añadir pruebas de modelo para código único, CP sin coordenadas, duplicado y resolución por código; verificar `make test-enrich`.
- [x] 1.6 Documentar la tabla `sucursales`, la columna `codigo_postal` y la versión 5 en `docs/ARCHITECTURE.md`; verificar que la sección existe y coincide con el modelo.

## 2. Ingesta del directorio

- [x] 2.1 Crear `services/enrich/src/mediateca/catalog/directory.py` con parser de listado y de ficha; añadir fixtures con `ll=`, sin `ll=`, sin `SUBC`, cerrada y móvil; verificar las pruebas del parser.
- [x] 2.2 Implementar el cliente paginado del directorio con retardo, límite y reintentos; verificar con HTTP simulado o fixture y `make test-enrich`.
- [x] 2.3 Implementar `upsert_sucursal` idempotente, sin borrar ausentes y sin pisar coordenadas existentes con valores vacíos; verificar con una prueba SQLite de reproceso.
- [x] 2.4 Añadir el comando `mediateca refresh-branches` con resumen de cobertura; verificar `--help` y una ejecución con `--limit` sobre fixture o mock.
- [x] 2.5 Añadir el objetivo `make branches` y la sección correspondiente en `README.md`; verificar que el objetivo aparece en `make help` y que el comando documentado funciona.
- [x] 2.6 Añadir pruebas de omisión de fichas sin `SUBC`, cerradas, móviles y de biblioteca desconocida, y del resumen de cobertura; verificar `make test-enrich`.

## 3. API de ubicación

- [x] 3.1 Implementar `ubicacion` en `serialize_record` con la precedencia sucursal → biblioteca → `null`; verificar los cuatro casos con pruebas del serializador.
- [x] 3.2 Cargar `Ejemplar.sucursal` con `selectinload` en `services/api/src/mediateca/api/routers/records.py`; verificar que la ficha no hace consultas por ejemplar y que pasan los tests de API.
- [x] 3.3 Reexportar `UbicacionOut` en `services/api/src/mediateca/api/schemas.py` y comprobar el esquema OpenAPI; verificar que `ubicacion` aparece como campo opcional.
- [x] 3.4 Regenerar contrato y tipos con `make contracts`; verificar `contracts/openapi.json` y `apps/web/lib/api-types.ts`.
- [x] 3.5 Añadir pruebas de API para sucursal con coordenadas, CP sin coordenadas, fallback a biblioteca y ejemplar sin ubicación; verificar `make test-api`.
- [x] 3.6 Documentar el campo `ubicacion` en README y en las notas del contrato; verificar que el ejemplo coincide con una respuesta real de la API.

## 4. Datos de códigos postales

- [x] 4.1 Crear `scripts/generate_codigos_postales.py` para descargar, unir y filtrar las fuentes de centroides y municipios, y escribir el JSON; verificar que genera 304 entradas.
- [x] 4.2 Añadir `apps/web/lib/codigos-postales-madrid.json` con fuente y licencia; verificar que el JSON es válido y que contiene 28015 y 28801 con centroide y municipio.
- [x] 4.3 Documentar las fuentes y la atribución en `README.md` y en la nota de la ficha; verificar que el texto de licencia y la atribución son visibles.
- [x] 4.4 Añadir al README el comando reproducible de generación y comprobación del JSON; verificar que el comando documentado termina sin errores.

## 5. Portal: selector y orden por cercanía

- [x] 5.1 Crear `apps/web/lib/geo.ts` con `haversineKm` y `formatDistance`; verificar con `npm run build` y una muestra de cálculo 28015 → 28801.
- [x] 5.2 Convertir `LibrariesTable` en componente cliente y agrupar por `biblioteca_codigo` y `sucursal_codigo`; verificar `npm run build` y que la tabla mantiene los datos y el enlace al OPAC.
- [x] 5.3 Añadir el selector de código postal, la persistencia en `localStorage` y la acción de limpiar; verificar `npm run build` y que no se solicita geolocalización.
- [x] 5.4 Añadir el cálculo de distancia, el orden por cercanía y el fallback al centroide del CP; verificar QA manual con una ficha de Madrid y Alcalá.
- [x] 5.5 Añadir los estados de CP desconocido, sucursales sin ubicación y ninguna ubicación disponible, con aviso y orden alfabético; verificar QA manual.
- [x] 5.6 Añadir accesibilidad (etiqueta, teclado, `aria-live`) y la nota de atribución de códigos postales; verificar navegación por teclado y texto visible.
- [x] 5.7 Actualizar la ficha y el README con el comportamiento de ordenación; verificar que la documentación coincide con la UI.

## 6. Integración y despliegue

- [x] 6.1 Ejecutar `make migrate` y verificar la tabla `sucursales`, la columna `bibliotecas.codigo_postal` y `schema_meta.schema_version = 5`.
- [x] 6.2 Ejecutar `make branches` y verificar el resumen de cobertura y las filas resultantes en `sucursales`.
- [x] 6.3 Ejecutar `make contracts`, `make test`, `make lint` y `npm run build`; verificar que todas las comprobaciones pasan.
- [x] 6.4 Verificar en el portal una ficha con sucursales de Madrid y Alcalá: orden por CP, distancias, persistencia, limpiar, aviso sin ubicación y ausencia de petición de geolocalización.
- [x] 6.5 Revisar el rollback documentado (revertir imágenes y devolver `schema_meta.schema_version` a `4`) y verificar que las migraciones son aditivas.

## Workflow follow-up

- Archivar el cambio después de la revisión y verificación.
- Verificar el resultado archivado y las specs sincronizadas.
