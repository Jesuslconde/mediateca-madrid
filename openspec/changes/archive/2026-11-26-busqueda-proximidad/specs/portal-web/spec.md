# Spec Delta

## ADDED Requirements

### Requirement: Selector global de código postal

El portal SHALL ofrecer un selector global de código postal para toda España, con autocompletado por código o municipio. La elección SHALL recordarse entre visitas y SHALL reflejarse en la URL de búsqueda. SHALL NOT solicitar geolocalización del navegador.

#### Scenario: Elegir un código postal

- **WHEN** el usuario escribe su código postal o su municipio en el selector global
- **THEN** puede elegir un código postal de toda España
- **AND** no se solicita permiso de geolocalización

#### Scenario: Recordar la elección

- **WHEN** el usuario vuelve al portal después de haber elegido un código postal
- **THEN** el selector restaura esa elección
- **AND** la ficha y la búsqueda la usan como referencia

#### Scenario: Código postal en la URL

- **WHEN** el usuario busca con un código postal elegido
- **THEN** la URL de búsqueda incluye `cp`
- **AND** la URL puede compartirse y abre la misma referencia

### Requirement: Control de radio

La página de resultados SHALL ofrecer un control de radio con opciones predefinidas y una opción sin límite. El radio SHALL combinarse con el código postal y el resto de filtros.

#### Scenario: Aplicar un radio

- **WHEN** el usuario elige un radio con un código postal seleccionado
- **THEN** los resultados se limitan a las sucursales dentro de ese radio
- **AND** el radio aparece en la URL y como filtro activo

#### Scenario: Sin límite

- **WHEN** el usuario elige la opción sin límite
- **THEN** la búsqueda no se acota por distancia
- **AND** se conservan el código postal y el resto de filtros

### Requirement: Selección de bibliotecas cercanas

Con un código postal y un radio, el portal SHALL mostrar las bibliotecas y sucursales resultantes y SHALL permitir buscar en todas, excluir algunas o buscar solo en una.

#### Scenario: Lista de bibliotecas cercanas

- **WHEN** el usuario fija un código postal y un radio
- **THEN** el portal muestra las bibliotecas y sucursales dentro del radio con su distancia
- **AND** puede marcarlas o desmarcarlas

#### Scenario: Excluir bibliotecas

- **WHEN** el usuario desmarca una o varias bibliotecas del conjunto cercano
- **THEN** la búsqueda se limita al resto
- **AND** las excluidas se reflejan en la URL

#### Scenario: Buscar solo en una

- **WHEN** el usuario elige buscar solo en una biblioteca concreta
- **THEN** la búsqueda se limita a esa biblioteca
- **AND** el filtro usa el código estable de la biblioteca o sucursal
