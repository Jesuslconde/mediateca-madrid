# Mediateca Madrid — portal web

`apps/web` es la interfaz pública de Mediateca Madrid. Consume la API FastAPI para buscar el catálogo, mostrar fichas, filtrar por biblioteca y gestionar listas de favoritos compartibles.

No accede directamente a PostgreSQL ni a Meilisearch. El catálogo lo produce `services/enrich`; el portal solo lee datos a través de `services/api` y mantiene en el navegador el código postal utilizado para ordenar por cercanía.

## Índice

- [Stack y límites](#stack-y-límites)
- [Estructura](#estructura)
- [Configuración](#configuración)
- [Renderizado y navegación](#renderizado-y-navegación)
- [Cliente HTTP y contratos](#cliente-http-y-contratos)
- [Búsqueda y filtros](#búsqueda-y-filtros)
- [Resultados y paginación](#resultados-y-paginación)
- [Ficha de registro](#ficha-de-registro)
- [Bibliotecas y cercanía](#bibliotecas-y-cercanía)
- [Listas de favoritos](#listas-de-favoritos)
- [SEO, accesibilidad y diseño](#seo-accesibilidad-y-diseño)
- [Comandos y desarrollo](#comandos-y-desarrollo)
- [Limitaciones actuales](#limitaciones-actuales)

## Stack y límites

| Elemento | Versión declarada | Uso |
|---|---:|---|
| Next.js | `^16.4.6` | App Router y servidor standalone |
| React | `^19.1.0` | Server y Client Components |
| TypeScript | `^5.7.0` | Tipado estricto |
| Tailwind CSS | `^3.4.17` | Estilos responsive |
| ESLint | `^9.0.0` | Reglas de Next y Core Web Vitals |
| `openapi-typescript` | `^7.13.0` | Generación de tipos desde OpenAPI |

El paquete se llama `mediateca-web`. Node 22 es la versión usada en Docker. No hay biblioteca de componentes, cliente HTTP externo, gestor de estado remoto, mapas, validación runtime ni framework de pruebas.

### Flujo de datos

```text
PostgreSQL + Meilisearch
          ↓
services/api
          ↓ HTTP API_URL
apps/web
  ├── Server Components: catálogo, fichas y listas
  ├── Server Actions: crear, adoptar y modificar listas
  └── Client Components: filtros, orden, favoritos y cercanía
```

| Componente | PostgreSQL | Meilisearch | Estado propio |
|---|---|---|---|
| `services/enrich` | Migraciones y escritura del catálogo | Escritura y reconstrucción | Cola y configuración |
| `services/api` | Lectura del catálogo; escritura de listas | Solo lectura | Contrato OpenAPI |
| `apps/web` | Sin acceso | Sin acceso | Cookie de lista y `localStorage` |
| `packages/shared` | Modelos | Contrato de documentos | Esquemas y `SCHEMA_VERSION` |

## Estructura

```text
apps/web/
├── app/
│   ├── layout.tsx                         # layout, navegación y lista activa
│   ├── page.tsx                           # portada
│   ├── globals.css                        # Tailwind y estilos base
│   ├── robots.ts                          # exclusiones de indexación
│   ├── actions/lists.ts                   # Server Actions
│   ├── buscar/
│   │   ├── page.tsx                       # búsqueda, filtros y facetas
│   │   └── loading.tsx                    # esqueleto
│   ├── registro/[recordId]/
│   │   ├── page.tsx                       # ficha de edición
│   │   └── loading.tsx                    # esqueleto
│   ├── mi-lista/page.tsx                  # lista activa
│   └── lista/[token]/
│       ├── page.tsx                       # lista compartida
│       ├── not-found.tsx                  # token ausente o caducado
│       └── error.tsx                      # error recuperable
├── components/                            # UI de servidor y cliente
├── lib/
│   ├── api.ts                             # cliente del catálogo
│   ├── api-types.ts                       # tipos OpenAPI generados
│   ├── lists.ts                           # cliente HTTP de listas
│   ├── list-cookie.ts                     # cookie de lista activa
│   ├── list-cookie-config.ts              # política Secure
│   ├── active-list.ts                     # resolución de lista activa
│   ├── geo.ts                             # Haversine y distancias
│   ├── codigos-postales-madrid.json       # centroides y municipios
│   ├── labels.ts                          # idiomas, países y fuentes
│   ├── sort.ts                            # órdenes admitidos
│   └── url.ts                             # parámetros y URLs
├── next.config.mjs
├── tailwind.config.ts
├── postcss.config.mjs
├── tsconfig.json
└── package.json
```

### Componentes cliente

La interactividad se aísla en:

- `SortSelect`: cambia el orden mediante la URL.
- `PaginationLink`: muestra estado pendiente durante la navegación.
- `FavoriteButton`: actualización optimista del favorito.
- `ShareLink`: copia el enlace de una lista.
- `AdoptList`: adopta una lista compartida como activa.
- `LibrarySelect`: filtra y agrupa bibliotecas/sucursales en el navegador.
- `LibrariesTable`: agrupa ejemplares y calcula distancias.
- `app/lista/[token]/error.tsx`: boundary de error.

Las páginas y componentes principales son Server Components.

## Configuración

### Next.js

`next.config.mjs` define:

- `output: "standalone"`.
- `outputFileTracingRoot` limitado a `apps/web`.
- `reactStrictMode: true`.
- Cabeceras privadas para `/lista/:path*` y `/mi-lista`:
  - `Referrer-Policy: no-referrer`.
  - `X-Robots-Tag: noindex, nofollow`.

No hay rewrites, proxy de API, dominios de imagen ni configuración de caché personalizada. El portal llama a la API desde el servidor.

### TypeScript

`tsconfig.json` usa:

- `strict: true`.
- Target `ES2022`.
- Módulos `ESNext` y resolución `bundler`.
- `noEmit: true`.
- Alias `@/*` → `./*`.
- `resolveJsonModule: true` para importar el JSON de códigos postales.
- Tipos de rutas generados por Next en `.next/types`.

### Estilos

Tailwind analiza `app`, `components` y `lib`. La paleta personalizada usa `ink`, `paper` y `accent`, con una sombra `card`. PostCSS aplica `tailwindcss` y `autoprefixer`.

`globals.css` define el esquema claro, `scroll-behavior: smooth`, estilos de selección y `<mark>`. No hay modo oscuro.

### Variables de entorno

| Variable | Predeterminado | Ámbito | Uso |
|---|---|---|---|
| `API_URL` | `http://localhost:8000` | Servidor | URL base de la API |
| `MEDITECA_WEB_COOKIE_SECURE` | `auto` | Servidor | Política `Secure` de la cookie |
| `PORT` | `3000` en Docker | Servidor | Puerto standalone |
| `HOSTNAME` | `0.0.0.0` en Docker | Servidor | Bind del servidor |
| `NEXT_TELEMETRY_DISABLED` | `1` en Docker | Build/runtime | Desactiva telemetría |

`API_URL` no lleva prefijo `NEXT_PUBLIC_`: no se expone al navegador. No existen variables de PostgreSQL, Meilisearch o TMDB en el portal.

En Compose y Portainer se configura:

```yaml
API_URL: http://api:8000
MEDITECA_WEB_COOKIE_SECURE: ${MEDITECA_WEB_COOKIE_SECURE:-auto}
```

## Renderizado y navegación

### Rutas

| Ruta | Contenido |
|---|---|
| `/` | Buscador, accesos por soporte, estadísticas y distribución del catálogo |
| `/buscar` | Resultados, filtros, facetas, orden, paginación y favoritos |
| `/registro/[recordId]` | Ficha completa y ediciones de la misma obra |
| `/mi-lista` | Lista activa del navegador |
| `/lista/[token]` | Lista compartida editable |

`/lista/[token]` incluye `not-found.tsx` y `error.tsx`. `robots.ts` controla la indexación.

### Datos dinámicos

Las páginas de datos usan `export const dynamic = "force-dynamic"`. Además, `lib/api.ts` y `lib/lists.ts` usan `fetch(..., { cache: "no-store" })`.

No se usa ISR, `revalidate`, `unstable_cache` ni caché persistente. El objetivo es reflejar cambios del catálogo y del índice sin recompilar el portal.

El layout lee la cookie de lista activa para mostrar el contador de “Mi lista”, de modo que incluso la navegación pública se personaliza por petición.

### Transiciones

- Los enlaces internos usan `next/link`.
- Buscador y filtros usan `next/form`.
- `SortSelect` usa `router.replace` y conserva los parámetros.
- `PaginationLink` usa `useLinkStatus()` para mostrar “Cargando…”.
- Los esqueletos de búsqueda y ficha anuncian el estado con `role="status"`, `aria-live` y `aria-busy`.

En `/buscar`, `SearchBody` se envuelve en `<Suspense key={suspenseKey}>` para reiniciar el estado de carga cuando cambian los parámetros. Búsqueda, ubicaciones y lista activa se cargan con `Promise.all`.

En la ficha, `getRecord()` se resuelve antes de consultar la lista activa. El layout ya ha consultado esa lista para el contador, por lo que existen llamadas independientes adicionales.

## Cliente HTTP y contratos

### Catálogo

`lib/api.ts` centraliza el acceso al catálogo:

- `API_URL = process.env.API_URL ?? "http://localhost:8000"`.
- `queryString()` omite valores vacíos y serializa arrays como parámetros repetidos.
- `apiFetch<T>()` añade `Accept: application/json`, usa `no-store` y lanza un error con estado y detalle si la respuesta no es correcta.
- No hay timeout, aborto ni reintentos.
- La respuesta se convierte directamente a `T`; no hay validación runtime.

Funciones:

| Función | Endpoint |
|---|---|
| `searchRecords(params)` | `GET /api/search` |
| `getRecord(recordId)` | `GET /api/records/{record_id}` |
| `getLibraries()` | `GET /api/libraries` |
| `getLocations()` | `GET /api/locations` |
| `getStats()` | `GET /api/stats` |

La búsqueda actual usa `getLocations()`; `getLibraries()` permanece disponible pero no se utiliza en las páginas actuales.

Los tipos `SearchHit`, `SearchResponse`, `Library`, `Location`, `Stats`, `Persona`, `Enlace`, `Ejemplar`, `Obra` y `RecordDetail` proceden de `api-types.ts`.

### Listas

`lib/lists.ts` implementa el cliente HTTP de listas:

- `listFetch<T>()` usa `no-store` y `Content-Type` cuando hay cuerpo.
- `ListApiError` conserva el estado HTTP.
- `createList()` reenvía la primera IP de `x-forwarded-for` o `x-real-ip` como `X-Client-IP`.
- `getList(token)` devuelve `null` ante 404 y propaga otros errores.
- Tokens e identificadores se codifican con `encodeURIComponent`.

### OpenAPI

El flujo de tipos es:

```bash
make openapi       # API -> contracts/openapi.json
make web-types     # OpenAPI -> apps/web/lib/api-types.ts
make contracts     # ambos pasos
```

`api-types.ts` es un archivo generado: no debe editarse manualmente. Contiene `paths`, `operations` y esquemas, pero no es un cliente ejecutable.

El contrato versionado actual declara `0.7.11`, mientras el repositorio está en `0.8.2`. Debe regenerarse después de cambiar la API. Además, el contrato no documenta todos los estados runtime: por ejemplo, `POST /api/lists/{token}/items` puede devolver 201 al crear un elemento y 200 si ya existía, y la búsqueda puede devolver 400 o 503.

## Búsqueda y filtros

### Parámetros de URL

`app/buscar/page.tsx` reconoce:

| Parámetro | Tratamiento |
|---|---|
| `q` | Primer valor, con `trim()` |
| `campo` | `titn` o `todo`; otros valores equivalen a `todo` |
| `soporte` | Uno o varios valores |
| `genero` | Primer valor |
| `idioma` | Primer valor |
| `paises_origen` | Uno o varios valores |
| `biblioteca` | Código de biblioteca/sucursal o nombre histórico |
| `fuente` | Primer valor; se envía a la API |
| `anio_desde`, `anio_hasta` | Conversión numérica si es finita |
| `page` | Mínimo 1 |
| `sort` | Validado contra `SORT_VALUES` |
| `volver` | URL de retorno a resultados; no se reenvía como filtro |

La página solicita siempre `limit: 20`.

### Buscador

`SearchBar` es un formulario GET hacia `/buscar`:

- Selector `Todo` / `TITN`.
- Input `type="search"`.
- En modo TITN envía `titn`, no `q`.
- Una búsqueda nueva desde la barra no conserva los filtros anteriores.

### Filtros laterales

`FacetFilters` construye otro formulario GET:

- Soportes: garantiza `DVD`, `Blu-ray` y `4K UHD`, y añade otros valores de las facetas.
- Género e idioma: ordenados por conteo descendente y limitados a 40 entradas.
- Países: `<select multiple>` con etiquetas españolas.
- Biblioteca/sucursal: `LibrarySelect`.
- Año: inputs numéricos con límites HTML 1900–2100.
- Campos ocultos para consulta, modo de campo y orden no predeterminado.
- Al aplicar filtros se elimina `page` y vuelve a la primera página.
- “Limpiar filtros” conserva consulta y modo de campo.

La API devuelve facetas de soportes, géneros, año, idiomas, países, bibliotecas y fuente. El portal construye controles para soportes, géneros, idiomas, países y bibliotecas.

### Semántica de la API

La búsqueda pública impone siempre `detail_complete=true`. Varios soportes se combinan con OR; varios países de origen también con OR. El resto de filtros se combina con AND.

- `titn` es coincidencia exacta.
- `genero` e `idioma` usan pertenencia/valor exacto.
- El año se convierte en rango numérico.
- `biblioteca` admite códigos estables `b:`/`s:` o nombres históricos.
- `fuente` es un filtro exacto.
- `disponible` está retirado y la API lo rechaza con 400.

Los campos textuales del índice incluyen títulos, sinopsis, dirección, reparto, guion, personas, materias, géneros, publicación y TITN.

## Resultados y paginación

### Agrupación por obra

Meilisearch usa `distinct: "obra_key"`, por lo que una obra produce como máximo una tarjeta. Una edición sin obra utiliza `edicion:<record_id>` y aparece individualmente.

La API carga las ediciones de cada obra encontrada y agrega:

- Soportes.
- Bibliotecas.
- Número de ejemplares.
- Número de ediciones.
- Metadatos de respaldo, como póster, año, duración, sinopsis y título uniforme.

La agregación abarca todas las ediciones de la obra, no solo las que cumplen individualmente el filtro activo. `total` representa obras paginables; `total_ediciones` y las facetas cuentan ediciones.

### Ordenación

| Valor | Etiqueta | Orden backend |
|---|---|---|
| `relevancia` | Relevancia | Sin orden explícito |
| `anio_desc` | Año más reciente | `anio:desc`, `titulo:asc` |
| `anio_asc` | Año más antiguo | `anio:asc`, `titulo:asc` |
| `titulo_asc` | Título A-Z | `titulo:asc` |
| `duracion_asc` | Duración menor | `duracion_min:asc`, `titulo:asc` |

`SortSelect` conserva los parámetros, elimina `page`, usa `router.replace` y desactiva el control durante la transición.

### Tarjetas

`RecordCard` muestra:

- Título y sinopsis con resaltado de búsqueda.
- Título uniforme.
- Póster TMDB con carga diferida.
- Soportes, año, duración, idioma, países y edad.
- Hasta tres géneros.
- Dirección y hasta cuatro actores.
- Número de ediciones, ejemplares y bibliotecas.
- Favorito, enlace TMDB y enlace a la ficha.

El enlace interno usa `record_id`; mantiene `titn` como respaldo. El resaltado se inserta como HTML procedente de los campos `_formatted` de Meilisearch; el portal confía en la API y no aplica un saneador propio.

### Paginación y estados

La paginación solo ofrece anterior/siguiente y conserva los parámetros de búsqueda.

- Error de API: panel “No se pudo conectar con la API”.
- Sin resultados: estado vacío y enlace para limpiar la búsqueda.
- Si falla `getLocations()`, el selector de bibliotecas queda vacío.
- Si falla la lista activa, los favoritos se muestran como no guardados.

`volver` se construye con todos los parámetros de búsqueda y se codifica en los enlaces a fichas. `safeVolver()` acepta rutas que empiezan por `/buscar` y rechaza dobles barras o barras invertidas.

## Ficha de registro

`app/registro/[recordId]/page.tsx` acepta:

- Un `record_id` completo.
- Un TITN suelto de URLs antiguas, que la API resuelve como `madrid:<titn>`.

`decodePathParam()` tolera codificaciones repetidas al decodificar el parámetro.

### Contenido

Cabecera:

- Soportes.
- Título y título uniforme.
- Publicación y año.
- Favorito y enlace TMDB.
- Fuente, TITN y EAN.

Metadatos:

- Año, duración, idioma y país del OPAC.
- Países de origen de TMDB.
- Edad recomendada, tipo documental y soporte principal.
- Número de ejemplares.

Cuerpo:

- Sinopsis.
- Créditos agrupados por función: dirección, guion, reparto, producción, fotografía, música y otros.
- Ediciones de la misma obra.
- Bibliotecas, sucursales y ejemplares.
- Notas que empiezan por `Nota` o `Depósito`.
- Géneros, materias y enlaces externos.
- Procedencia y enlace al OPAC original.

El campo MARC se recibe en el contrato, pero no se muestra.

### Ediciones hermanas

Si la obra tiene más de una edición, se listan todas con fuente, año, soportes y ejemplares. La edición actual se marca visualmente y cada enlace conserva `volver`.

### Errores

Cualquier error de `getRecord()` se transforma en `null` y termina en `notFound()`. Un fallo transitorio de la API se presenta como ficha no encontrada, no como error de servicio.

## Bibliotecas y cercanía

### Selector

`LibrarySelect` consume `Location[]` de `GET /api/locations` y permite buscar por nombre visible sin acentos ni mayúsculas.

Agrupa por `fuente:codigo_biblioteca`, ordena con locale `es` y coloca la biblioteca matriz antes que sus sucursales. El valor seleccionado se reinserta si el filtro local lo oculta; si ya no existe, se crea una opción histórica.

Códigos estables:

```text
b:<fuente>:<codigo_biblioteca>
s:<fuente>:<codigo_sucursal>
```

La API normaliza códigos antiguos sin fuente a Madrid.

### Agrupación de ejemplares

`LibrariesTable` agrupa por biblioteca y sucursal. Cada grupo contiene biblioteca, sucursal, ejemplares, código postal y un punto de coordenadas.

- Si varios ejemplares aportan ubicación, conserva el primer punto disponible.
- El orden inicial es alfabético.
- Cada grupo muestra signatura, localización, tipo y soporte.
- Las tablas usan `overflow-x-auto`.
- El enlace al OPAC se repite en cada grupo.

### Resolución de coordenadas

Para cada grupo:

1. Usar latitud/longitud de la API si existen.
2. Si faltan, buscar el centroide del código postal en `lib/codigos-postales-madrid.json`.
3. Si no hay punto utilizable, dejar el grupo sin distancia.

El JSON contiene 304 códigos de la provincia de Madrid con código, municipio, latitud, longitud, fuente y licencia.

Se regenera con:

```bash
python3 scripts/generate_codigos_postales.py
```

El generador descarga centroides de `kodens-dev/Spain-Postal-Codes` (MIT) y municipios del INE mediante `regi-es/ds-codigos-postales-ine-es` (CC BY 4.0). Filtra códigos `28`, normaliza a cinco dígitos, deduplica y ordena.

### Distancia

`lib/geo.ts` implementa Haversine con radio terrestre de 6371 km.

- Menos de 1 km: metros redondeados a 10, mínimo 10.
- Desde 1 km: un decimal con formato `es-ES`.
- Se muestra siempre con `≈`.

Con código postal seleccionado, los grupos con punto se ordenan por distancia y los grupos sin ubicación quedan al final. A igual distancia se desempata alfabéticamente. Si ninguno tiene ubicación, se mantiene el orden alfabético y se muestra un aviso.

### Persistencia y privacidad

- Clave localStorage: `mediateca:codigo-postal`.
- Se lee en `useEffect()` para evitar diferencias de hidratación.
- Un valor que no está en el JSON se elimina.
- No se solicita geolocalización del navegador.
- El código postal no se envía a la API ni se incluye en la URL.

El fallback por centroide solo cubre Madrid. Otras fuentes sin coordenadas y con códigos no madrileños no tienen respaldo local.

## Listas de favoritos

### Flujo de favorito

`FavoriteButton` es un Client Component con:

- `useState`.
- `useOptimistic`.
- `useTransition`.
- `aria-pressed` y etiqueta accesible.
- Botón deshabilitado durante la petición.
- Formulario como respaldo progresivo sin JavaScript.

`app/actions/lists.ts` implementa las Server Actions:

| Acción | Comportamiento |
|---|---|
| `ensureListToken()` | Usa la cookie o crea una lista |
| `toggleFavoriteAction()` | Añade o quita según el estado previo |
| `toggleFavoriteFormAction()` | Variante para envío de formulario |
| `createListAction()` | Crea una lista y redirige a `/mi-lista` |
| `removeItemAction()` | Quita un elemento |
| `renameListAction()` | Renombra la lista |
| `adoptListAction()` | Fija una lista compartida como activa |

Si la API devuelve 404 al añadir un favorito, la acción crea otra lista y reintenta. Un 409 muestra el mensaje de lista llena. Las mutaciones correctas llaman a:

```ts
revalidatePath("/", "layout");
```

### Cookie de lista activa

`lib/list-cookie.ts` define:

| Atributo | Valor |
|---|---|
| Nombre | `mediateca_lista` |
| Contenido | Token opaco en claro, solo accesible al servidor |
| `HttpOnly` | `true` |
| `SameSite` | `lax` |
| `Path` | `/` |
| `Max-Age` | 180 días |

`MEDITECA_WEB_COOKIE_SECURE` controla `Secure`:

- `auto`: se activa si el primer `x-forwarded-proto` es `https`.
- `true`: siempre activo.
- `false`: nunca activo.
- Cualquier otro valor se interpreta como `auto`.

Existe `clearActiveListToken()`, pero no se usa actualmente. Si la cookie apunta a una lista inexistente, no se borra; el siguiente favorito crea una lista nueva cuando la API devuelve 404.

### Lista activa

`lib/active-list.ts`:

- Lee la cookie.
- Consulta la lista.
- Captura errores y devuelve `null`.
- Construye un `Set` de `record_id` guardados.

El layout usa esa información para mostrar el contador de “Mi lista”.

### `/mi-lista`

Estados:

1. Sin cookie o lista inexistente: estado vacío, explicación, botón para crear lista y enlace a búsqueda.
2. Error distinto de 404: panel de error y enlace para reintentar.
3. Lista válida: `ListaView`.

Metadatos: `robots: { index: false, follow: false }`.

### Lista compartida

`/lista/[token]` consulta la lista y muestra `AdoptList` si no coincide con la cookie activa. `AdoptList` ejecuta `adoptListAction(token)` en `useEffect()`.

Con JavaScript, abrir una lista compartida sustituye la lista activa del navegador. La lista anterior no se borra y sigue accesible por su enlace. Sin JavaScript, la lista puede verse y editarse mediante Server Actions, pero no se ejecuta la adopción automática de la cookie.

### `ListaView` y `ShareLink`

`ListaView` muestra:

- Título y número de elementos.
- Renombrado con `maxLength=80`.
- Elementos en el orden de la API.
- Fuente, año, soportes y póster.
- Estado “Ficha no disponible” cuando `disponible=false`.
- Acción para quitar elementos.
- Enlace al OPAC cuando existe.
- Estado vacío con enlace a búsqueda.

`ShareLink`:

- Construye la URL con el origen real del navegador tras hidratarse.
- Usa un input readonly.
- Copia con `navigator.clipboard.writeText()`.
- Muestra “Copiado” durante 2,5 segundos.
- Si falla el portapapeles, indica copia manual.
- Advierte de que cualquiera con el enlace puede ver y editar la lista.

### Semántica de la API

- Token generado con `secrets.token_urlsafe(24)`.
- PostgreSQL solo guarda su hash SHA-256.
- Máximo 200 elementos.
- Título recortado y limitado a 80 caracteres; vacío → “Mi lista”.
- Elementos ordenados por fecha de adición descendente.
- Añadir es idempotente.
- Si una edición desaparece, se conserva su título snapshot.
- `disponible=false` significa que la ficha no existe o está marcada como desaparecida; no indica disponibilidad de préstamo.
- Caducidad de 180 días desde la última mutación.
- Límite de creación: 5 por IP/hora y 60 globales/hora.
- El limitador vive en memoria del proceso; no se comparte entre réplicas ni persiste tras reinicios.

Estados HTTP relevantes: 404 para token desconocido o caducado, 409 para lista llena, 422 para edición inexistente y 429 por creación excesiva.

### Protección del token

- Páginas de lista con `noindex,nofollow`.
- `robots.ts` excluye `/lista/` y `/mi-lista`.
- Cabeceras `X-Robots-Tag` y `Referrer-Policy: no-referrer`.
- Enlaces externos con `rel="noreferrer"`.
- La API enmascara tokens de `/api/lists/...` en los logs de acceso de Uvicorn.

No hay cuentas, correo ni contraseñas. La IP se usa temporalmente para limitar creación, pero no se guarda en las tablas de listas.

## SEO, accesibilidad y diseño

### SEO

El layout global define:

- `<html lang="es">`.
- Título “Mediateca Madrid” y plantilla `%s · Mediateca Madrid`.
- Descripción general.
- Favicon.
- Atribución de TMDB en el footer.
- Aviso de portal alternativo no oficial.
- Enlace al OPAC oficial.
- Versión visible desde `package.json`.

No hay metadatos específicos por ficha, canonical, Open Graph, sitemap, `metadataBase`, JSON-LD ni manifest PWA.

### Accesibilidad

Se han implementado:

- Elementos semánticos `header`, `nav`, `main`, `article`, `section`, `aside`, `footer`, tablas y listas de definición.
- Un `h1` por página de contenido.
- Labels explícitos u ocultos en los controles principales.
- Texto alternativo en pósteres.
- Botones nativos y controles operables por teclado.
- `aria-pressed` en favoritos.
- `aria-busy` en ordenación.
- `aria-live` en errores, distancias y paginación.
- `role="status"` y texto `sr-only` en esqueletos.
- Iconos decorativos con `aria-hidden`.

No hay enlace para saltar al contenido, estilos `focus-visible` propios ni manejo de `prefers-reduced-motion`. Los inputs de año no tienen labels explícitos. No existen pruebas automáticas de accesibilidad ni una auditoría WCAG.

### Responsive

- Contenedor `max-w-7xl` con padding.
- Breakpoints `sm`, `md` y `lg`.
- Buscador adaptable.
- Filtros en una columna o panel fijo de 280 px en pantallas grandes.
- Ficha en una o dos columnas, con lateral de 340 px.
- Portada en una o tres columnas.
- Tablas de ejemplares con scroll horizontal.

No hay menú móvil específico.

## Comandos y desarrollo

Desde `apps/web`:

```bash
npm ci
npm run dev
npm run build
npm start
npm run lint
npm run generate:api
```

| Script | Comando |
|---|---|
| `dev` | `next dev` |
| `build` | `next build` |
| `start` | `next start` |
| `generate:api` | `openapi-typescript ../../contracts/openapi.json -o lib/api-types.ts` |
| `lint` | `eslint .` |

No hay scripts `test`, `typecheck` o `format`, ni pruebas frontend. El build de Next comprueba tipos por defecto.

Desde la raíz del monorepo:

```bash
make up
make web-types
make contracts
```

`make lint` y `make fmt` solo cubren Python; no incluyen el portal. `make test` ejecuta shared, API e ingesta.

### Docker

`docker/web.Dockerfile`:

1. Construye el portal con Node 22 y `npm ci`.
2. Ejecuta `npm run build`.
3. Prepara una etapa runtime con Node y Python.
4. Instala `packages/shared` y la API.
5. Copia `.next/standalone`, `.next/static` y `public`.
6. Ejecuta `node server.js`.

La imagen `mediateca-web` aloja dos contenedores separados: API y portal.

## Limitaciones actuales

- El contrato OpenAPI está desactualizado respecto a la versión del repositorio y debe regenerarse tras cambios de API.
- `FacetFilters` no conserva el filtro `fuente` porque no tiene un control o campo oculto para él.
- Un `sort` inválido en la URL puede conservarse al enviar el formulario de filtros y provocar un 400.
- La validación de parámetros del portal es limitada; la API sigue siendo la autoridad final.
- El resaltado de título y sinopsis confía en el HTML de Meilisearch.
- La lista activa se consulta varias veces por petición.
- Un fallo temporal de la ficha se presenta como 404 de aplicación.
- Las llamadas a `localStorage` no están protegidas contra navegadores que bloqueen el almacenamiento.
- No hay pruebas automatizadas del portal.
- CORS de la API solo declara métodos GET; el portal no se ve afectado porque las Server Actions llaman a la API desde el servidor.

## Documentación relacionada

- [API pública](../../services/api/README.md)
- [Ingesta y dashboard](../../services/enrich/README.md)
- [Modelos compartidos](../../packages/shared/README.md)
- [Operación y despliegue](../../docs/OPERATIONS.md)
- [Arquitectura](../../docs/ARCHITECTURE.md)
