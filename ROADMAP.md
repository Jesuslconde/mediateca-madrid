# Roadmap

## M0 · MVP del catálogo de vídeo

Estado: completado (cambio OpenSpec `mvp-catalogo-video`, archivado el 2026-11-09).

- Ingesta del OPAC con sesión y snapshots.
- Modelo obra / edición / ejemplar.
- Parser y detección de DVD / Blu-ray.
- Índice con facetas.
- API REST.
- Portal con búsqueda y ficha.
- Docker Compose.

## M1 · Calidad de datos

- Recolección completa de la colección de vídeo.
- Normalización de idiomas, países y roles.
- Detección de duplicados entre ediciones.
- Informe de cobertura y campos vacíos.

## M2 · Disponibilidad

- Refresco programado por lotes.
- Historial de disponibilidad.
- Comprobación en vivo desde la ficha (opcional).
- Mapa de bibliotecas.

## M3 · Enriquecimiento externo

- Portadas y sinopsis desde TMDb/Filmaffinity/IMDb.
- Enlaces a plataformas legales.
- Valoraciones y datos de reparto adicionales.

## M4 · API pública

- Versionado de API.
- Exportación MARC/JSON.
- Límites de uso y claves.
- Documentación OpenAPI publicada.

## M5 · Escala y operación

- Migración a OpenSearch si el volumen lo exige.
- Almacenamiento S3/MinIO para snapshots.
- Cola distribuida (Redis/RabbitMQ) y workers.
- Métricas, trazas y alertas.
- Despliegue en producción con backups.
