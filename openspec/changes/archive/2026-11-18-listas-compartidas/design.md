# Design

## Context

Ver `proposal.md` para la motivacion y `specs/` para el contrato de comportamiento.

El estado actual que condiciona el diseno:

- La API es FastAPI de solo lectura, con CORS limitado a `GET`, y comprueba `SCHEMA_VERSION` contra `schema_meta` al arrancar.
- `apps/web` es Next.js 15 con App Router y componentes de servidor. Ya usa `dynamic = "force-dynamic"` en portada, resultados y ficha, y habla con la API por `API_URL` interno.
- `packages/shared` concentra modelos SQLAlchemy, esquemas Pydantic y `SCHEMA_VERSION`. La ingesta es la propietaria de las migraciones y `init` las aplica antes de arrancar la API.
- El portal no guarda datos personales. La unica preferencia persistente es el codigo postal en `localStorage`.
- El despliegue es un contenedor por servicio, sin proxy inverso ni TLS dentro del stack.

## Goals / Non-Goals

**Goals:**

- Persistir una lista de ediciones favoritas en PostgreSQL sin introducir cuentas ni datos personales.
- Convertir la URL de la lista en la unica credencial, con lectura y edicion para quien la posea.
- Mantener el navegador como cliente fino: ninguna llamada directa del navegador a la API.
- Encajar en el ciclo actual de migraciones, contratos y despliegue sin servicios nuevos.
- Degradar con elegancia cuando una edicion guardada desaparece del catalogo.

**Non-Goals:**

- Autenticacion, sesiones de usuario, correo, recuperacion de cuenta o roles.
- Varias listas por navegador, colaboracion con permisos o historial de cambios.
- Sincronizacion en tiempo real entre pestanas o dispositivos.
- Orden manual de elementos, notas por titulo o avisos de disponibilidad.
- Cambiar el modelo de catalogo o la propiedad de escritura de la ingesta.

## Decisions

### 1. PostgreSQL compartido con escritura acotada a listas

Se anaden las tablas `listas` y `lista_items` a la base existente. La API gana un router de listas que solo escribe en esas dos tablas; el catalogo sigue siendo exclusivo de `services/enrich`.

Alternativas descartadas:

- **Base o esquema separado para datos de usuario**: anade operacion (backups, permisos, migraciones) sin resolver un problema real, porque no hay PII.
- **Servicio externo de listas**: introduce una dependencia y un coste desproporcionados para dos tablas.
- **localStorage**: no cumple el objetivo de persistencia ni de compartir.

La tabla de propiedad de escritura de `docs/ARCHITECTURE.md` se actualiza para reflejar la excepcion: la API lee el catalogo y escribe solo listas. El requisito de `operacion-despliegue` se modifica en este mismo cambio para recoger la excepcion y el mantenimiento de listas desde `init`.

### 2. Token opaco como credencial, hash en reposo

- El token se genera con `secrets.token_urlsafe(24)` (192 bits, 32 caracteres).
- En la base de datos se guarda `sha256(token)` en `listas.token_hash`, con indice unico. La busqueda se hace por hash; el token en claro nunca se persiste.
- El token viaja en la ruta `/lista/{token}` y en una cookie `HttpOnly` para comodidad del navegador.
- Una cookie robada o una URL filtrada conceden lo mismo: lectura y edicion. Es una decision de producto aceptada.

Alternativas descartadas:

- **Guardar el token en claro**: un dump de la base concederia edicion sobre todas las listas.
- **JWT firmado**: anade rotacion, revocacion y secretos sin aportar nada frente a un identificador opaco.
- **Dos tokens (propietario y compartido)**: el producto decidio que el enlace compartido sea editable.

El hash protege ante una fuga de la base, no ante una fuga del enlace. Esa distincion queda documentada.

### 3. BFF: el navegador solo habla con Next

Las mutaciones se implementan como Server Actions de Next. El navegador envia el formulario a Next, Next lee la cookie y llama a la API por la red interna.

