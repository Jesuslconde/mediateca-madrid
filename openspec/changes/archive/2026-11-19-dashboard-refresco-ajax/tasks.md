# Tasks

## 1. Endpoints JSON de datos dinámicos

- [x] 1.1 Añadir serialización JSON de los datos dinámicos de Inicio y Tareas reutilizando las funciones de `dashboard/queries.py` (`worker_health`, `job_status_counts`, `job_type_counts`, `job_fuente_counts`, `catalog_coverage`, `enrichment_percentage`, `ingest_metrics`, `recent_jobs`, `has_active_job`). Verificar que la serialización se puede importar y devuelve dicts con las claves esperadas.
- [x] 1.2 Añadir `GET /api/dashboard/inicio` y `GET /api/dashboard/tareas` en `dashboard/app.py`, capturando `SQLAlchemyError` para responder `{"status": "degraded", "message": ...}` sin trazas. Verificar con `pytest services/enrich/tests/test_dashboard.py` que ambos endpoints responden 200 con JSON.
- [x] 1.3 Añadir tests en `services/enrich/tests/test_dashboard.py` que comprueben: datos de Inicio y Tareas correctos, que los endpoints no modifican trabajos/ediciones, y que con base de datos caída responden `degraded` sin trazas ni detalles de conexión.

## 2. Cliente JavaScript de actualización parcial

- [x] 2.1 En `templates/base.html`, sustituir `<meta http-equiv="refresh">` por un `<script>` inline emitido solo cuando `refresh_seconds` está definido, que inicializa el sondeo en `setInterval`. Verificar que Inicio y Tareas ya no incluyen `http-equiv="refresh"` y que Configuración no incluye el script.
- [x] 2.2 Envolver en `templates/inicio.html` y `templates/tareas.html` las secciones dinámicas en contenedores con `id` estable, y añadir `data-job-type` a los botones de acciones de Tareas para poder habilitar/deshabilitar según `active_jobs`. Verificar que las plantillas renderizan con esos contenedores y atributos.
- [x] 2.3 Implementar en el script el `fetch` del endpoint correspondiente a la `section`, la actualización del DOM (métricas, tabla de trabajos, estado de botones, marca "Actualizado"), un flag `in-flight` contra peticiones solapadas, el render con `textContent` (no `innerHTML`) para el texto de error y el manejo del estado degradado sin recargar. Verificar manualmente en el dashboard y con los tests de plantilla.
- [x] 2.4 Actualizar los tests existentes que asumían el meta-refresh (`test_app_responde_y_muestra_los_datos` y `test_refresco_solo_en_inicio_y_tareas`) para verificar la ausencia de `http-equiv="refresh"` y la presencia del script de actualización parcial.

## 3. Verificación e integración

- [x] 3.1 Ejecutar `make test-enrich` y confirmar que toda la suite de `services/enrich`, incluidos los nuevos tests de endpoints, pasa en verde.
- [x] 3.2 Ejecutar `make lint` (ruff) sobre `services/enrich` y corregir cualquier aviso introducido por el cambio.

## Workflow follow-up

- Archivar el cambio una vez superada la revisión del proyecto.
- Verificar el resultado archivado.
