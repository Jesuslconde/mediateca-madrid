# Proposal

## Why

La lista activa de favoritos se pierde en el despliegue actual: la cookie `mediateca_lista` se marca como `Secure` siempre que `NODE_ENV=production`, pero el portal se publica por HTTP sin TLS ni proxy inverso. El navegador rechaza esa cookie, de modo que cada petición parece no tener lista, varias pestañas no comparten estado y al cerrar el navegador no se restaura nada. El resultado contradice el contrato de `listas-compartidas`, que promete recordar la lista activa del navegador.

## What Changes

- Corregir la emisión de la cookie de lista activa para que funcione en el despliegue HTTP actual y siga siendo `Secure` cuando el portal se sirva por HTTPS.
- Mantener una única lista activa compartida por todas las pestañas del navegador (sin listas independientes por pestaña).
- Convertir la cookie de lista activa en persistente más allá del cierre del navegador, conservando su `maxAge` y restaurando la última lista creada o adoptada en ese navegador.
- No cambiar el modelo de datos ni la API: la lista sigue viviendo en PostgreSQL y la URL `/lista/{token}` sigue siendo la credencial.
- Documentar la nueva variable de entorno de seguridad de cookies y su valor recomendado por escenario de despliegue.
- Verificar el comportamiento multi-pestaña y de reapertura del navegador, incluido el caso de una cookie caducada o apuntando a una lista eliminada.

Fuera de alcance:

- Listas independientes por pestaña, sincronización en tiempo real entre pestañas o notificaciones de cambio.
- Cuentas, sesiones de usuario, recuperación de listas por correo o datos personales.
- Cambiar el formato del token, la caducidad del servidor o los límites de la API.
- Añadir almacenamiento local del token como alternativa a la cookie.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `listas-compartidas`: la lista activa por navegador pasa a exigir una cookie persistente que sobreviva al cierre del navegador y que funcione con el despliegue HTTP actual, compartida por todas las pestañas.
- `portal-web`: la página Mi lista, el acceso en cabecera y la adopción de listas compartidas deben tratar la lista activa persistente como estado compartido entre pestañas y restaurado al reabrir el navegador.

## Impact

- `apps/web/lib/list-cookie.ts`: cálculo del atributo `Secure` según la petición y la configuración, en lugar de `NODE_ENV`.
- `apps/web/app/actions/lists.ts`, `apps/web/lib/active-list.ts` y las páginas `/mi-lista` y `/lista/[token]`: sin cambios de contrato, pero sí verificación de que todas las rutas que fijan la lista activa emiten la cookie corregida.
- `.env.example`, `docker-compose.yml`, `deploy/portainer-stack.yml` y `README.md`: nueva variable de entorno y nota operativa sobre HTTPS.
- `openspec/specs/listas-compartidas` y `openspec/specs/portal-web`: deltas de comportamiento.
- Sin cambios en `packages/shared`, `services/api`, `services/enrich`, migraciones ni contratos OpenAPI.