```text
navegador --POST (server action)--> Next --POST/DELETE--> API --> PostgreSQL
   ^                                  |
   +---- HTML/RSC revalidado ---------+
```

Consecuencias:

- CORS puede seguir limitado a `GET`; el navegador nunca llama a la API.
- La cookie es same-origin con el portal, sin `SameSite=None` ni problemas de dominio.
- Las Server Actions de Next validan el origen de la peticion, lo que cubre CSRF junto con `SameSite=Lax`.
- La API sigue siendo accesible por red interna; el puerto publicado en el stack es una decision operativa aparte.

Alternativa descartada: llamada directa del navegador a la API con cookie entre origenes. Requiere CORS con credenciales, `SameSite=None`, TLS y proteccion CSRF adicional.

### 4. Modelo de datos

```text
listas
  id             uuid pk            (generado en Python)
  token_hash     char(64) unique    sha256 del token
  titulo         varchar(80) null   por defecto "Mi lista"
  created_at     timestamptz
  updated_at     timestamptz
  expires_at     timestamptz        now + 180 dias, deslizante

lista_items
  lista_id       uuid fk -> listas on delete cascade
  titn           varchar(32)
  titulo_snapshot varchar(1000)     titulo en el momento de guardar
  added_at       timestamptz
  pk (lista_id, titn)
  index (lista_id, added_at desc)
```

Decisiones:

- **Favorito por edicion (`titn`), no por obra**: la UI ya trabaja con `titn`, el enlace al OPAC es por edicion y `Edicion.obra_id` puede ser nulo en stubs. Agrupar por obra queda como mejora de presentacion futura.
- **`titulo_snapshot`**: permite renderizar la lista cuando la edicion desaparece. No se guardan portada, sinopsis ni disponibilidad, que envejecen mal.
- **Sin columna `position`**: orden por `added_at` descendente. El orden manual queda fuera de alcance.
- **`ON DELETE CASCADE`**: borrar una lista elimina sus elementos sin logica adicional.

Los modelos viven en `packages/shared/src/mediateca_shared/lists.py` y se importan desde `models.py` para que `Base.metadata.create_all` los registre en bases nuevas.

### 5. API

Router nuevo `services/api/src/mediateca/api/routers/lists.py`, incluido con prefijo `/api`.

| Metodo | Ruta | Respuesta |
|---|---|---|
| POST | `/lists` | 201 `{ token }` |
| GET | `/lists/{token}` | 200 `ListaOut` |
| POST | `/lists/{token}/items` | 201 si se anade, 200 si ya estaba `{ item_count }` |
| DELETE | `/lists/{token}/items/{titn}` | 200 `{ item_count }` |
| PATCH | `/lists/{token}` | 200 `ListaOut` |

`ListaOut` incluye `titulo`, `item_count`, `created_at`, `updated_at`, `expires_at` e `items`. `ListaItemOut` incluye `titn`, `titulo` (vigente o guardado), `soportes`, `anio`, `poster_url`, `opac_url` y `disponible`. Los campos de catalogo son opcionales cuando la ficha ya no existe.

Reglas de validacion:

- `titn` debe existir en `ediciones` al anadirse. Un `titn` inexistente devuelve 422.
- Anadir es idempotente: `ON CONFLICT (lista_id, titn) DO NOTHING` o comprobacion previa; el resultado es 200 y `item_count` sin cambios.
- Lista llena (200 elementos) devuelve 409 con mensaje legible.
- Token desconocido o caducado devuelve 404, sin distinguir ambos casos.
- El titulo se recorta a 80 caracteres tras eliminar espacios sobrantes; vacio significa `Mi lista`.
- Toda mutacion renueva `updated_at` y `expires_at`. Las lecturas no renuevan la caducidad.

El router no toca ninguna tabla del catalogo. Las respuestas de lista llevan `Cache-Control: no-store`.

### 6. Cookie y lectura de la lista activa

