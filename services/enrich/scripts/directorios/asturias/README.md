# Directorio de la Red de Bibliotecas de Asturias

Carga del directorio de la fuente `asturias` (Red de Bibliotecas de Asturias).
Forma parte de las migraciones automáticas: se aplica al iniciar la aplicación
con `python -m mediateca init` o `python -m mediateca migrate`, tanto en una
instalación desde cero como en una actualización. Es idempotente, así que se
puede reejecutar sin duplicar filas.

## Origen

- Directorio: <https://absys.asturias.es/opacbp/imag/ba_directorio.pdf>
- Portal: <https://absys.asturias.es>
- Formato: PDF de 13 páginas
- Descarga: 26 de noviembre de 2026 (última modificación del fichero: 22 de
  enero de 2025)

El PDF publica una ficha por biblioteca o sucursal con concejo, código,
denominación, dirección, teléfono, correo electrónico y horario. Las
bibliotecas aparecen en dos bloques: bibliotecas públicas y bibliotecas
especializadas.

La fuente no publica coordenadas. Para que las sucursales entren en el filtro
por proximidad se usa el centroide del código postal
([kodens-dev/Spain-Postal-Codes](https://github.com/kodens-dev/Spain-Postal-Codes),
MIT), con los municipios del INE mediante
[regi-es/ds-codigos-postales-ine-es](https://github.com/regi-es/ds-codigos-postales-ine-es)
(CC BY 4.0). Es una localización aproximada a nivel de código postal, no una
geocodificación de la dirección.

El PDF repite el código de sucursal `GMFM` para la Biblioteca del Museo
Arqueológico y la Biblioteca del Museo del Ferrocarril, y el código `501` para
la Biblioteca Municipal de Ponga y la Biblioteca del Archivo Histórico de
Asturias. Para no perder filas se conservan como `GMFM`/`GMFM-FERROCARRIL` y
`501`/`501-OVIEDO`.

## Ficheros

- `normalizado.csv`: una fila por sucursal con `fuente`, `codigo_biblioteca`,
  `codigo_sucursal`, `nombre`, `nombre_biblioteca`, `direccion`, `municipio`,
  `codigo_postal`, `latitud` y `longitud`. `nombre_biblioteca` es el de la
  sucursal principal del grupo o, si no existe, el de la primera sucursal.
- `normalizado.metadata.json`: URL, fecha, recuentos y campos de origen.
- `services/enrich/scripts/migrate_sucursales_directorio_asturias.sql`:
  migración idempotente que inserta y actualiza `bibliotecas` y `sucursales` por
  `(fuente, codigo)`.

La copia del PDF descargado y el CSV generado se guardan en
`data/ingesta-directorio/asturias/` (directorio local ignorado por Git).

## Carga

La migración se aplica automáticamente al iniciar la aplicación:

```bash
python -m mediateca init
# o solo las migraciones
python -m mediateca migrate
```

En Docker, el servicio `init` ejecuta `python -m mediateca init` al desplegar.

El script no borra filas ausentes del directorio, no modifica otras fuentes y no
crea ediciones ni ejemplares. Al terminar devuelve el resumen de filas creadas y
actualizadas, además del total con código postal y con coordenadas.

## Resultado de la carga

- Primera ejecución: 127 bibliotecas y 164 sucursales insertadas.
- 127 bibliotecas y 164 sucursales con código postal y coordenadas.
- Segunda ejecución: 0 inserciones y 291 actualizaciones, sin duplicados y sin
  cambios en `ediciones` ni `ejemplares` (0 y 0 antes y después).
- La carga de Aragón (116 bibliotecas y 121 sucursales) queda intacta.
