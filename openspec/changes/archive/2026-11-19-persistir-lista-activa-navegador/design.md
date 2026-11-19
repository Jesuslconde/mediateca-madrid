# Design

## Context

Ver `proposal.md` para la motivación y `specs/listas-compartidas/spec.md` y `specs/portal-web/spec.md` para el contrato de comportamiento.

El estado actual que condiciona el diseño:

- `apps/web` es Next.js 15 con App Router. La lista activa se resuelve en componentes de servidor leyendo la cookie `mediateca_lista` y las mutaciones se ejecutan como Server Actions.
- `apps/web/lib/list-cookie.ts` fija `secure: process.env.NODE_ENV === "production"`. El contenedor `mediateca-web` se construye con `NODE_ENV=production` y se publica por HTTP en `${WEB_PORT:-3000}`, sin proxy inverso ni TLS dentro del stack.
- La lista en sí vive en PostgreSQL y su token viaja en la URL `/lista/{token}`. La cookie solo recuerda qué lista es la activa.
- La cookie ya usa `httpOnly`, `sameSite=lax`, `path=/` y `maxAge` de 180 días. El problema no es su duración declarada, sino que el navegador la rechaza cuando lleva `Secure` sobre HTTP.
- No existe runner de pruebas en `apps/web`; la verificación disponible es `npm run lint`, `npm run build` y pruebas manuales contra el stack.

## Goals / Non-Goals

**Goals:**

- Hacer que la cookie de lista activa se acepte en el despliegue HTTP actual y siga siendo `Secure` cuando haya TLS.
- Mantener una única lista activa por navegador, compartida por todas las pestañas.
- Conservar la lista activa al cerrar y reabrir el navegador dentro del plazo de persistencia.
- Dejar la seguridad de la cookie configurable por entorno para cubrir proxies y despliegues con TLS.
- No cambiar el contrato de la API ni el modelo de datos.

**Non-Goals:**

- Listas independientes por pestaña o adopción aislada por pestaña.
- Sincronización en vivo entre pestañas (BroadcastChannel, polling o WebSocket).
- Guardar el token en `localStorage` o exponerlo a JavaScript.
- Cambiar la caducidad del servidor, el formato del token o los límites de creación.
- Resolver la carrera de creación cuando dos pestañas pulsan su primer favorito exactamente a la vez más allá de lo que ya limita la API.

## Decisions

### 1. `Secure` según la petición, con anulación por entorno

La emisión de la cookie pasa a decidir `Secure` así:

- Si `MEDITECA_WEB_COOKIE_SECURE` vale `true`, se fuerza `Secure`.
- Si vale `false`, nunca se marca `Secure`.
- Si vale `auto` (por defecto), se marca `Secure` solo cuando la petición llega por HTTPS, según `x-forwarded-proto` o el protocolo de la URL.

El valor por defecto `auto` mantiene funcionando el stack actual por HTTP y activa `Secure` automáticamente detrás de un proxy que reenvíe `x-forwarded-proto: https`. La variable permite corregir despliegues donde el proxy no reenvía esa cabecera.

Alternativas descartadas:

- **Seguir usando `NODE_ENV`**: es la causa del fallo; `production` no implica HTTPS en este stack.
- **No marcar nunca `Secure`**: funciona por HTTP, pero degrada la seguridad en despliegues con TLS.
- **Marcar siempre `Secure`**: rompe el despliegue HTTP documentado.
- **Deducir solo de `x-forwarded-proto`**: no cubre el caso de TLS terminado sin cabecera reenviada; la variable de entorno da una salida explícita.

### 2. Cookie persistente y compartida, no almacenamiento por pestaña

Se mantiene una cookie de primera parte con `httpOnly`, `sameSite=lax`, `path=/` y `maxAge` de 180 días. Al no ser una cookie de sesión, el navegador la conserva al cerrarse y la reenvía en todas las pestañas del mismo perfil, que es exactamente el comportamiento pedido: una sola lista activa compartida por pestañas y restaurada al reabrir.

Alternativas descartadas:

- **`sessionStorage`**: es por pestaña y se borra al cerrar el navegador; rompe ambos requisitos.
- **`localStorage`**: se comparte entre pestañas y persiste, pero no está disponible en componentes de servidor ni en Server Actions sin duplicar el estado en cliente, y expone el token a JavaScript.
- **Cookie de sesión sin `maxAge`**: no sobrevive al cierre del navegador.

### 3. Un único punto de emisión y mismos atributos en todos los caminos

Todas las rutas que fijan la lista activa (`createListAction`, `toggleFavoriteAction` al crear, `adoptListAction`) siguen usando el helper de `list-cookie.ts`, de modo que el arreglo se aplica una sola vez. No se añaden cookies nuevas ni se duplica el token en otros almacenes.

Consecuencias observables:

- Al guardar el primer favorito desde cualquier pestaña, la cookie queda aceptada y las demás pestañas ven la misma lista en su siguiente petición.
- Al abrir `/lista/{token}`, la adopción afecta a todo el navegador, no solo a la pestaña que abrió el enlace.
- Al reabrir el navegador, la cookie sigue presente y `/mi-lista` y la cabecera muestran la lista anterior.

### 4. Sin sincronización en vivo entre pestañas

Las pestañas comparten la cookie, pero no reciben eventos de cambio. Una pestaña abierta antes de una mutación en otra refleja el nuevo estado al recargar o navegar. Se descarta añadir `BroadcastChannel` o polling porque el requisito es compartir la lista activa, no propagar cambios en tiempo real, y la lista ya se relee en cada navegación.

### 5. Verificación sin nuevo framework de pruebas

`apps/web` no tiene runner de pruebas. Se verificará con `npm run lint`, `npm run build` y una comprobación manual guiada de los escenarios de las specs: dos pestañas, cierre y reapertura, HTTP y HTTPS simulado con `x-forwarded-proto`. No se introduce Vitest ni Playwright en este cambio.

## Risks / Trade-offs

- **Proxy sin `x-forwarded-proto`** → En `auto` la cookie no se marcaría `Secure` aunque el sitio sea HTTPS. Mitigación: documentar `MEDITECA_WEB_COOKIE_SECURE=true` para esos despliegues.
- **Navegadores con cookies de terceros o de sitio bloqueadas** → La lista activa no se recuerda. Mitigación: queda como limitación conocida; no se añade respaldo en `localStorage` para no exponer el token.
- **Carrera al primer favorito en dos pestañas nuevas** → Podrían crearse dos listas y prevalecer la última cookie. Mitigación: la ventana es mínima, la lista anterior no se pierde y sigue accesible por su URL; el límite de creación de la API evita abusos.
- **Caducidad de la cookie y de la lista** → Ambas usan 180 días. Si el usuario solo lee durante ese plazo, tanto la cookie como la lista pueden caducar. Mitigación: el plazo ya está documentado y el siguiente favorito crea una lista nueva sin error.

## Migration Plan

1. Desplegar la nueva imagen `mediateca-web`. No hay migración de datos ni cambios de esquema.
2. Sin configurar nada, `MEDITECA_WEB_COOKIE_SECURE=auto` mantiene el comportamiento por HTTP y activa `Secure` si el proxy informa HTTPS.
3. En despliegues con TLS donde el proxy no reenvíe `x-forwarded-proto`, definir `MEDITECA_WEB_COOKIE_SECURE=true`.
4. Para volver atrás basta con desplegar la imagen anterior; las cookies ya emitidas siguen siendo válidas y las listas no cambian.

## Open Questions

Ninguna.
