# Proposal

## Why

El catálogo de las Bibliotecas Públicas de la Comunidad de Madrid (AbsysNet) permite consultar vídeos y DVD, pero no ofrece una API pública ni facetas que distingan DVD de Blu-ray, director, reparto, duración, edad recomendada o disponibilidad por biblioteca. Esto obliga a repetir búsquedas manuales y limita la reutilización de los metadatos.

## What Changes

- Añadir una canalización de ingesta que recorre el OPAC, mantiene sesión, respeta el rate limit y guarda snapshots HTML/MARC para reprocesar.
- Normalizar los registros en un modelo de obra, edición y ejemplar, separando soportes (DVD, Blu-ray, 4K UHD, VHS) y disponibilidad por biblioteca.
- Crear un índice de búsqueda con facetas por soporte, género, año, idioma, país, biblioteca y disponibilidad.
- Exponer una API REST para búsqueda, facetas, ficha de registro y bibliotecas.
- Construir un portal web con buscador, filtros de soporte y ficha de detalle con ejemplares.
- Empaquetar todo en Docker Compose (PostgreSQL, Meilisearch, API, scheduler y frontend).

## Capabilities

### New Capabilities

- `ingesta-catalogo`: recolección del OPAC, gestión de sesión, paginación, límites y snapshots.
- `modelo-catalogo`: modelo obra/edición/ejemplar, normalización y deduplicación.
- `busqueda-facetas`: índice de búsqueda, ranking y facetas.
- `filtro-soporte`: detección y filtrado normalizado de DVD, Blu-ray y otros soportes.
- `api-portal`: API REST para el portal alternativo.
- `portal-web`: interfaz de búsqueda y ficha de registro.
- `operacion-despliegue`: Docker Compose, configuración, arranque y verificación.

### Modified Capabilities

Ninguna.

## Impact

- Nuevo backend Python (FastAPI, SQLAlchemy, httpx, BeautifulSoup) y frontend Next.js.
- Nuevas dependencias: PostgreSQL 16, Meilisearch, Docker Compose.
- La ingesta depende de la estructura HTML de AbsysNet; cambios en el OPAC pueden romper los selectores.
- No se accede a datos personales: solo metadatos públicos del catálogo.
