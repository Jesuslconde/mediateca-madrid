# Spec Delta

## ADDED Requirements

### Requirement: Endpoint de datos dinámicos del dashboard

El dashboard MUST exponer endpoints de solo lectura que devuelven en formato JSON los datos dinámicos de Inicio y de Tareas. Estos endpoints SHALL devolver la misma información que muestran las páginas y SHALL NOT crear, modificar ni eliminar datos.

#### Scenario: Datos de Inicio

- **WHEN** se consulta el endpoint de datos de Inicio
- **THEN** devuelve la salud del worker, el resumen de trabajos por estado, tipo y fuente, la cobertura del catálogo y las métricas de ingesta
- **AND** no modifica trabajos, ediciones ni configuración

#### Scenario: Datos de Tareas

- **WHEN** se consulta el endpoint de datos de Tareas
- **THEN** devuelve los trabajos recientes y el estado activo de cada tipo de trabajo
- **AND** no modifica trabajos, ediciones ni configuración

#### Scenario: Base de datos no disponible

- **WHEN** la base de datos no responde al consultar un endpoint de datos dinámicos
- **THEN** el endpoint devuelve un estado de error o degradado comprensible
- **AND** no expone trazas internas ni detalles de conexión

## MODIFIED Requirements

### Requirement: Actualización automática

El sistema SHALL refrescar automáticamente los datos dinámicos de las páginas de Inicio y Tareas con un intervalo configurable, obteniendo únicamente la información que cambia mediante una llamada AJAX a un endpoint, sin recargar la página completa ni requerir que el operador la recargue manualmente. La página de Configuración SHALL NOT refrescarse automáticamente para no perder cambios en los formularios.

#### Scenario: Refresco periódico

- **WHEN** transcurre el intervalo de refresco configurado
- **THEN** la vista actualiza los datos mostrados en Inicio y Tareas mediante una llamada AJAX, sin recargar la página completa
- **AND** el intervalo puede cambiarse mediante configuración de entorno

#### Scenario: Refresco parcial de Tareas

- **WHEN** transcurre el intervalo de refresco configurado en la página de Tareas
- **THEN** la página actualiza la tabla de trabajos recientes y el estado activo de las tareas sin recargar la página completa
- **AND** los valores introducidos en los formularios de acciones bajo demanda no se pierden con el refresco

#### Scenario: Configuración sin refresco

- **WHEN** el operador está editando un formulario en Configuración
- **THEN** la página no se refresca automáticamente
- **AND** los valores introducidos no se pierden por el refresco

#### Scenario: Fallo en la actualización parcial

- **WHEN** la base de datos no responde durante una actualización parcial
- **THEN** la página muestra un estado degradado comprensible sin recargarse
- **AND** no expone trazas internas ni detalles de conexión