- Cookie `mediateca_lista` con el token en claro, `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age` de 180 dias y `Secure` cuando el entorno es produccion.
- Se escribe en Server Actions, nunca durante el render de un componente de servidor (Next 15 no lo permite).
- `getActiveListToken()` lee la cookie; `getActiveList()` consulta la API y devuelve `null` si el token ya no existe. Un 404 se trata como "sin lista activa" y la siguiente mutacion sobrescribe la cookie.
- La cabecera muestra el enlace a `/mi-lista` y el recuento. El layout ya es dinamico en las paginas principales; se asume una llamada interna adicional por render, cacheada por peticion.

### 7. Paginas y componentes

- `apps/web/app/mi-lista/page.tsx`: componente de servidor. Sin cookie muestra estado vacio con accion de crear. Con lista muestra elementos, recuento, enlace compartible, formulario de renombrado y botones de quitar.
- `apps/web/app/lista/[token]/page.tsx`: componente de servidor. Consulta la lista; si no existe, `notFound()`. Renderiza el mismo contenido que `/mi-lista` y un componente cliente `AdoptList` que invoca la accion `adoptList(token)` para fijar la cookie como lista activa.
- `apps/web/components/FavoriteButton.tsx`: componente cliente con `useOptimistic` y `useTransition`. Incluye un `<form action={...}>` para funcionar sin JavaScript, `aria-pressed` y etiqueta accesible. No usa iconos externos.
- `apps/web/components/ShareLink.tsx`: copia el enlace con `navigator.clipboard` y ofrece el texto seleccionable como respaldo.
- `apps/web/lib/lists.ts`: cliente de la API para listas.
- `apps/web/lib/list-cookie.ts`: lectura y escritura de la cookie.
- `apps/web/app/actions/lists.ts`: Server Actions `createListAction`, `toggleFavoriteAction`, `removeItemAction`, `renameListAction` y `adoptListAction`, con `revalidatePath` sobre las rutas afectadas.

Para pintar el corazon en resultados y ficha, la pagina obtiene una vez el conjunto de `titn` guardados y lo pasa a las tarjetas. Si no hay cookie, el conjunto esta vacio sin llamar a la API.

### 8. Adopcion de una lista compartida

Next no permite escribir cookies desde un componente de servidor. Por eso la pagina `/lista/[token]` valida el token y, solo si la cookie actual es distinta, renderiza `AdoptList`, que ejecuta una Server Action al montar. Esto evita adoptar listas invalidas y mantiene el render inicial sin efectos secundarios. Adoptar otra lista solo cambia el puntero del navegador; la lista anterior sigue existiendo y accesible por su enlace.

Alternativa descartada: escribir la cookie en `middleware.ts`. Ahorra una ida y vuelta, pero adopta el token antes de saber si la lista existe y complica el tratamiento de enlaces caducados.

### 9. Limites, caducidad y abuso

- Maximo 200 elementos por lista, validado en la API.
- Limite de creacion en memoria por cliente y ventana (por ejemplo, 5 listas por hora). Next reenvia la IP del visitante en `X-Client-IP` a partir de `x-forwarded-for` o `x-real-ip`; la API la usa como clave en memoria y no la persiste. Si no hay cabecera, se aplica un cubo global mas permisivo.
- `expires_at` se renueva en cada mutacion. Un comando `clean-lists` en el CLI de la ingesta borra las listas caducadas y se ejecuta desde `init` despues de `migrate`. No se anade scheduler ni dependencia nueva.
- El limite en memoria asume una sola instancia de API, que es el despliegue actual. Si se anaden replicas o workers, el limite pasa a ser por proceso; se documenta como limitacion.

### 10. Privacidad y fugas del enlace

