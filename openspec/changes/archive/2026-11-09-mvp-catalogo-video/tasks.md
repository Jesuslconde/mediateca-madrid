# Tasks

## 1. Estructura y configuración

- [x] 1.1 Crear el monorepo `backend/` + `frontend/` y verificar que `docker compose config` resuelve sin errores
- [x] 1.2 Añadir `pyproject.toml`, dependencias y configuración por entorno, y verificar que el paquete se importa con `python -c "import mediateca"`
- [x] 1.3 Añadir `.env.example`, `.gitignore`, `.dockerignore` y Makefile, y verificar que `make help` lista los comandos

## 2. Modelo de catálogo

- [x] 2.1 Implementar modelos SQLAlchemy de obra, edición, ejemplar, persona, materia, biblioteca y snapshots, y verificar la creación del esquema con `mediateca init-db`
- [x] 2.2 Implementar repositorios de upsert y deduplicación por `TITN`, y verificar con una prueba que dos ejecuciones no duplican registros
- [x] 2.3 Implementar historial de disponibilidad y verificar que un cambio de estado genera una entrada nueva

## 3. Parser y soporte

- [x] 3.1 Implementar el parser de fichas HTML/MARC y verificar con un fixture que extrae título, año, duración, idioma y sinopsis
- [x] 3.2 Implementar la detección de soportes DVD/Blu-ray desde `300$a` y desde el campo `Soporte`, y verificar los casos `DVD-Video`, `Blu-ray` y `Vídeo (Blu-Ray)`
- [x] 3.3 Implementar la extracción de ejemplares por biblioteca/sucursal y verificar signatura, soporte y disponibilidad en el fixture

## 4. Ingesta

- [x] 4.1 Implementar el cliente de sesión del OPAC y verificar que obtiene un identificador de sesión y detecta la caducidad
- [x] 4.2 Implementar la búsqueda paginada por formato `Videos y DVD` y verificar que recorre varias páginas con un límite
- [x] 4.3 Implementar el guardado de snapshots y el comando `harvest`, y verificar que una ficha se puede reprocesar sin red

## 5. Índice y búsqueda

- [x] 5.1 Implementar la creación del índice de Meilisearch con atributos filtrables y ordenables, y verificar con `curl` que el índice existe
- [x] 5.2 Implementar la construcción de documentos y el comando `index`, y verificar que una edición aparece en el índice
- [x] 5.3 Implementar filtros combinados de soporte, género, año, biblioteca, idioma y disponibilidad, y verificar DVD y Blu-ray por separado

## 6. API

- [x] 6.1 Implementar `GET /api/search` con paginación y facetas, y verificar con una petición que devuelve total y `facetDistribution`
- [x] 6.2 Implementar `GET /api/records/{titn}` con ejemplares y personas, y verificar 200 para un `TITN` existente y 404 para uno inexistente
- [x] 6.3 Implementar `GET /api/libraries`, `GET /api/stats` y `GET /health`, y verificar que `/health` comprueba PostgreSQL y Meilisearch

## 7. Portal web

- [x] 7.1 Implementar la página de inicio con buscador y accesos `Solo DVD` / `Solo Blu-ray`, y verificar la navegación
- [x] 7.2 Implementar resultados con facetas combinables y paginación, y verificar que el filtro de soporte se conserva
- [x] 7.3 Implementar la ficha de registro con ejemplares agrupados por biblioteca, y verificar que muestra soporte y disponibilidad

## 8. Docker y operación

- [x] 8.1 Crear los Dockerfiles de backend y frontend y verificar que las imágenes se construyen
- [x] 8.2 Crear `docker-compose.yml` con PostgreSQL, Meilisearch, API, scheduler y frontend, y verificar el arranque completo
- [x] 8.3 Documentar arranque, ingesta, indexación y pruebas en el README, y verificar que los comandos funcionan como se describen

## 9. Verificación final

- [x] 9.1 Ejecutar `pytest` y verificar que pasan las pruebas de soporte, parser y repositorio
- [x] 9.2 Ejecutar una ingesta de prueba limitada y verificar que el portal devuelve resultados con filtro DVD/Blu-ray
- [x] 9.3 Ejecutar `openspec validate mvp-catalogo-video` y verificar que el cambio es válido

## Workflow follow-up

- Archivar el cambio una vez completadas las tareas y revisadas las especificaciones.
