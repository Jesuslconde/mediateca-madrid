# Spec Delta

## ADDED Requirements

### Requirement: Selección de código postal

La ficha SHALL ofrecer un selector de código postal para establecer la referencia de cercanía, SHALL recordar la elección entre visitas y SHALL permitir limpiarla. SHALL NOT solicitar geolocalización del navegador.

#### Scenario: Seleccionar un código postal

- **WHEN** el usuario elige un código postal en la ficha
- **THEN** la ficha usa ese código postal como referencia de cercanía
- **AND** no se solicita permiso de geolocalización

#### Scenario: Recordar la elección

- **WHEN** el usuario vuelve a abrir una ficha después de haber elegido un código postal
- **THEN** la ficha restaura esa elección
- **AND** mantiene el orden por cercanía

#### Scenario: Limpiar la elección

- **WHEN** el usuario limpia el código postal
- **THEN** la ficha deja de usar una referencia de cercanía
- **AND** vuelve al orden alfabético

#### Scenario: Código postal desconocido

- **WHEN** la elección guardada no corresponde a ningún código postal disponible
- **THEN** la ficha ignora esa elección
- **AND** muestra el orden alfabético

### Requirement: Orden por cercanía

Con un código postal seleccionado, la ficha SHALL ordenar las bibliotecas por distancia aproximada y SHALL mostrar esa distancia. Las bibliotecas sin ubicación SHALL quedar al final; si ninguna tiene ubicación, SHALL mantener el orden alfabético y avisar.

#### Scenario: Orden y distancia

- **WHEN** el usuario selecciona un código postal y las bibliotecas tienen ubicación
- **THEN** la ficha ordena las bibliotecas de menor a mayor distancia aproximada
- **AND** muestra la distancia junto a cada biblioteca

#### Scenario: Sucursal con código postal sin coordenadas

- **WHEN** una sucursal tiene código postal pero no coordenadas
- **THEN** la ficha usa el centroide de ese código postal como su ubicación
- **AND** la incluye en el orden por cercanía

#### Scenario: Bibliotecas sin ubicación

- **WHEN** algunas bibliotecas no tienen coordenadas ni código postal utilizable
- **THEN** esas bibliotecas quedan al final del orden
- **AND** se ordenan alfabéticamente entre ellas

#### Scenario: Ninguna ubicación disponible

- **WHEN** ninguna biblioteca de la ficha tiene ubicación utilizable
- **THEN** la ficha mantiene el orden alfabético
- **AND** muestra un aviso de que no hay datos de ubicación disponibles

#### Scenario: Sin código postal

- **WHEN** no hay un código postal seleccionado
- **THEN** la ficha mantiene el orden alfabético actual

### Requirement: Atribución de códigos postales

El portal MUST mostrar en la ficha la atribución de las fuentes de los centroides de códigos postales utilizados para calcular las distancias.

#### Scenario: Atribución visible

- **WHEN** el usuario consulta una ficha con ordenación por cercanía disponible
- **THEN** el portal muestra la atribución de las fuentes de los códigos postales
- **AND** la atribución no se oculta al ordenar las bibliotecas
