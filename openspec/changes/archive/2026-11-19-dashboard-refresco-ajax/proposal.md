# Proposal

## Why

El dashboard de ingesta recarga hoy la página completa mediante `<meta http-equiv="refresh">` para actualizar Inicio y Tareas. Esto fuerza una petición HTML completa en cada intervalo, interrumpe el estado visual del navegador y vuelve a pintar el menú y los formularios aunque no hayan cambiado. El operador solo necesita que se refresquen los datos que cambian (métricas, cobertura, salud del worker y trabajos recientes).

## What Changes

- Sustituir la recarga completa de página por una actualización parcial mediante un endpoint y una llamada AJAX que solo devuelve la información dinámica de Inicio y Tareas.
- Exponer endpoints JSON de solo lectura para los datos dinámicos de Inicio (`/`) y de Tareas (`/tareas`).
- Añadir un pequeño cliente JavaScript en el dashboard que, en el intervalo configurado, consulta esos endpoints y actualiza en el DOM únicamente las secciones dinámicas y la marca de "Actualizado", sin recargar la página.
- Mantener sin refresco automático las páginas de Configuración y Catálogo, y conservar el intervalo configurable actual (`MEDIATECA_DASHBOARD_REFRESH_SECONDS`).
- Conservar el comportamiento de tolerancia a fallos: si la base de datos no responde, la actualización parcial muestra el estado degradado sin recargar la página.

## Capabilities

### New Capabilities

<!-- Sin capacidades nuevas. -->

### Modified Capabilities

- `dashboard-ingesta`: cambia la forma de refresco automático de Inicio y Tareas, pasando de recarga completa de página a actualización parcial vía endpoint y AJAX.

## Impact

- `services/enrich/src/mediateca/dashboard/app.py`: nuevos endpoints JSON de solo lectura y posible montaje/servicio del script estático.
- `services/enrich/src/mediateca/dashboard/templates/base.html`: sustituir `<meta http-equiv="refresh">` por el script de actualización parcial.
- `services/enrich/src/mediateca/dashboard/templates/inicio.html` y `tareas.html`: marcar las secciones dinámicas con identificadores para poder actualizarlas.
- `services/enrich/src/mediateca/dashboard/queries.py`: reutiliza las consultas existentes para alimentar los endpoints JSON.
- `services/enrich/tests/test_dashboard.py`: nuevos casos para los endpoints JSON y para la ausencia del meta-refresh.
- Sin cambios en la API pública de ingesta (`/api`) ni en `apps/web`.
