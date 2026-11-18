# Tasks

## 1. Modelo compartido y migracion

- [x] 1.1 Crear `packages/shared/src/mediateca_shared/lists.py` con los modelos `Lista` y `ListaItem` descritos en `design.md`; verificar que `python -c "from mediateca_shared.lists import Lista, ListaItem"` funciona dentro de la imagen del worker.
- [x] 1.2 Importar los modelos nuevos desde `packages/shared/src/mediateca_shared/models.py` para que `Base.metadata.create_all` los registre; verificar que `listas` y `lista_items` aparecen en `Base.metadata.tables`.
- [x] 1.3 Anadir los esquemas Pydantic `ListaOut`, `ListaItemOut`, `ListaCreatedOut` e `ItemMutationOut` en `packages/shared` y reexportarlos desde `mediateca/api/schemas.py`; verificar que la importacion desde la API no falla.
- [x] 1.4 Subir `SCHEMA_VERSION` de `5` a `6` en `packages/shared/src/mediateca_shared/version.py`; verificar con `make migrate && make check-schema` que la API acepta el esquema.
- [x] 1.5 Crear `services/enrich/scripts/migrate_listas.sql` idempotente con las tablas, claves, indices y la actualizacion de `schema_meta`; verificar ejecutando `make migrate` dos veces seguidas sin error y revisando las tablas con `make psql`.
- [x] 1.6 Anadir el comando `clean-lists` al CLI de `services/enrich` para borrar listas con `expires_at` vencido; verificar con una lista caducada sembrada a mano que se borra y una vigente que permanece.
- [x] 1.7 Enganchar `python -m mediateca clean-lists` en el servicio `init` de `docker-compose.yml` y `deploy/portainer-stack.yml`, despues de `migrate`; verificar que `make init` termina correctamente y registra la limpieza.
- [x] 1.8 Anadir pruebas en `packages/shared/tests/test_lists.py` para valores por defecto, clave compuesta y cascade; verificar con `make test-shared`.
- [x] 1.9 Actualizar la tabla de propiedad de escritura de `docs/ARCHITECTURE.md` para indicar que la API escribe solo en `listas` y `lista_items`; verificar que la tabla y el texto de la seccion siguen siendo coherentes.

## 2. API de listas

- [x] 2.1 Crear `services/api/src/mediateca/api/routers/lists.py` con generacion de token, hash SHA-256, creacion, consulta, renombrado y alta/baja de elementos; verificar con `TestClient` que crear y consultar una lista devuelve el titulo y los elementos esperados.
- [x] 2.2 Implementar las reglas de error y los codigos 404, 409, 422 y la idempotencia al anadir; verificar cada caso con pruebas de API.
- [x] 2.3 Implementar la serializacion de elementos con `join` a `ediciones` y el respaldo `titulo_snapshot` cuando la ficha ya no existe; verificar que un elemento huerfano devuelve `disponible: false` y el titulo guardado.
- [x] 2.4 Renovar `updated_at` y `expires_at` en cada mutacion y rechazar listas por encima de 200 elementos; verificar con pruebas que la fecha avanza y que el elemento 201 devuelve 409.
- [x] 2.5 Anadir el limite de creacion en memoria por `X-Client-IP`, sin persistir el identificador, con cubo global de respaldo; verificar que la peticion que supera la ventana devuelve 429.
- [x] 2.6 Anadir un filtro de logging que enmascare el token en las rutas `/api/lists/{token}`; verificar que una peticion deja el token oculto en el log de acceso.
- [x] 2.7 Registrar el router en `services/api/src/mediateca/api/main.py` con prefijo `/api`; verificar que `GET /openapi.json` incluye las cinco rutas de lista.
- [x] 2.8 Crear `services/api/tests/test_lists.py` con SQLite en memoria y `StaticPool`, cubriendo creacion, consulta, idempotencia, lista llena, token invalido, edicion inexistente, orden de elementos, ficha desaparecida y limite de creacion; verificar con `make test-api`.
- [x] 2.9 Regenerar el contrato y los tipos con `make contracts`; verificar que `contracts/openapi.json` y `apps/web/lib/api-types.ts` incluyen los esquemas de lista y que el segundo no se edita a mano.
- [x] 2.10 Actualizar la tabla de endpoints de `README.md` con las rutas de lista y la nota de escritura acotada; verificar que las rutas documentadas coinciden con el contrato generado.

## 3. Portal: cookie, acciones y corazon

