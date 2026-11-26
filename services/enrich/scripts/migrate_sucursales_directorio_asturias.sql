-- Migracion de datos del directorio de la Red de Bibliotecas de Asturias.
--
-- Se aplica automaticamente desde `python -m mediateca migrate` y desde
-- `python -m mediateca init`, tanto en instalaciones desde cero como en
-- actualizaciones. Es idempotente.
--
-- Fuente:
--   Directorio: https://absys.asturias.es/opacbp/imag/ba_directorio.pdf
--   Portal:     https://absys.asturias.es
--   Descarga:   2026-11-26
--
-- El directorio es un PDF publicado por el Principado de Asturias con una ficha
-- por biblioteca o sucursal: concejo, codigo, denominacion, direccion y
-- contacto. No publica coordenadas. Se usa el centroide del codigo postal
-- (kodens-dev/Spain-Postal-Codes, MIT; municipios del INE via
-- regi-es/ds-codigos-postales-ine-es, CC BY 4.0) para que las sucursales entren
-- en el filtro por proximidad. Es una localizacion aproximada a nivel de codigo
-- postal, no una geocodificacion de la direccion.
--
-- El PDF repite el codigo de sucursal GMFM para dos bibliotecas especializadas
-- de Gijon y el codigo 501 para Ponga y el Archivo Historico de Asturias. Para
-- no perder filas se desambiguan como GMFM-FERROCARRIL y 501-OVIEDO.
--
-- Operacion idempotente: inserta o actualiza bibliotecas y sucursales por
-- (fuente, codigo), sin borrar filas ausentes ni tocar otras fuentes, y sin
-- crear ediciones ni ejemplares. Se puede ejecutar varias veces.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM fuentes WHERE codigo = 'asturias') THEN
        RAISE EXCEPTION
            'No existe la fuente asturias; aplica las migraciones antes de la carga';
    END IF;
END
$$;

CREATE TEMP TABLE tmp_directorio_asturias (
    codigo_biblioteca VARCHAR(64) NOT NULL,
    codigo_sucursal VARCHAR(64) NOT NULL,
    nombre VARCHAR(500) NOT NULL,
    nombre_biblioteca VARCHAR(500) NOT NULL,
    direccion TEXT,
    municipio VARCHAR(250),
    codigo_postal VARCHAR(5),
    latitud DOUBLE PRECISION,
    longitud DOUBLE PRECISION
) ON COMMIT DROP;

