# Design

## Context

El dashboard es una aplicación FastAPI con plantillas Jinja2 en `services/enrich/src/mediateca/dashboard/`, sin assets estáticos ni tooling de frontend. Hoy el refresco automático se consigue con `<meta http-equiv="refresh">` en `base.html` (véase proposal.md - Why), lo que recarga la página entera. Solo Inicio (`/`) y Tareas (`/tareas`) llevan `refresh_seconds`; Configuración y Catálogo no. Las consultas que producen los datos viven en `queries.py` y ya son funciones puras que reciben una `Session`.

## Goals / Non-Goals

**Goals:**
- Sustituir la recarga completa por una actualización parcial vía endpoint + AJAX que solo traiga los datos dinámicos.
- Reutilizar las consultas existentes (`queries.py`) sin duplicar lógica de negocio.
- Conservar el intervalo configurable, la página degradada sin trazas y el carácter de solo lectura.

**Non-Goals:**
- No se introducen frameworks de frontend ni build de JS.
- No se cambia el comportamiento de Configuración ni de Catálogo.
- No se toca la API pública de ingesta (`/api`) ni `apps/web`.

## Decisions

### 1. Endpoints JSON de solo lectura (en lugar de fragmentos HTML)

Se añaden dos endpoints que devuelven JSON con los datos dinámicos, reutilizando las funciones de `queries.py`:

- `GET /api/dashboard/inicio` → `worker`, `status_counts`, `type_counts`, `fuente_counts`, `coverage`, `enrichment_percent`, `metrics`, `generated_at`.
- `GET /api/dashboard/tareas` → `jobs`, `active_jobs`, `worker_concurrency`, `generated_at`.

Ambos capturan `SQLAlchemyError`, lo registran y responden con `{"status": "degraded", "message": ...}` (HTTP 200, coherente con el comportamiento actual de las páginas) sin exponer trazas.

**Alternativa considerada:** endpoints que devuelven fragmentos HTML parciales y un `innerHTML` swap. Se descarta porque el requisito pide "obtener solo la información que se actualiza" (datos, no HTML) y porque devolver HTML acoplaría el endpoint a la presentación.

### 2. Cliente JavaScript inline en `base.html`

Se elimina `<meta http-equiv="refresh">` y se emite un `<script>` inline solo cuando `refresh_seconds` está definido. El script consulta el endpoint que corresponde a la `section` (Inicio o Tareas) con `setInterval` y actualiza el DOM en su sitio. La marca "Actualizado ..." de la barra superior también se actualiza.

**Alternativa considerada:** servir un fichero `.js` con `StaticFiles`. Se descarta para no añadir infraestructura de estáticos a un dashboard que hoy no la tiene; el script es pequeño y queda autocontenido.

### 3. Secciones dinámicas marcadas con contenedores identificables

En `inicio.html` y `tareas.html` se envuelven las secciones dinámicas en contenedores con `id` estable para que el script las sustituya. En Tareas, los botones de acciones llevan un atributo `data-job-type` para que el script habilite/deshabilite según `active_jobs` (respetando además `is_admin`, que no cambia dentro de una carga de página). Los formularios y sus valores no se reconstruyen, por lo que no se pierden con el refresco.

### 4. Serialización y fechas

Los endpoints serializan las estructuras existentes (`WorkerHealth`, `IngestCoverage`, métricas, `HarvestJob`) a JSON plano. Las fechas se devuelven en ISO-8601 (UTC) y el cliente las formatea con un pequeño helper, o muestra `—` cuando son nulas.

### 5. Escapado de contenido

El cliente construye el DOM de la tabla con APIs seguras (`textContent`) y nunca interpola texto (p. ej. `job.error`) en `innerHTML`, para evitar XSS al reflejar el error de un trabajo.

## Risks / Trade-offs

- **Duplicación de renderizado en JS** (la tabla de trabajos se pinta en el cliente además de en la plantilla) → Se limita a la tabla y a los contadores; la plantilla conserva el renderizado inicial para operadores sin JS.
- **Peticiones solapadas** si el intervalo es menor que la latencia de la respuesta → El script guarda un flag `in-flight` y omite la petición si la anterior no terminó.
- **Regresión de accesibilidad** al actualizar contenido sin anunciarlo → No bloqueante; se deja como mejora futura.
- **Drift entre la plantilla inicial y el render en JS** → Mantener ambos en el mismo cambio y cubrir el render JSON con tests de endpoint.

## Migration Plan

- Sin migración de datos ni de esquema; cambio aditivo (endpoints nuevos, script nuevo).
- Despliegue: reconstruir `services/enrich` y reiniciar el dashboard.
- Rollback: revertir el código; el `<meta http-equiv="refresh">` se restaura y los endpoints nuevos quedan sin consumir.

## Open Questions

Ninguna.