- [x] 3.1 Crear `apps/web/lib/lists.ts` con las funciones de cliente para crear, consultar, anadir, quitar y renombrar listas; verificar que compila con `npx tsc --noEmit` en `apps/web`.
- [x] 3.2 Crear `apps/web/lib/list-cookie.ts` para leer, escribir y limpiar la cookie `mediateca_lista` con `HttpOnly`, `SameSite=Lax`, `Secure` en produccion y `Max-Age` de 180 dias; verificar los atributos en la respuesta del navegador.
- [x] 3.3 Crear `apps/web/app/actions/lists.ts` con las Server Actions `createListAction`, `toggleFavoriteAction`, `removeItemAction`, `renameListAction` y `adoptListAction`, incluida la revalidacion de rutas; verificar el ciclo completo desde la interfaz local.
- [x] 3.4 Crear `apps/web/components/FavoriteButton.tsx` con actualizacion optimista, formulario de respaldo sin JavaScript, `aria-pressed`, etiqueta accesible y aviso de lista llena; verificar con teclado, sin JavaScript y con una lista de 200 elementos.
- [x] 3.5 Integrar el boton en `apps/web/components/RecordCard.tsx` y en `apps/web/app/registro/[titn]/page.tsx`, calculando el conjunto de `titn` guardados una vez por pagina; verificar que el corazon refleja el estado tras recargar.
- [x] 3.6 Comprobar que guardar o quitar un favorito conserva termino, filtros, orden y pagina en resultados y en la ficha; verificar manualmente con una busqueda filtrada y paginada.
- [x] 3.7 Verificar que `apps/web` compila con `npm run build` y que no se anaden dependencias nuevas al `package.json`.

## 4. Portal: paginas, enlace y privacidad

- [x] 4.1 Crear `apps/web/app/mi-lista/page.tsx` con estado vacio, listado, recuento, formulario de renombrado y accion de quitar; verificar los estados con y sin cookie, y con una cookie que apunte a una lista inexistente.
- [x] 4.2 Crear `apps/web/app/lista/[token]/page.tsx` con el mismo contenido que `/mi-lista`, `notFound()` para tokens invalidos y el componente `AdoptList` que fija la cookie como lista activa; verificar con un enlace valido y uno inexistente.
- [x] 4.3 Crear `apps/web/components/ShareLink.tsx` para copiar el enlace compartible con respaldo de texto seleccionable; verificar la copia en un navegador con y sin permiso de portapapeles.
- [x] 4.4 Anadir a la cabecera de `apps/web/app/layout.tsx` el acceso a la lista activa con recuento; verificar que el numero se actualiza al guardar y quitar favoritos.
- [x] 4.5 Declarar `robots: { index: false, follow: false }` en la pagina de lista, anadir `apps/web/app/robots.ts` con `/lista/` desautorizado y configurar `Referrer-Policy: no-referrer` para `/lista/:path*` y `/mi-lista` en `next.config.mjs`; verificar las cabeceras con `curl -I` y la directiva en el HTML.
- [x] 4.6 Revisar los estados vacio, lista sin elementos, token invalido y error de API para que ofrezcan una salida clara; verificar manualmente cada uno.
- [x] 4.7 Actualizar `README.md` con el uso de la lista, el caracter editable del enlace y la nota de que no se almacenan datos personales; verificar que el texto no contradice la tabla de propiedad ni la seccion de privacidad.

## 5. Integracion y despliegue

- [x] 5.1 Recorrer el flujo completo en local: crear lista, guardar desde resultados y ficha, abrir el enlace en una ventana privada, editar desde ahi y comprobar que ambos navegadores ven los cambios.
- [x] 5.2 Sembrar una lista caducada y una lista con 200 elementos para verificar la limpieza de `init` y el rechazo del elemento 201.
- [x] 5.3 Ejecutar `make test`, `make lint` y `make check-schema`; verificar que todo pasa con el esquema 6.
- [x] 5.4 Probar la actualizacion sobre una base existente en version 5: `make init` debe aplicar la migracion y la API debe arrancar sin errores.
- [x] 5.5 Verificar el rollback documentado: dejar las tablas creadas, restaurar `schema_meta.schema_version` a `5` y comprobar que la version anterior de la API arranca.
- [x] 5.6 Construir las dos imagenes con `make build` y verificar que la API responde y el portal renderiza `/mi-lista` y `/lista/{token}`.
- [x] 5.7 Ejecutar `openspec validate listas-compartidas --strict` y corregir cualquier aviso antes de cerrar el cambio.

## Workflow follow-up

- Archivar el cambio despues de la revision y del despliegue, cuando las pruebas y la verificacion manual esten completas.