INSERT INTO tmp_directorio_asturias (
    codigo_biblioteca, codigo_sucursal, nombre, nombre_biblioteca, direccion,
    municipio, codigo_postal, latitud, longitud
)
VALUES
    ('011', '011', 'Biblioteca Pública Municipal "Celestino Valledor"', 'Biblioteca Pública Municipal "Celestino Valledor"', 'C/ Donato Fernández, 2', 'Allande', '33880', 43.278547, -6.620769943),
    ('022', '022', 'Biblioteca Pública Municipal "Lorenzo Rodríguez-Castellano"', 'Biblioteca Pública Municipal "Lorenzo Rodríguez-Castellano"', 'Av. Constitución, 45', 'Aller', '33686', 43.151295, -5.6153194469999),
    ('023', '023', 'Biblioteca Pública Municipal "Jesús Barettini"', 'Biblioteca Pública Municipal "Jesús Barettini"', 'Av. Marianes, 53', 'Aller', '33684', 43.182185, -5.753382329),
    ('021', '021', 'Biblioteca Pública Municipal "Toribio Velasco"', 'Biblioteca Pública Municipal "Toribio Velasco"', 'C/ Eloy Martino, s/n', 'Aller', '33670', 43.171332476, -5.7400949999999),
    ('031', '031', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Pl. la Pastorina', 'Amieva', '33558', 43.225275, -5.074657827),
    ('041', '041', 'Biblioteca Pública Municipal "Bances Candamo"', 'Biblioteca Pública Municipal "Bances Candamo"', 'Pl. Álvarez Acebal, 2', 'Avilés', '33402', 43.54967, -5.9242163389999),
    ('044', '044', 'Biblioteca Pública Municipal de La Carriona', 'Biblioteca Pública Municipal de La Carriona', 'C/ Castilla, 13', 'Avilés', '33401', 43.572401484, -5.92655),
    ('043', '043', 'Biblioteca Pública Municipal de La Luz', 'Biblioteca Pública Municipal de La Luz', 'Pl. Fray Junípero Serra, 2', 'Avilés', '33403', 43.53908, -5.919568134),
    ('042', '042', 'Biblioteca Pública Municipal de Los Canapés', 'Biblioteca Pública Municipal de Los Canapés', 'C/ La Concordia, 3', 'Avilés', '33402', 43.54967, -5.9242163389999),
    ('051', '051', 'Biblioteca Pública Municipal "Cardenal Cienfuegos"', 'Biblioteca Pública Municipal "Cardenal Cienfuegos"', 'Pl. del Parque', 'Belmonte de Miranda', '33830', 43.281605, -6.2198527969999),
    ('061', '061', 'Biblioteca Pública Municipal "Padre Severiano Montes"', 'Biblioteca Pública Municipal "Padre Severiano Montes"', 'San Julián de Bimenes', 'Bimenes', '33527', 43.340819568, -5.5626549999999),
    ('071', '071', 'Biblioteca Pública Municipal "Acevedo y Huelves"', 'Biblioteca Pública Municipal "Acevedo y Huelves"', 'Av. Asturias', 'Boal', '33720', 43.42778, -6.8235338709999),
    ('082', '082', 'Biblioteca Pública Municipal "Ateneo Cabraliego"', 'Biblioteca Pública Municipal "Ateneo Cabraliego"', 'Crta. de Arenas a Arangas', 'Cabrales', '33554', 43.268804209, -4.80308),
    ('082', 'CCAR', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal "Ateneo Cabraliego"', 'Casa de Cultura', 'Cabrales', '33555', 43.300238651, -4.877695),
    ('091', '091', 'Biblioteca Pública Municipal "María Josefa Canellada"', 'Biblioteca Pública Municipal "María Josefa Canellada"', 'C/ Jesús Arango, 4', 'Cabranes', '33310', 43.419234114, -5.3959449999999),
    ('101', '101', 'Biblioteca Pública Municipal "Francisco Cuervo y Valdés"', 'Biblioteca Pública Municipal "Francisco Cuervo y Valdés"', 'Palacio Valdés Bazán', 'Candamo', '33828', 43.42523, -6.0837869989999),
    ('121', '121', 'Biblioteca Pública Municipal "Santa Cruz"', 'Biblioteca Pública Municipal "Santa Cruz"', 'C/ La Cárcel, 13', 'Cangas de Onís', '33550', 43.35037, -5.120789724),
    ('111', '111', 'Biblioteca Pública Municipal "Padre Luis Alfonso de Carvallo"', 'Biblioteca Pública Municipal "Padre Luis Alfonso de Carvallo"', 'Casa de Cultura "Palacio de Omaña", Plaza Mayor, s/n', 'Cangas del Narcea', '33800', 43.1781, -6.5485385499999),
    ('131', '131', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', NULL, 'Caravia', '33344', 43.458265, -5.17617324),
    ('141', '141', 'Biblioteca Pública Municipal "Carlos González Posada"', 'Biblioteca Pública Municipal "Carlos González Posada"', 'C/ Enrique Alau Flórez, 1', 'Carreño', '33430', 43.556715882, -5.748345),
    ('151', '151', 'Biblioteca Pública Municipal "Sociedad Casina de La Habana"', 'Biblioteca Pública Municipal "Sociedad Casina de La Habana"', 'Antiguas escuelas El Cruce, s/n', 'Caso', '33990', 43.208685, -5.310317787),
    ('161', '161', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Alfonso I, 3', 'Castrillón', '33450', 43.568641667, -5.9745399999999),
    ('162', '162', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Centro Cultural "El Agüil", C/ Carreño, 10', 'Castrillón', '33405', 43.57479, -5.95436),
    ('171', '171', 'Biblioteca Popular Circulante "Menéndez Pelayo"', 'Biblioteca Popular Circulante "Menéndez Pelayo"', 'Parque Vicente Loriente, s/n', 'Castropol', '33760', 43.522165, -7.0240806329999),
    ('172', '172', 'Biblioteca Pública Municipal "Miguel García Teijeiro"', 'Biblioteca Pública Municipal "Miguel García Teijeiro"', 'Av. De Trénor - Edif. Torre del Reloj', 'Castropol', '33794', 43.532065, -6.942206401),
    ('181', '181', 'Biblioteca Pública Municipal "Gonzálo Anes"', 'Biblioteca Pública Municipal "Gonzálo Anes"', 'Barrio Rabeirón, s/n', 'Coaña', '33716', 43.553245, -6.741184607),
    ('191', '191', 'Biblioteca Pública Municipal "Pedro Caravia"', 'Biblioteca Pública Municipal "Pedro Caravia"', 'Av. Del Sueve, 7 Bajo', 'Colunga', '33320', 43.484235564, -5.26897),
    ('191', 'CLAS', 'Centro de Servicios Múltiples "El Piqueru"', 'Biblioteca Pública Municipal "Pedro Caravia"', 'La Colegiata, 12', 'Colunga', '33330', 43.514938181, -5.273245),
    ('202', '202', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Hermanas Bobes, 2 Bajo-bloque B', 'Corvera', '33470', 43.494989353, -5.85955),
    ('201', '201', 'Biblioteca Pública Municipal "Ángel González"', 'Biblioteca Pública Municipal "Ángel González"', 'Centro Tomás y Valiente, C/ Rubén Darío, s/n, 2ª planta', 'Corvera', '33404', 43.54037, -5.8866078839999),
    ('203', '203', 'Biblioteca Pública Municipal “José Ramón Rodríguez”', 'Biblioteca Pública Municipal “José Ramón Rodríguez”', 'C/ Pepín de Pría, 9', 'Corvera', '33404', 43.54037, -5.8866078839999),
    ('204', '204', 'Biblioteca de Trasona', 'Biblioteca de Trasona', 'C/ El Pedrero, 5', 'Corvera', '33468', 43.548315, -5.8768418929999),
    ('211', '211', 'Biblioteca Pública Municipal "Armando Palacio Valdés"', 'Biblioteca Pública Municipal "Armando Palacio Valdés"', 'C/ García de la Concha', 'Cudillero', '33150', 43.56106, -6.145163575),
    ('212', '212', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', NULL, 'Cudillero', '33156', 43.56687, -6.240027937),
    ('222', '222', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Ctra. General, s/n', 'Degaña', '33812', 42.93491, -6.6029972229999),
    ('231', '231', 'Biblioteca Pública Municipal "As Quintas"', 'Biblioteca Pública Municipal "As Quintas"', 'Complejo Cultural "As Quintas"', 'El Franco', '33750', 43.551845, -6.8300468479999),
    ('24', '24', 'Biblioteca Pública "Jovellanos"', 'Biblioteca Pública "Jovellanos"', 'C/ Jovellanos, 23', 'Gijón', '33206', 43.541935, -5.6671501449999),
    ('24M', '24M', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Fco. Tomás y Valiente, 1', 'Gijón', '33201', 43.546634765, -5.66369),
    ('24M', '24M03', 'Biblioteca Pública Municipal de Pumarín-Gijón Sur', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Ramón Areces, 7', 'Gijón', '33211', 43.513625, -5.6961005109999),
    ('24M', '24M02', 'Biblioteca Pública Municipal de Roces "Alfonso Camín"', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Salvador Allende, 13', 'Gijón', '33211', 43.513625, -5.6961005109999),
    ('24M', '24M06', 'Biblioteca Pública Municipal de Vega-La Camocha', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Charles Chaplín, s/n', 'Gijón', '33350', 43.469645, -5.657223412),
    ('24M', '24M05', 'Biblioteca Pública Municipal de Contrueces', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Río Nalón, 2', 'Gijón', '33210', 43.52317, -5.6697657249999),
    ('24M', '24M04', 'Biblioteca Pública Municipal de El Coto "Luis Sepúlveda"', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'Pl. de la República, s/n', 'Gijón', '33204', 43.52816, -5.6423131359999),
    ('24M', '24M08', 'Biblioteca Pública Municipal de El Llano', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Rio de Oro, 37', 'Gijón', '33209', 43.518755, -5.6588533509999),
    ('24M', '24M10', 'Biblioteca Pública Municipal de El Natahoyo', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ La Estrella, s/n', 'Gijón', '33212', 43.560355, -5.704077733),
    ('24M', '24M00', 'Biblioteca Pública Municipal de Polígono de Pumarín', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Puerto de Piedrafita, 3', 'Gijón', '33207', 43.53479, -5.6744224089999),
    ('24M', '24M09', 'Biblioteca Pública Municipal de La Arena "Pachín de Melás"', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Canga Argüelles, 16-18', 'Gijón', '33203', 43.539555, -5.618891536),
    ('24M', '24M01', 'Biblioteca Pública Municipal de La Calzada', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'C/ Ateneo Obrero de La Calzada, 1', 'Gijón', '33212', 43.560355, -5.704077733),
    ('24M', '24M07', 'Biblioteca Pública Municipal de Montiana', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'Ctra. de Veriña a San Andrés, nº 3540', 'Gijón', '33691', 43.53357, -5.741511766),
    ('251', '251', 'Biblioteca Pública Municipal "Mariano Suárez Pola"', 'Biblioteca Pública Municipal "Mariano Suárez Pola"', 'Parque Zapardel, s/n', 'Gozón', '33440', 43.608545, -5.8513505),
    ('261', '261', 'Biblioteca Pública Municipal "Valentín Andrés"', 'Biblioteca Pública Municipal "Valentín Andrés"', 'Palacio Valdecárzana (Casa de Cultura), C/ Cerro de la Muralla, s/n', 'Grado', '33820', 43.38697, -6.075496594),
    ('271', '271', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ El Salvador, 6', 'Grandas de Salime', '33730', 43.193989448, -6.8992749999999),
    ('291', '291', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Pl. del Ayuntamiento, 1', 'Illano', '33734', 43.34071, -6.879370782),
    ('312', '312', 'Biblioteca Pública Municipal "Alberto Vega"', 'Biblioteca Pública Municipal "Alberto Vega"', 'Pl. Merediz, s/n', 'Langreo', '33930', 43.318132357, -5.6967099999999),
    ('313', '313', 'Biblioteca Pública Municipal "Federico García Lorca"', 'Biblioteca Pública Municipal "Federico García Lorca"', 'Polígono Residencial de Riaño, s/n', 'Langreo', '33920', 43.33144, -5.725282179),
    ('311', '311', 'Biblioteca Pública Municipal "Escuelas Dorado"', 'Biblioteca Pública Municipal "Escuelas Dorado"', 'C/ Dorado, 6', 'Langreo', '33900', 43.278695978, -5.676160019),
    ('541', '541', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', NULL, 'Las Regueras', '33190', 43.427465, -5.9701611999999),
    ('322', '322', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ 1º de Mayo', 'Laviana', '33970', 43.25748, -5.581187073),
    ('323', '323', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'La Bolera', 'Laviana', '33992', 43.256953796, -5.4965549999999),
    ('321', '321', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Pl. La Pontona', 'Laviana', '33980', 43.243514574, -5.5619149999999),
    ('332', '332', 'Centro de Lectura "La Casona"', 'Centro de Lectura "La Casona"', 'C/ Alfonso Llanes Alonso, 7', 'Lena', '33620', 43.108045, -5.812418067),
    ('331', '331', 'Biblioteca Pública Municipal "Ramón Menéndez Pidal"', 'Biblioteca Pública Municipal "Ramón Menéndez Pidal"', 'Pl Alfonso X El Sabio, 7', 'Lena', '33630', 43.154276756, -5.8315449999999),
    ('333', '333', 'Centro de Lectura de Villayana', 'Centro de Lectura de Villayana', 'C/ La Estación, 1', 'Lena', '33695', 43.1853, -5.8056656819999),
    ('352', '352', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Lg. Pondal, 5', 'Llanera', '33690', 43.44711, -5.832410497),
    ('351', '351', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Av. Prudencio González, 10', 'Llanera', '33424', 43.442380491, -5.8567249999999),
    ('361', '361', 'Biblioteca Pública Municipal "Cardenal Inguanzo"', 'Biblioteca Pública Municipal "Cardenal Inguanzo"', 'C/ Celso Amieva, esquina Avda. de las Gaviotas, s/n', 'Llanes', '33500', 43.4214, -4.756672798),
    ('362', '362', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Casa de Cultura "Valle de San Jorge"', 'Llanes', '33592', 43.42563, -4.950460327),
    ('363', '363', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Centro Cívico, C/ La Cultural, s/n', 'Llanes', '33594', 43.41892, -4.8651662779999),
    ('364', '364', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Casa de Cultura', 'Llanes', '33508', 43.369454926, -4.9080499999999),
    ('371', '371', 'Biblioteca Pública Municipal "Vital Aza"', 'Biblioteca Pública Municipal "Vital Aza"', 'C/ Manuel Llaneza, 8', 'Mieres', '33600', 43.24777104, -5.776404),
    ('372', '372', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Polideportivo 1ª Planta', 'Mieres', '33612', 43.196061, -5.778810785),
    ('373', '373', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'El Parque', 'Mieres', '33610', 43.211105, -5.714928082),
    ('374', '374', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Dr. Julio Rodríguez Vigil, s/n', 'Mieres', '33640', 43.203095, -5.801441605),
    ('381', '381', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Av. Mont-Sacro', 'Morcín', '33162', 43.28113, -5.901345211),
    ('392', '392', 'Biblioteca Pública Municipal "Tomás García Sampedro"', 'Biblioteca Pública Municipal "Tomás García Sampedro"', 'C/ Teresina, 15', 'Muros de Nalón', '33130', 43.557165, -6.09067154),
    ('391', '391', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Pl. del Marqués, 7', 'Muros de Nalón', '33138', 43.547495, -6.1058462579999),
    ('401', '401', 'Biblioteca Pública Municipal "José Fernández Guerra"', 'Biblioteca Pública Municipal "José Fernández Guerra"', 'C/ Villabona, 2', 'Nava', '33520', 43.35891, -5.507203659),
    ('411', '411', 'Biblioteca Pública Municipal "Carlos Peláez"', 'Biblioteca Pública Municipal "Carlos Peláez"', 'C/ Antonio Fernández Vallina, 6', 'Navia', '33710', 43.543130226, -6.723018286),
    ('412', '412', 'Biblioteca Pública Municipal "Jovellanos"', 'Biblioteca Pública Municipal "Jovellanos"', 'Av. Juan Pérez Villamil, 2', 'Navia', '33790', 43.5629, -6.6419797749999),
    ('421', '421', 'Biblioteca Pública Municipal "Alonso Marcos de Llanes"', 'Biblioteca Pública Municipal "Alonso Marcos de Llanes"', 'C/ De la Libertad, 12', 'Noreña', '33180', 43.39672, -5.7085106819999),
    ('431', '431', 'Biblioteca Pública Municipal "Hermanos Álvarez Marcos"', 'Biblioteca Pública Municipal "Hermanos Álvarez Marcos"', 'Centro Municipal "Hermanos Álvarez Marcos"', 'Onís', '33556', 43.294877857, -4.99204),
    ('44', '44', 'Biblioteca de Asturias "Ramón Pérez de Ayala" / BPE Oviedo', 'Biblioteca de Asturias "Ramón Pérez de Ayala" / BPE Oviedo', 'Pl. Daoiz y Velarde, 11', 'Oviedo', '33009', 43.358975, -5.8422330559999),
    ('44M', '44M', 'Coordinación Bibliotecaria Municipal', 'Coordinación Bibliotecaria Municipal', 'Campo de San Francisco, s/n', 'Oviedo', '33007', 43.357986323, -5.8504599999999),
    ('44M', '44M11', 'Biblioteca Pública Municipal "Villa Magdalena"', 'Coordinación Bibliotecaria Municipal', 'Av. Galicia, s/n', 'Oviedo', '33005', 43.358895, -5.856292175),
    ('44M', '44M03', 'Biblioteca Pública Municipal "Lorenzo Rodríguez Castellano" (La Granja)', 'Coordinación Bibliotecaria Municipal', 'Campo de San Francisco, s/n', 'Oviedo', '33007', 43.357986323, -5.8504599999999),
    ('44M', '44M01', 'Biblioteca Pública Municipal de Ciudad Naranco', 'Coordinación Bibliotecaria Municipal', 'C/ Fernández de Oviedo, s/n', 'Oviedo', '33012', 43.369095, -5.866822746),
    ('44M', '44M02', 'Biblioteca Pública Municipal de La Corredoria', 'Coordinación Bibliotecaria Municipal', 'Finca del Cortijo, 82', 'Oviedo', '33011', 43.38473, -5.8219014649999),
    ('44M', '44M04', 'Biblioteca Pública Municipal "Sara Suárez Solís" (Pumarín)', 'Coordinación Bibliotecaria Municipal', 'C/ Aureliano San Román, 25', 'Oviedo', '33011', 43.38473, -5.8219014649999),
    ('44M', '44M05', 'Biblioteca Pública Municipal de San Claudio', 'Coordinación Bibliotecaria Municipal', 'C/ San Roque, s/n', 'Oviedo', '33191', 43.36442, -5.925475123),
    ('44M', '44M07', 'Biblioteca Pública Municipal de Tudela Veguín', 'Coordinación Bibliotecaria Municipal', 'C/ de la Manzanilla, s/n', 'Oviedo', '33910', 43.34337, -5.7840872099999),
    ('44M', '44M06', 'Biblioteca Pública Municipal de Trubia', 'Coordinación Bibliotecaria Municipal', 'C/ General Ordoñez, s/n', 'Oviedo', '33100', 43.34072062, -5.964259978),
    ('44M', '44M08', 'Biblioteca Pública Municipal de Vallobín', 'Coordinación Bibliotecaria Municipal', 'C/ Doctor Solís Cajigal, s/n', 'Oviedo', '33012', 43.369095, -5.866822746),
    ('44M', '44M09', 'Biblioteca Pública Municipal "José María Laso Prieto" (Ventanielles)', 'Coordinación Bibliotecaria Municipal', 'Pl. Lago Enol, s/n', 'Oviedo', '33010', 43.37409, -5.806747338),
    ('44M', '44M12', 'Biblioteca Pública Municipal de San Lázaro', 'Coordinación Bibliotecaria Municipal', 'Pl. Manolo Díaz, s/n', 'Oviedo', '33008', 43.354935, -5.833549583),
    ('451', '451', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Leopoldo Alas "Clarín"', 'Parres', '33540', 43.381076674, -5.18251),
    ('461', '461', 'Biblioteca Pública Municipal "Luis Ángel Sánchez Villar"', 'Biblioteca Pública Municipal "Luis Ángel Sánchez Villar"', 'Bo Llumberu, s/n', 'Peñamellera Alta', '33578', 43.33874, -4.672596864),
    ('461', 'PMIE', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal "Luis Ángel Sánchez Villar"', 'Antiguas Escuelas, s/n', 'Peñamellera Alta', '33577', 43.312388136, -4.6663599999999),
    ('471', '471', 'Biblioteca Pública Municipal "José María de Pereda"', 'Biblioteca Pública Municipal "José María de Pereda"', 'Ayuntamiento', 'Peñamellera Baja', '33570', 43.322866346, -4.5818149999999),
    ('481', '481', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Edificio de Servicios Múltiples, s/n', 'Pesoz', '33735', 43.276565207, -6.871845),
    ('491', '491', 'Biblioteca Pública Municipal "Marqués de Vista Alegre"', 'Biblioteca Pública Municipal "Marqués de Vista Alegre"', 'C/ Covadonga, 42', 'Piloña', '33530', 43.347759438, -5.3652049999999),
    ('492', '492', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Travesía Ramón Toraño, s/n', 'Piloña', '33583', 43.371785841, -5.289575),
    ('501', '501', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Ayuntamiento', 'Ponga', '33557', 43.203949877, -5.18961),
    ('511', '511', 'Biblioteca Pública Municipal "Antón de la Braña"', 'Biblioteca Pública Municipal "Antón de la Braña"', 'C/ Primo de Rivera, 2', 'Pravia', '33120', 43.4891, -6.1106307599999),
    ('521', '521', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Carretera General, s/n', 'Proaza', '33114', 43.239695, -6.035244862),
    ('531', '531', 'Biblioteca Pública Municipal "San Melchor de Quirós"', 'Biblioteca Pública Municipal "San Melchor de Quirós"', 'El Felgueru, s/n', 'Quirós', '33117', 43.173325, -5.9669397709999),
    ('551', '551', 'Biblioteca Pública Municipal "Iñigo Noriega Laso"', 'Biblioteca Pública Municipal "Iñigo Noriega Laso"', 'El Redondo Casa de Piedra', 'Ribadedeva', '33590', 43.37183, -4.595798987),
    ('561', '561', 'Biblioteca Pública Municipal "Enriqueta González Rubín"', 'Biblioteca Pública Municipal "Enriqueta González Rubín"', 'C/ Ecce Homo, s/n', 'Ribadesella', '33560', 43.460285, -5.0540446799999),
    ('571', '571', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Edif. de Servicios Múltiples', 'Ribera de Arriba', '33172', 43.301315, -5.9261380629999),
    ('581', '581', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Alcalde Próspero M. Suárez, 1', 'Riosa', '33160', 43.20848, -5.8904352489999),
    ('591', '591', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Centro de Cultura "Juan Velarde Fuertes", Av. de Chamberí, 29', 'Salas', '33860', 43.40655, -6.253792727),
    ('611', '611', 'Centro de Lectura', 'Centro de Lectura', 'Casa de los Guzmanes de Vegadeo', 'San Martín de Oscos', '33777', 43.298121097, -6.955955),
    ('602', '602', 'Biblioteca Pública Municipal "Aquilino de la Torre"', 'Biblioteca Pública Municipal "Aquilino de la Torre"', 'C/ Aquilino de la Torre, 3 Bajo', 'San Martín del Rey Aurelio', '33960', 43.276671633, -5.59151),
    ('601', '601', 'Biblioteca Pública Municipal "Gaspar García Laviana"', 'Biblioteca Pública Municipal "Gaspar García Laviana"', 'C/ Manuel Gutiérrez Vigil, 16, 1ª', 'San Martín del Rey Aurelio', '33940', 43.283325, -5.6283546879999),
    ('603', '603', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Lago Enol, 1 Bajo', 'San Martín del Rey Aurelio', '33950', 43.277806701, -5.615193179),
    ('631', '631', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', NULL, 'San Tirso de Abres', '33774', 43.403365, -7.131594655),
    ('621', '621', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', NULL, 'Santa Eulalia de Oscos', '33776', 43.277417746, -7.0242249999999),
    ('641', '641', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Pza. de Ángel Fernández, s/n', 'Santo Adriano', '33115', 43.282225, -5.989153464),
    ('651', '651', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', NULL, 'Sariego', '33518', 43.399435, -5.5578247779999),
    ('663', '663', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'El Chalet, s/n', 'Siero', '33936', 43.34423, -5.6228989809999),
    ('664', '664', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Av. de Oviedo, 8-10 Bajo', 'Siero', '33186', 43.380545, -5.704675505),
    ('662', '662', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Leopoldo Lugones, 31', 'Siero', '33420', 43.402988621, -5.813795),
    ('661', '661', 'Biblioteca Pública Municipal "Fausto Vigil"', 'Biblioteca Pública Municipal "Fausto Vigil"', 'C/ Alcalde Parrondo, 30', 'Siero', '33510', 43.39319, -5.6607942369999),
    ('665', '665', 'Biblioteca Pública Municipal "Casino de Lieres"', 'Biblioteca Pública Municipal "Casino de Lieres"', 'La Pedrera, s/n', 'Siero', '33580', 43.372854407, -5.577755),
    ('666', '666', 'Biblioteca Pública Municipal de Santiago de Arenas', 'Biblioteca Pública Municipal de Santiago de Arenas', 'C/ Francisco Orueta, s/n', 'Siero', '33936', 43.34423, -5.6228989809999),
    ('667', '667', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Av. Principal', 'Siero', '33429', 43.361775, -5.71602832),
    ('671', '671', 'Biblioteca Pública Municipal "Fermín Canella"', 'Biblioteca Pública Municipal "Fermín Canella"', 'Ctra. General, 25', 'Sobrescobio', '33993', 43.177934088, -5.4676449999999),
    ('671', 'SSOT', 'Biblioteca Pública Municipal "Padre Juan Prado"', 'Biblioteca Pública Municipal "Fermín Canella"', NULL, 'Sobrescobio', '33993', 43.177934088, -5.4676449999999),
    ('681', '681', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Parque Natural de Somiedo, s/n', 'Somiedo', '33840', 43.06888, -6.212395166),
    ('692', '692', 'Biblioteca Pública Municipal "Emilio Alarcos Llorach"', 'Biblioteca Pública Municipal "Emilio Alarcos Llorach"', 'Av. de los Quebrantos, s/n', 'Soto del Barco', '33125', 43.562001722, -6.0707899999999),
    ('691', '691', 'Biblioteca Pública Municipal "Ildefonso Fierro Ordóñez"', 'Biblioteca Pública Municipal "Ildefonso Fierro Ordóñez"', 'El Campo, s/n', 'Soto del Barco', '33126', 43.527301, -6.073955),
    ('701', '701', 'Biblioteca Pública Municipal "Fernando Villamil"', 'Biblioteca Pública Municipal "Fernando Villamil"', 'Pl. del Mercado, 1', 'Tapia de Casariego', '33740', 43.54882, -6.935910604),
    ('711', '711', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'Av. de Galicia, s/n', 'Taramundi', '33775', 43.363325, -7.0777006759999),
    ('721', '721', 'Biblioteca Pública Municipal "Sandalio Suárez"', 'Biblioteca Pública Municipal "Sandalio Suárez"', 'C/ Manuel Lombardero, s/n', 'Teverga', '33111', 43.14514, -6.120019847),
    ('732', '732', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Camino de la Iglesia, 22', 'Tineo', '33873', 43.41497, -6.5882207399999),
    ('731', 'TTUÑ', 'Centro de Lectura', 'Biblioteca Pública Municipal', NULL, 'Tineo', '33876', 43.24234, -6.3591563279999),
    ('731', '731', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ Mayor, 25', 'Tineo', '33870', 43.33058, -6.4170848119999),
    ('341', '341', 'Biblioteca Pública Municipal "Joaquín Rodríguez"', 'Biblioteca Pública Municipal "Joaquín Rodríguez"', 'C/ Olavarrieta, 24', 'Valdés', '33700', 43.536475649, -6.53171),
    ('741', '741', 'Biblioteca Pública Municipal "Emilio y Armando Cotarelo"', 'Biblioteca Pública Municipal "Emilio y Armando Cotarelo"', 'C/ Alameda, 12', 'Vegadeo', '33770', 43.448224003, -7.0554089999999),
    ('751', '751', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ El Colegio', 'Villanueva de Oscos', '33777', 43.298121097, -6.955955),
    ('761', '761', 'Biblioteca Pública Municipal "A. Balbín de Unquera"', 'Biblioteca Pública Municipal "A. Balbín de Unquera"', 'Casa de los Hevia, C/ del Agua, 29', 'Villaviciosa', '33300', 43.4834095, -5.4339087339999),
    ('771', '771', 'Biblioteca Pública Municipal', 'Biblioteca Pública Municipal', 'C/ La Plaza 14', 'Villayón', '33717', 43.429485101, -6.68233),
    ('24M12', 'GARM', 'Biblioteca del Archivo Municipal', 'Biblioteca del Archivo Municipal', 'C/ Recoletas, 5 (Edificio Torre del Reloj)', 'Gijón', '33201', 43.546634765, -5.66369),
    ('24M', '24M11', 'Biblioteca del Paciente. Hospital de Cabueñes', 'Fundación Municipal de Cultura (Departamento de Bibliotecas)', 'Hospital de Cabueñes, s/n, Planta -1 (Rehabilitación)', 'Gijón', '33203', 43.539555, -5.618891536),
    ('24M13', 'GMFM', 'Biblioteca "Manuel Fernández-Miranda" Museos Arqueológicos de Gijón', 'Biblioteca "Manuel Fernández-Miranda" Museos Arqueológicos de Gijón', 'Parque Arqueológico-Natural de la Campa Torres, Ctra. de la Campa Torres, 3834', 'Gijón', '33299', 43.54816, -5.706133447),
    ('24M12', 'GDIF', 'Mediateca-Difusión. Centro de Cultura Antiguo Instituto', 'Biblioteca del Archivo Municipal', 'C/ Jovellanos, 21', 'Gijón', '33201', 43.546634765, -5.66369),
    ('24M13', 'GMJO', 'Biblioteca y Centro de Documentación Antonio Martín - Museo Casa Natal de Jovellanos', 'Biblioteca "Manuel Fernández-Miranda" Museos Arqueológicos de Gijón', 'Pl. Jovellanos, s/n', 'Gijón', '33201', 43.546634765, -5.66369),
    ('24M13', 'GMFM-FERROCARRIL', 'Biblioteca del Museo del Ferrocarril de Asturias', 'Biblioteca "Manuel Fernández-Miranda" Museos Arqueológicos de Gijón', 'Pl. de la Estación del Norte, s/n', 'Gijón', '33212', 43.560355, -5.704077733),
    ('24M13', 'GMPA', 'Biblioteca del Muséu del Pueblu d''Asturies', 'Biblioteca "Manuel Fernández-Miranda" Museos Arqueológicos de Gijón', 'Paseo del Doctor Fleming, 877, La Güelga', 'Gijón', '33203', 43.539555, -5.618891536),
    ('24M12', 'GOIJ', 'Biblioteca de la Oficina de Información Juvenil', 'Biblioteca del Archivo Municipal', 'C/ Jovellanos, 21', 'Gijón', '33201', 43.546634765, -5.66369),
    ('24M12', 'GMFS', 'Biblioteca FMSS', 'Biblioteca del Archivo Municipal', 'C/ Palacio Valdes, 2', 'Gijón', '33006', 43.353175, -5.872795885),
    ('508', '508', 'Mediateca Laboral Centro de Arte y Creación Industrial', 'Mediateca Laboral Centro de Arte y Creación Industrial', 'Los Prados, 121', 'Gijón', '33394', 43.519965, -5.594926555),
    ('509', '509', 'Biblioteca de la Fundación Alvargonzález', 'Biblioteca de la Fundación Alvargonzález', 'C/ Claudio Alvargonzález, 16, 1º', 'Gijón', '33201', 43.546634765, -5.66369),
    ('503', '503', 'Biblioteca del Museo Marítimo de Asturias', 'Biblioteca del Museo Marítimo de Asturias', 'C/ Gijón, 8', 'Gozón', '33440', 43.608545, -5.8513505),
    ('361', 'MEOA', 'Biblioteca del Museo Etnográfico del Oriente de Asturias', 'Biblioteca Pública Municipal "Cardenal Inguanzo"', 'Barriu El Llacín', 'Llanes', '33509', 43.394536783, -4.78387),
    ('506', '506', 'Biblioteca del Museo de Bellas Artes de Asturias', 'Biblioteca del Museo de Bellas Artes de Asturias', 'C/ Santa Ana, 1', 'Oviedo', '33003', 43.36203, -5.8449700429999),
    ('501-OVIEDO', '501-OVIEDO', 'Biblioteca del Archivo Histórico de Asturias', 'Biblioteca del Archivo Histórico de Asturias', 'Arcipreste de Hita, s/n', 'Oviedo', '33012', 43.369095, -5.866822746),
    ('504', '504', 'Biblioteca del Museo Arqueológico de Asturias', 'Biblioteca del Museo Arqueológico de Asturias', 'C/ San Vicente, 5', 'Oviedo', '33003', 43.36203, -5.8449700429999),
    ('505', '505', 'Biblioteca del Real Instituto de Estudios Asturianos', 'Biblioteca del Real Instituto de Estudios Asturianos', 'Pl. de Porlier, 9 1ª planta', 'Oviedo', '33003', 43.36203, -5.8449700429999),
    ('507', '507', 'Biblioteca del Conservatorio Superior de Música "Eduardo Martínez Torner"', 'Biblioteca del Conservatorio Superior de Música "Eduardo Martínez Torner"', 'C/ Corrada del Obispo, s/n', 'Oviedo', '33003', 43.36203, -5.8449700429999),
    ('5111', 'BIAM', 'Biblioteca del Instituto Asturiano de la Mujer', 'Biblioteca del Instituto Asturiano de la Mujer', 'Ed. Buenavista, Pl.3, C/ Eduardo Herrera "Herrerita", s/n', 'Oviedo', '33006', 43.353175, -5.872795885),
    ('551', 'ARIN', 'Biblioteca del Archivo de Indianos', 'Biblioteca Pública Municipal "Iñigo Noriega Laso"', 'Quinta Guadalupe', 'Ribadedeva', '33590', 43.37183, -4.595798987),
    ('601', 'MUMI', 'Biblioteca del Museo de la Minería y de la Industria', 'Biblioteca Pública Municipal "Gaspar García Laviana"', 'C/ El Trabaquín, s/n', 'San Martín del Rey Aurelio', '33940', 43.283325, -5.6283546879999),
    ('510', '510', 'Biblioteca del SERIDA', 'Biblioteca del SERIDA', 'Ctra. AS-267, PK 19', 'Villaviciosa', '33300', 43.4834095, -5.4339087339999),
    ('512', '512', 'Biblioteca de la Fundación Cardín', 'Biblioteca de la Fundación Cardín', 'C/ Eloísa Fernández, 2', 'Villaviciosa', '33300', 43.4834095, -5.4339087339999);

CREATE TEMP TABLE tmp_resumen_asturias (
    tabla TEXT NOT NULL,
    creadas INTEGER NOT NULL,
    actualizadas INTEGER NOT NULL
) ON COMMIT DROP;

WITH ins AS (
    INSERT INTO bibliotecas (
        fuente_id, codigo, nombre, municipio, direccion,
        codigo_postal, latitud, longitud
    )
    SELECT
        f.id,
        d.codigo_biblioteca,
        d.nombre_biblioteca,
        d.municipio,
        d.direccion,
        d.codigo_postal,
        d.latitud,
        d.longitud
    FROM (
        SELECT DISTINCT ON (codigo_biblioteca)
            codigo_biblioteca, nombre_biblioteca, direccion, municipio,
            codigo_postal, latitud, longitud
        FROM tmp_directorio_asturias
        ORDER BY
            codigo_biblioteca,
            (codigo_sucursal = codigo_biblioteca) DESC,
            codigo_sucursal
    ) AS d
    CROSS JOIN fuentes AS f
    WHERE f.codigo = 'asturias'
    ON CONFLICT (fuente_id, codigo) DO UPDATE SET
        nombre = EXCLUDED.nombre,
        municipio = COALESCE(EXCLUDED.municipio, bibliotecas.municipio),
        direccion = COALESCE(EXCLUDED.direccion, bibliotecas.direccion),
        codigo_postal = COALESCE(EXCLUDED.codigo_postal, bibliotecas.codigo_postal),
        latitud = COALESCE(EXCLUDED.latitud, bibliotecas.latitud),
        longitud = COALESCE(EXCLUDED.longitud, bibliotecas.longitud)
    RETURNING (xmax = 0) AS creada
)
INSERT INTO tmp_resumen_asturias (tabla, creadas, actualizadas)
SELECT
    'bibliotecas',
    count(*) FILTER (WHERE creada),
    count(*) FILTER (WHERE NOT creada)
FROM ins;

WITH ins AS (
    INSERT INTO sucursales (
        fuente_id, biblioteca_id, codigo, nombre, municipio, direccion,
        codigo_postal, latitud, longitud
    )
    SELECT
        b.fuente_id,
        b.id,
        d.codigo_sucursal,
        d.nombre,
        d.municipio,
        d.direccion,
        d.codigo_postal,
        d.latitud,
        d.longitud
    FROM tmp_directorio_asturias AS d
    JOIN fuentes AS f
        ON f.codigo = 'asturias'
    JOIN bibliotecas AS b
        ON b.fuente_id = f.id
       AND b.codigo = d.codigo_biblioteca
    ON CONFLICT (fuente_id, codigo) DO UPDATE SET
        biblioteca_id = EXCLUDED.biblioteca_id,
        nombre = EXCLUDED.nombre,
        municipio = COALESCE(EXCLUDED.municipio, sucursales.municipio),
        direccion = COALESCE(EXCLUDED.direccion, sucursales.direccion),
        codigo_postal = COALESCE(EXCLUDED.codigo_postal, sucursales.codigo_postal),
        latitud = COALESCE(EXCLUDED.latitud, sucursales.latitud),
        longitud = COALESCE(EXCLUDED.longitud, sucursales.longitud),
        updated_at = now()
    RETURNING (xmax = 0) AS creada
)
INSERT INTO tmp_resumen_asturias (tabla, creadas, actualizadas)
SELECT
    'sucursales',
    count(*) FILTER (WHERE creada),
    count(*) FILTER (WHERE NOT creada)
FROM ins;

SELECT
    r.tabla,
    r.creadas,
    r.actualizadas,
    (SELECT count(*) FROM bibliotecas b
        JOIN fuentes f ON f.id = b.fuente_id
        WHERE f.codigo = 'asturias') AS total,
    (SELECT count(*) FROM bibliotecas b
        JOIN fuentes f ON f.id = b.fuente_id
        WHERE f.codigo = 'asturias'
          AND b.codigo_postal IS NOT NULL) AS con_codigo_postal,
    (SELECT count(*) FROM bibliotecas b
        JOIN fuentes f ON f.id = b.fuente_id
        WHERE f.codigo = 'asturias'
          AND b.latitud IS NOT NULL AND b.longitud IS NOT NULL) AS con_coordenadas
FROM tmp_resumen_asturias AS r
WHERE r.tabla = 'bibliotecas'
UNION ALL
SELECT
    r.tabla,
    r.creadas,
    r.actualizadas,
    (SELECT count(*) FROM sucursales s
        JOIN fuentes f ON f.id = s.fuente_id
        WHERE f.codigo = 'asturias') AS total,
    (SELECT count(*) FROM sucursales s
        JOIN fuentes f ON f.id = s.fuente_id
        WHERE f.codigo = 'asturias'
          AND s.codigo_postal IS NOT NULL) AS con_codigo_postal,
    (SELECT count(*) FROM sucursales s
        JOIN fuentes f ON f.id = s.fuente_id
        WHERE f.codigo = 'asturias'
          AND s.latitud IS NOT NULL AND s.longitud IS NOT NULL) AS con_coordenadas
FROM tmp_resumen_asturias AS r
WHERE r.tabla = 'sucursales'
ORDER BY tabla;