- `robots.ts` desautoriza `/lista/` y la pagina declara `robots: { index: false, follow: false }`.
- `next.config.mjs` aplica `Referrer-Policy: no-referrer` a `/lista/:path*` y `/mi-lista`; los enlaces externos ya usan `rel="noreferrer"`.
- El titulo de la lista se renderiza como texto, nunca como HTML.
- No se persisten IPs ni identificadores de cliente. Los logs de acceso de la API pueden contener el token en la ruta; se anade un filtro de logging que lo enmascara.
- Los enlaces compartidos no se indexan, pero pueden acabar en historiales, capturas o previsualizaciones de mensajeria. Es un riesgo aceptado del modelo.

### 11. Contratos y versionado

- `SCHEMA_VERSION` sube de `5` a `6`.
- Nueva migracion idempotente `services/enrich/scripts/migrate_listas.sql`, aplicada por `init`.
- Los esquemas Pydantic nuevos se anaden a `packages/shared` y se reexportan desde `mediateca/api/schemas.py`; el contrato se regenera con `make openapi` y `make web-types`.
- No se anaden dependencias Python ni Node. Todo se apoya en la biblioteca estandar (`secrets`, `hashlib`, `uuid`) y en lo ya instalado.

## Risks / Trade-offs

| Riesgo | Mitigacion |
|---|---|
| El enlace se filtra y cualquiera edita o vacia la lista | Aceptado por producto; no hay borrado de lista completa en v1; `noindex` y `no-referrer`; se puede crear otra lista y dejar de compartir la anterior |
| El token aparece en logs de acceso | Filtro de logging que enmascara `/api/lists/{token}`; recomendar la misma redaccion en el proxy |
| La API pasa de solo lectura a escribir listas | Escritura limitada por router y por tabla; el catalogo no se toca; se actualiza la tabla de propiedad y las pruebas lo verifican |
| Crecimiento ilimitado de listas anonimas | Maximo de elementos, limite de creacion, TTL deslizante y limpieza en `init` |
| Limite por IP eludible si la API esta publicada | La API debe quedar en red interna en produccion; si no hay cabecera de cliente, se aplica un cubo global |
| Cookie perdida y lista no editable desde ese navegador | La URL sigue siendo la credencial; basta volver a abrir el enlace para adoptarla |
| Edicion desaparecida del catalogo | `titulo_snapshot` y marca `disponible: false`; se puede quitar el elemento |
| Deriva entre imagenes y `SCHEMA_VERSION` | La comprobacion de arranque existente falla de forma legible; ambas imagenes se construyen desde el mismo commit |
| Sin pruebas de UI en el repositorio | Pruebas de API con SQLite en memoria y verificacion manual de las paginas; no se introduce un framework de test nuevo en este cambio |

## Migration Plan

1. Anadir modelos, esquemas y `SCHEMA_VERSION = "6"` en `packages/shared`.
2. Anadir `migrate_listas.sql` y el comando `clean-lists` en `services/enrich`.
3. Anadir el router de listas y sus pruebas en `services/api`.
4. Regenerar `contracts/openapi.json` y `apps/web/lib/api-types.ts`.
5. Implementar cookie, Server Actions, paginas y boton de favorito en `apps/web`.
6. Actualizar `docs/ARCHITECTURE.md` y `README.md` (propiedad de escritura, API y privacidad).
7. Reconstruir `mediateca-batch` y `mediateca-web`, desplegar `init` y despues API y portal.

Rollback: las tablas de listas pueden quedarse sin uso. Para volver a una version anterior de la API, restaurar `schema_meta.schema_version` al valor que espere esa version; no es necesario borrar las tablas. Si se quiere retirar la funcionalidad por completo, borrar `lista_items` y `listas` y revertir `SCHEMA_VERSION`. Las listas existentes se pierden en ese caso.

## Open Questions

- Presentacion de la lista: rejilla de tarjetas o lista compacta. No afecta al contrato ni a las tareas.
- Si conviene ofrecer mas adelante un boton para regenerar el enlace y invalidar el anterior. Queda fuera de v1.
- Si el recuento de la cabecera debe cachearse por peticion o resolverse con un endpoint ligero adicional. Se puede ajustar sin cambiar el comportamiento especificado.
