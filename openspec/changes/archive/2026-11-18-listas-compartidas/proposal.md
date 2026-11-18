# Proposal

## Why

Hoy el unico estado propio del visitante vive en `localStorage`: la busqueda y el codigo postal. No existe forma de guardar titulos que interesen ni de recuperarlos en otro dispositivo. El portal es de solo lectura y no almacena datos personales, asi que la solucion no debe introducir cuentas, correo ni contrasenas.

Una lista de favoritos identificada por una URL opaca resuelve las dos necesidades sin pedir identidad: la lista vive en el servidor, sobrevive al navegador y se comparte enviando el enlace. Quien recibe el enlace puede editarla, una decision de producto aceptada por el bajo impacto de una lista de titulos.

## What Changes

- Nueva capacidad de listas: crear una lista, anadir y quitar ediciones favoritas, renombrarla y abrirla desde un enlace compartible.
- Una sola lista activa por navegador. El primer favorito crea la lista; la cookie recuerda cual es; abrir otra lista la adopta como activa.
- La URL `/lista/{token}` es la credencial: cualquiera que la tenga puede leer y editar. No hay propietario, invitados ni permisos.
- La API deja de ser estrictamente de solo lectura: incorpora endpoints de escritura limitados a las tablas de listas. El catalogo sigue siendo propiedad exclusiva de la ingesta.
- Nuevas tablas `listas` y `lista_items` en PostgreSQL, con migracion idempotente y subida de `SCHEMA_VERSION`.
- El token se guarda hasheado y se genera con entropia suficiente para no ser adivinable.
- El portal incorpora un corazon en resultados y ficha, una pagina de lista propia y una pagina de lista compartida. La lista compartida queda fuera de indexacion y no filtra el token en cabeceras `Referer`.
- Se mantiene la ausencia de datos personales: no hay correo, nombre, telefono ni IP persistida. La lista solo contiene identificadores de ediciones, un titulo opcional y marcas de tiempo.
- Limites de abuso: maximo de items por lista, maximo de listas creadas por ventana, caducidad deslizante y borrado oportunista de listas caducadas.

Fuera de alcance:

- Cuentas, login, contrasenas, verificacion por correo y recuperacion de cuenta.
- Varias listas con nombre por usuario y selectores de "anadir a".
- Permisos por persona, invitaciones o colaboracion con roles.
- Avisos de disponibilidad, historial de prestamos o sincronizacion con el OPAC.
- Orden manual de los items.

## Capabilities

### New Capabilities

- `listas-compartidas`: creacion, edicion y consulta de listas de favoritos sin cuenta, identificadas por un token opaco que actua como credencial compartible.

### Modified Capabilities

- `api-portal`: anade los endpoints y el contrato de las listas, y ajusta el limite de escritura de la API para que siga siendo de solo lectura sobre el catalogo.
- `portal-web`: anade el corazon de favoritos, la pagina de lista propia, la pagina de lista compartida y la gestion de la cookie de lista activa.
- `operacion-despliegue`: ajusta la propiedad de escritura para que la API escriba solo las tablas de listas y anade la limpieza de listas caducadas en `init`.

## Impact

- `packages/shared`: modelos `Lista` y `ListaItem`, esquemas Pydantic y subida de `SCHEMA_VERSION`.
- `services/enrich/scripts`: nueva migracion idempotente para las tablas de listas; `init` la aplica antes de arrancar la API.
- `services/api`: router de listas con lectura publica y escritura autenticada por token; el resto de routers sigue en solo lectura.
- `apps/web`: server actions para crear listas y alternar favoritos, paginas `/mi-lista` y `/lista/[token]`, corazon en `RecordCard` y en la ficha.
- `contracts/openapi.json` y `apps/web/lib/api-types.ts`: regenerados con `make openapi` y `make web-types`.
- `docs/ARCHITECTURE.md` y `README.md`: la tabla de propiedad de escritura y la nota de privacidad deben reflejar que la API escribe solo listas y que no se almacenan datos personales.
- Operacion: no hay servicios nuevos. La API necesita permiso de escritura en PostgreSQL, que ya tiene con el usuario actual.
