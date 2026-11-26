# Directorio de la Red de Bibliotecas de Aragón

Carga manual del directorio de la fuente `aragon` (Red de Bibliotecas de
Aragón). No forma parte de las migraciones automáticas: se ejecuta una vez sobre
el entorno de datos y se puede repetir sin duplicar filas.

## Origen

- Bibliotecas: `https://opendata.aragon.es/GA_OD_Core/download?resource_id=282&formato=json`
- Sucursales: `https://opendata.aragon.es/GA_OD_Core/download?resource_id=283&formato=json`
- Catálogo: <https://opendata.aragon.es/datos/catalogo/dataset/catalogo-de-la-red-de-bibliotecas-de-aragon-en-formatos-abiertos>
- Licencia: CC BY 4.0
- Descarga: 25 de noviembre de 2026

El recurso de bibliotecas aporta `bicobi`, `bidesc`, `bidir1` y `bidir2`; el de
sucursales aporta `sucobi`, `sucosu`, `sudesc`, `sudir1` y `sudir2`. Los códigos
`bicobi` y `sucobi` identifican la biblioteca; `sucosu` identifica la sucursal
que usa el OPAC en los ejemplares.

La fuente no publica coordenadas. Para que las sucursales entren en el filtro por
proximidad se usa el centroide del código postal
([kodens-dev/Spain-Postal-Codes](https://github.com/kodens-dev/Spain-Postal-Codes),
MIT). Cuando un código postal no tiene centroide propio se usa la media de los
centroides de su municipio. Es una localización aproximada a nivel de código
postal, no una geocodificación de la dirección.

## Ficheros

- `normalizado.csv`: una fila por sucursal con `fuente`, `codigo_biblioteca`,
  `codigo_sucursal`, `nombre`, `nombre_biblioteca`, `direccion`, `municipio`,
  `codigo_postal`, `latitud` y `longitud`.
- `normalizado.metadata.json`: URL, fecha, recuentos y campos de origen.
- `carga.sql`: inserción y actualización idempotente de `bibliotecas` y
  `sucursales` por `(fuente, codigo)`.

La copia de los ficheros fuente descargados y el CSV generado se guardan en
`data/ingesta-directorio/aragon/` (directorio local ignorado por Git).

## Carga

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/enrich/scripts/directorios/aragon/carga.sql
```

El script no borra filas ausentes del directorio, no modifica otras fuentes y no
crea ediciones ni ejemplares. Al terminar devuelve el resumen de filas creadas y
actualizadas, además del total con código postal y con coordenadas.

## Resultado de la carga

- 116 bibliotecas y 121 sucursales insertadas.
- 116 bibliotecas y 121 sucursales con código postal y coordenadas.
- Segunda ejecución: 0 inserciones y 237 actualizaciones, sin duplicados y sin
  cambios en `ediciones` ni `ejemplares`.
