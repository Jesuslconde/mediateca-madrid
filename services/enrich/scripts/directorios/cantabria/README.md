# Directorio de la Red de Bibliotecas de Cantabria

Carga del directorio de la fuente `cantabria` (Sistema de Lectura Pública de
Cantabria). Forma parte de las migraciones automáticas: se aplica al iniciar la
aplicación con `python -m mediateca init` o `python -m mediateca migrate`, tanto
en una instalación desde cero como en una actualización. Es idempotente, así que
se puede reejecutar sin duplicar filas.

## Origen

- Directorio de Bibliotecas Españolas (DIMBE):
  <https://directoriobibliotecas.mcu.es/dimbe.cmd>
- Descarga completa en JSON:
  <https://directoriobibliotecas.mcu.es/dimbe.cmd?apartado=descarga&accion=descargar&completa=si&formato=json>
- Catálogo del SLPC: <https://slpc.cantabria.es/cgi-bin/abnetopac2>
- Descarga: 26 de noviembre de 2026

DIMBE publica una ficha por biblioteca con denominación, dirección, municipio,
código postal, coordenadas y, cuando existe, el código `SUBC` del catálogo. La
descarga completa contiene 104 registros de Cantabria.

El selector `subcat` del OPAC del SLPC publica el árbol completo de la red con
los códigos que usa el catálogo: 56 bibliotecas (44 `BBP` de bibliotecas
públicas y 12 `BBE` de bibliotecas especializadas) y 66 sucursales. Se usa ese
árbol para la identidad de bibliotecas y sucursales, y DIMBE para la ubicación.

Cuatro centros no tienen ficha en DIMBE: Alfoz de Lloredo, Liérganes, Riotuerto
y Santiurde de Toranzo. Su dirección y código postal se han completado con el
ayuntamiento o el centro cultural, y sus coordenadas con OpenStreetMap. Las
coordenadas de DIMBE son de edificio o de núcleo y pueden ser aproximadas; no se
geocodifican direcciones.

## Ficheros

- `normalizado.csv`: una fila por sucursal con `fuente`, `codigo_biblioteca`,
  `codigo_sucursal`, `nombre`, `nombre_biblioteca`, `direccion`, `municipio`,
  `codigo_postal`, `latitud` y `longitud`.
- `normalizado.metadata.json`: URL, fecha, recuentos, campos de origen e
  incidencias.
- `services/enrich/scripts/migrate_sucursales_directorio_cantabria.sql`:
  migración idempotente que inserta y actualiza `bibliotecas` y `sucursales` por
  `(fuente, codigo)`.

La copia del JSON de DIMBE, el selector del OPAC y el CSV generado se guardan en
`data/ingesta-directorio/cantabria/` (directorio local ignorado por Git).

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

- Primera ejecución: 56 bibliotecas y 67 sucursales insertadas.
- 56 bibliotecas y 67 sucursales con código postal y coordenadas.
- Segunda ejecución: 0 inserciones y 123 actualizaciones (56 bibliotecas y 67
  sucursales), sin duplicados y sin cambios en `ediciones` ni `ejemplares`
  (0 y 0 antes y después).
- Las cargas de Aragón (116 bibliotecas y 121 sucursales) y Asturias (127
  bibliotecas y 164 sucursales) quedan intactas.
