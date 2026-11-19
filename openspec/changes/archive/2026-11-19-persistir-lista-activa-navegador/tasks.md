# Tasks

## 1. Cookie de lista activa

- [x] 1.1 En `apps/web/lib/list-cookie.ts`, sustituir `secure: process.env.NODE_ENV === "production"` por una resolución basada en `MEDITECA_WEB_COOKIE_SECURE` (`auto`, `true`, `false`) y, en `auto`, en `x-forwarded-proto === "https"` leído con `headers()`; verificar que `npm run build` compila y que `npm run lint` no reporta errores.
- [x] 1.2 Revisar que `createListAction`, `toggleFavoriteAction` y `adoptListAction` en `apps/web/app/actions/lists.ts` siguen emitiendo la cookie solo a través de `setActiveListToken`, sin duplicar atributos; verificar con una búsqueda en `apps/web` de escrituras directas de `mediateca_lista` y confirmar que no existen.
- [x] 1.3 Confirmar que la cookie conserva `httpOnly`, `sameSite=lax`, `path=/` y `maxAge` de 180 días, de modo que sea persistente y compartida por pestañas; verificar en las herramientas de desarrollo del navegador que la cookie no es de sesión y que aparece en dos pestañas del mismo perfil.

## 2. Configuración y documentación

- [x] 2.1 Añadir `MEDITECA_WEB_COOKIE_SECURE=auto` a `.env.example` con un comentario que explique `auto`, `true` y `false`; verificar que el archivo sigue siendo un `.env` válido y que la variable aparece documentada.
- [x] 2.2 Pasar la variable al servicio `web` en `docker-compose.yml` y en `deploy/portainer-stack.yml` como `MEDIATECA_WEB_COOKIE_SECURE: ${MEDITECA_WEB_COOKIE_SECURE:-auto}`; verificar con `docker compose config` que el servicio `web` recibe el valor por defecto `auto`.
- [x] 2.3 Actualizar `README.md` en la sección de listas de favoritos y en la de configuración por entorno para indicar que la cookie es persistente, compartida por pestañas y que `Secure` se activa con HTTPS o con `MEDITECA_WEB_COOKIE_SECURE=true`; verificar que los comandos y nombres de variable citados coinciden con el código.

## 3. Verificación funcional

- [x] 3.1 Con el portal servido por HTTP, comprobar en dos pestañas del mismo navegador que guardar un favorito en una pestaña lo muestra como guardado en la otra tras recargar y que ambas abren la misma `/mi-lista`; verificar también que no se crea una lista nueva por pestaña.
- [x] 3.2 Con el portal servido por HTTP, cerrar el navegador y volver a abrirlo; verificar que `/mi-lista` y el recuento de la cabecera restauran la misma lista y que un nuevo favorito se añade a ella.
- [x] 3.3 Simular HTTPS enviando `x-forwarded-proto: https` y comprobar que la cookie se emite con `Secure`; repetir con `MEDITECA_WEB_COOKIE_SECURE=true` sin la cabecera y verificar el mismo resultado, y con `MEDITECA_WEB_COOKIE_SECURE=false` para confirmar que no se marca `Secure`.
- [x] 3.4 Abrir `/lista/{token}` en una pestaña y verificar que la lista adoptada pasa a ser la activa en el resto de pestañas y sigue siéndolo tras reabrir el navegador; comprobar además que una cookie con token inexistente muestra el estado vacío y que el siguiente favorito crea una lista nueva sin error.
- [x] 3.5 Ejecutar `npm run lint` y `npm run build` en `apps/web` y verificar que terminan sin errores.

## Workflow follow-up

- Archivar el cambio cuando la revisión y las verificaciones estén completas.
- Sincronizar las specs principales con los deltas de `listas-compartidas` y `portal-web` al archivar.
