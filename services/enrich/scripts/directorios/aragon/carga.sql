-- Carga manual del directorio de la Red de Bibliotecas de Aragon.
--
-- Fuente:
--   Bibliotecas: https://opendata.aragon.es/GA_OD_Core/download?resource_id=282&formato=json
--   Sucursales:  https://opendata.aragon.es/GA_OD_Core/download?resource_id=283&formato=json
--   Portal:      https://opendata.aragon.es/datos/catalogo/dataset/catalogo-de-la-red-de-bibliotecas-de-aragon-en-formatos-abiertos
--   Licencia:    CC BY 4.0
--   Descarga:    2026-11-25
--
-- La fuente no publica coordenadas. Se usa el centroide del codigo postal
-- (kodens-dev/Spain-Postal-Codes, MIT) para que las sucursales entren en el
-- filtro por proximidad. Cuando el codigo postal no tiene centroide se usa la
-- media de los centroides del municipio.
--
-- Operacion manual e idempotente: inserta o actualiza bibliotecas y sucursales
-- por (fuente, codigo), sin borrar filas ausentes ni tocar otras fuentes, y sin
-- crear ediciones ni ejemplares. Se puede ejecutar varias veces.
--
-- Uso:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f carga.sql
--
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM fuentes WHERE codigo = 'aragon') THEN
        RAISE EXCEPTION
            'No existe la fuente aragon; aplica las migraciones antes de la carga';
    END IF;
END
$$;

CREATE TEMP TABLE tmp_directorio_aragon (
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

INSERT INTO tmp_directorio_aragon (
    codigo_biblioteca, codigo_sucursal, nombre, nombre_biblioteca,
    direccion, municipio, codigo_postal, latitud, longitud
)
VALUES
    ('AHPH', 'AHPH', 'Archivo Histórico Provincial de Huesca', 'Archivo Histórico Provincial de Huesca', 'C/ Canellas 2', 'Huesca', '22001', 42.140096113, -0.40508499999993),
    ('AHPT', 'AHPT', 'Archivo Histórico Provincial de Teruel', 'Archivo Histórico Provincial de Teruel', 'Ronda Damaso Toran 54', 'Teruel', '44003', 40.353351364, -1.1083399999999),
    ('AHPZ', 'AHPZ', 'Archivo Histórico Provincial de Zaragoza', 'Archivo Histórico Provincial de Zaragoza', 'C/ Diego Dormer 6-8', 'Zaragoza', '50001', 41.65118, -0.87833730799997),
    ('AINSA', 'AINSA', 'Biblioteca Municipal Aínsa-Sobrarbe', 'Biblioteca Municipal de Aínsa-Sobrarbe', 'Calle Río Soto s/n', 'Aínsa-Sobrarbe', '22330', 42.3545, 0.090200003000064),
    ('ALAGON', 'ALAGON', 'Biblioteca Municipal de Alagón', 'Biblioteca Municipal de Alagón', 'Plaza Alhóndiga 20', 'Alagón', '50630', 41.77042, -1.122513479),
    ('ALBALA', 'ALBALA', 'Biblioteca Municipal de Albalate del Arzobispo', 'Biblioteca Municipal de Albalate del Arzobispo', 'Ronda Pintor Gárate s/n', 'Albalate del Arzobispo', '44540', 41.124425, -0.57325379299994),
    ('ALBARR', 'ALBARR', 'Biblioteca Municipal de Albarracín', 'Biblioteca Municipal de Albarracín', 'C/ Travesera de la Catedral, 1', 'Albarracín', '44100', 40.37112, -1.428230888),
    ('ALBELD', 'ALBELD', 'Biblioteca Municipal de Albelda', 'Biblioteca Municipal de Albelda', 'Plaza Mayor 1', 'Albelda', '22558', 41.852925, 0.49453087800003),
    ('ALCA', 'ALCA', 'Biblioteca Municipal de Alcañiz Central', 'Biblioteca Municipal de Alcañiz', 'Calle Mayor 13-15', 'Alcañiz', '44600', 41.065225, -0.15741204199998),
    ('ALCA', 'PUIG', 'Biblioteca Municipal de Puigmoreno (Alcañiz)', 'Biblioteca Municipal de Alcañiz', 'Calle Mayor 7', 'Alcañiz', '44660', 41.1177745, -0.25470568199995),
    ('ALCA', 'VAL', 'Biblioteca Municipal de Valmuel (Alcañiz)', 'Biblioteca Municipal de Alcañiz', 'Plaza de España 1', 'Alcañiz', '44661', 41.151505, -0.17512927199994),
    ('ALCAMP', 'ALCAMP', 'Biblioteca Municipal de Alcampell', 'Biblioteca Municipal de Alcampell', 'C/ Litera, s/n', 'Alcampell', '22560', 41.90808857, 0.43975000000006),
    ('ALCOLE', 'ALCOLE', 'Biblioteca Municipal de Alcolea de Cinca', 'Biblioteca Municipal de Alcolea de Cinca', 'Plaza Mayor, 1', 'Alcolea de Cinca', '22410', 41.72654, 0.077138902000058),
    ('ALCORI', 'ALCORI', 'Biblioteca Municipal de Alcorisa', 'Biblioteca Municipal de Alcorisa', 'Marqués de Lena 12', 'Alcorisa', '44550', 40.93334, -0.38460471399998),
    ('ALFAME', 'ALFAME', 'Biblioteca Municipal de Alfamén', 'Biblioteca Municipal de Alfamén', 'C/ Camón Aznar, 7', 'Alfamén', '50461', 41.458875, -1.2343608849999),
    ('ALJUAN', 'ALJUAN', 'Biblioteca Municipal de Almunia de San Juan', 'Biblioteca Municipal de Almunia de San Juan', 'Plaza Agonac 1', 'Almunia de San Juan', '22420', 41.946175, 0.24893348800003),
    ('ALMUDE', 'ALMUDE', 'Biblioteca Municipal de Almudevar', 'Biblioteca Municipal de Almudevar', 'C/ Mayor 75', 'Almudévar', '22270', 42.077005, -0.57399819099993),
    ('ALPAR', 'ALPAR', 'Biblioteca Municipal de Alpartir', 'Biblioteca Municipal de Alpartir', 'Plaza de la Iglesia s/n', 'Alpartir', '50109', 41.40979034, -1.3839199999999),
    ('ALTOR', 'ALTOR', 'Biblioteca Municipal de Altorricón', 'Biblioteca Municipal de Altorricon', 'C/ La Paz', 'Altorricón', '22540', 41.790120325, 0.40751500000005),
    ('ANDO', 'ANDO', 'Biblioteca Pública de Andorra', 'Biblioteca Municipal de Andorra', 'C/ Escuelas, 10', 'Alcorisa', '44550', 40.93334, -0.38460471399998),
    ('ANSO', 'ANSO', 'Biblioteca Municipal de Ansó', 'Biblioteca Municipal de Ansó', 'Pza. Domingo Miral, 3', 'Ansó', '22728', 42.779875, -0.82230819499995),
    ('ATECA', 'ATECA', 'Biblioteca Municipal de Ateca', 'Biblioteca Municipal de Ateca', 'Plaza del mesón 7', 'Ateca', '50200', 41.33612, -1.804663177),
    ('AYERBE', 'AYERBE', 'Biblioteca Municipal de Ayerbe', 'Biblioteca Municipal de Ayerbe', 'C/ Aragón, 40', 'Ayerbe', '22800', 42.268015, -0.70377662699997),
    ('AYHU', 'AYHUDU', 'Biblioteca Municipal de Huesca-Durán Gudiol', 'Biblioteca Municipal de Huesca', 'C/Alfonso II de Aragón, 20', 'Huesca', '22005', 42.125755, -0.38314022099996),
    ('AYHU', 'AYHUSE', 'Biblioteca Municipal de Huesca-Ramón J. Sender', 'Biblioteca Municipal de Huesca', 'San Vicente de Paul 69', 'Huesca', '22006', 42.160525, -0.39459951999993),
    ('BALLOB', 'BALLOB', 'Biblioteca Municipal de Ballobar', 'Biblioteca Municipal de Ballobar', 'Pza. Mayor, 3', 'Ballobar', '22234', 41.60106, 0.15432440600006),
    ('BARBA', 'BARBA', 'Biblioteca Municipal Barbastro-Hermanos Argensola', 'Biblioteca Municipal de Barbastro', 'Argensola 26', 'Barbastro', '22300', 42.02006, 0.10756970300002),
    ('BDGA', 'BDGA', 'Biblioteca de la Administración', 'Biblioteca de la Administración', 'Edificio Pignatelli', 'Zaragoza', '50004', 41.65252, -0.88875748199996),
    ('BELCHI', 'BELCHI', 'Biblioteca Municipal del Belchite', 'Biblioteca Municipal de Belchite', 'Plaza del Ayuntamiento-Planta1', 'Belchite', '50130', 41.323677181, -0.71273499999995),
    ('BELVER', 'BELVER', 'Biblioteca Municipal de Belver de Cinca', 'Biblioteca Municipal de Belver de Cinca', 'Avda. Los Deportes', 'Belver de Cinca', '22533', 41.70764, 0.23162142400002),
    ('BENABA', 'BENABA', 'Biblioteca Municipal de Benabarre', 'Biblioteca Municipal de Benabarre', 'Plaza Escuelas Pías, 5', 'Benabarre', '22580', 42.13004, 0.47752708600007),
    ('BENASQ', 'BENASQ', 'Biblioteca Municipal de Benasque', 'Biblioteca Municipal de Benasque', 'Calle del Horno 10', 'Benasque', '22440', 42.643409888, 0.51787000000007),
    ('BIESCA', 'BIESCA', 'Biblioteca Municipal de Biescas', 'Biblioteca Municipal de Biescas', 'C/ Ramón y Cajal', 'Biescas', '22630', 42.632275, -0.29851561799995),
    ('BINACE', 'BINACE', 'Biblioteca Municipal de Binaced-Valcarca', 'Biblioteca Municipal de Binaced-Valcarca', 'Plaza Aragón 15', 'Binaced', '22510', 41.802055, 0.19028025600005),
    ('BINE', 'BINE', 'Biblioteca Municipal de Binefar', 'Biblioteca Municipal de Binefar', 'Mayor 6', 'Binéfar', '22500', 41.846255, 0.28809487500007),
    ('BOLTA', 'BOLTA', 'Biblioteca Municipal de Boltaña', 'Biblioteca Municipal de Boltaña', 'C/ Ramón y Cajal 24', 'Boltaña', '22340', 42.448412341, 0.065489549000063),
    ('BORJA', 'BORJA', 'Biblioteca Municipal de Borja', 'Biblioteca Municipal de Borja', 'Calle San Juan Alta, 15', 'Borja', '50540', 41.848229301, -1.553445),
    ('BPHU', 'BPHU', 'Biblioteca del Estado en Huesca', 'Biblioteca del Estado en Huesca', 'Avda. de los Pirineos, 2', 'Huesca', '22004', 42.133452732, -0.42133999999993),
    ('BPTE', 'BPTE', 'Biblioteca del Estado en Teruel', 'Biblioteca del Estado en Teruel', 'Pza. Pérez Prado, 3', 'Teruel', '44001', 40.345337151, -1.116725),
    ('BPZ', 'BPZ', 'Biblioteca del Estado en Zaragoza', 'Biblioteca del Estado en Zaragoza', 'Dr. Cerrada, 22', 'Zaragoza', '50005', 41.645815, -0.89444384099994),
    ('BREA', 'BREA', 'Biblioteca Municipal de Brea', 'Biblioteca Municipal de Brea', 'C/Oriente 27', 'Brea de Aragón', '50246', 41.526005, -1.590734471),
    ('CADRET', 'CADRET', 'Biblioteca Municipal de Cadrete', 'Biblioteca Municipal de Cadrete', 'Tenor Fleta 3-9', 'Cadrete', '50420', 41.554221181, -0.95817499999993),
    ('CALACE', 'CALACE', 'Biblioteca Municipal de Calaceite', 'Biblioteca Municipal de Calaceite', 'C/ Arriba s/n', 'Calaceite', '44610', 41.014271217, 0.18325000000004),
    ('CALAMO', 'CALAMO', 'Biblioteca Municipal de Calamocha', 'Biblioteca Municipal de Calamocha', 'Paseo San Roque, s/n', 'Calamocha', '44200', 40.920405, -1.3196712929999),
    ('CALAN', 'CALAN', 'Biblioteca Municipal de Calanda', 'Biblioteca Municipal de Calanda', 'Plaza Manuel Mindal 3', 'Calanda', '44570', 40.946915, -0.22002152899995),
    ('CALATA', 'CALATA', 'Biblioteca Municipal de Calatayud', 'Biblioteca Municipal de Calatayud', 'C/ Blas y Melendo, 1', 'Calatayud', '50300', 41.35138, -1.653729477),
    ('CALATO', 'CALATO', 'Biblioteca Municipal de Calatorao', 'Biblioteca Municipal de Calatorao', 'C/ Calvo Sotelo, 23', 'Calatorao', '50280', 41.52377, -1.2934691689999),
    ('CANFRA', 'CANFRA', 'Biblioteca Municipal de Canfranc', 'Biblioteca Municipal de Canfranc', 'Plaza del Pilar 1', 'Canfranc', '22880', 42.75778, -0.47777110599998),
    ('CARINE', 'CARINE', 'Biblioteca Municipal de Cariñena', 'Biblioteca Municipal de Cariñena', 'C/ Las Monjas, 27', 'Cariñena', '50400', 41.357318169, -1.206695),
    ('CASPE', 'CASPE', 'Biblioteca Municipal de Caspe', 'Biblioteca Municipal de Caspe', 'Glorieta José Besteiro S/N', 'Caspe', '50700', 41.312091682, -0.050454999999943),
    ('CASTES', 'CASTES', 'Biblioteca Municipal de Castejón de Sos', 'Biblioteca Municipal de Castejón de Sos', 'Avenida El Ral 41', 'Castejón de Sos', '22466', 42.5168045, 0.52990412000003),
    ('CELLA', 'CELLA', 'Biblioteca Municipal de Cella', 'Biblioteca Municipal de Cella', 'Calle Sánchez de Motos 64', 'Cella', '44370', 40.43606, -1.30015),
    ('CUARTE', 'CUARTE', 'Biblioteca Municipal de Cuarte de Huerva', 'Biblioteca Municipal de Cuarte de Huerva', 'Plaza de la Iglesia s/n', 'Cuarte de Huerva', '50410', 41.58925, -0.92971501899996),
    ('DAROCA', 'DAROCA', 'Biblioteca Municipal de Daroca', 'Biblioteca Municipal de Daroca', 'C/ Mayor 36', 'Daroca', '50360', 41.113345, -1.4206558),
    ('EJEA', 'EJEA', 'Biblioteca Publica de Ejea de los Caballeros', 'Biblioteca Municipal de Ejea de los Caballeros', 'Plaza del muro 22, 3ª planta', 'Ejea de los Caballeros', '50600', 42.09378, -1.101216692),
    ('EPILA', 'EPILA', 'Biblioteca Municipal de Épila', 'Biblioteca Municipal de Épila', 'Plaza España 1', 'Épila', '50290', 41.57463, -1.236991616),
    ('ESPLUS', 'ESPLUS', 'Biblioteca Municipal de Esplús', 'Biblioteca Municipal de Esplús', 'Plaza Escuelas 1', 'Esplús', '22535', 41.772224482, 0.30268500000005),
    ('ESTADI', 'ESTADI', 'Biblioteca Municipal de Estadilla', 'Biblioteca Municipal de Estadilla', 'Calle Nueva 3', 'Estadilla', '22423', 42.04678, 0.25673755100007),
    ('FIGUER', 'FIGUER', 'Biblioteca Pública Municipal de Figueruelas', 'Biblioteca Municipal de Figueruelas', 'Calle Isidoro Gracia 3-5', 'Figueruelas', '50639', 41.768965, -1.175423273),
    ('FONZ', 'FONZ', 'Biblioteca Municipal de Fonz', 'Biblioteca Municipal de Fonz', 'Plaza Mayor, 3', 'Fonz', '22422', 42.008515, 0.26636369100004),
    ('FRAGA', 'FRAGA', 'Biblioteca Municipal de Fraga Central', 'Biblioteca Municipal de Fraga', 'Jose de Calasanz 12', 'Fraga', '22520', 41.483763321, 0.16301500000003),
    ('FUENTE', 'FUENTE', 'Biblioteca Municipal de Fuentes de Ebro', 'Biblioteca Municipal de Fuentes de Ebro', 'Pza. de la Constitución, 4', 'Fuentes de Ebro', '50740', 41.474689512, -0.62803999999994),
    ('GALLUR', 'GALLUR', 'Biblioteca Pública Municipal de Gallur', 'Biblioteca Municipal de Gallur', 'C/ Baja 2 (Casa de Cultura)', 'Gallur', '50650', 41.86787, -1.330128622),
    ('GRAUS', 'GRAUS', 'Biblioteca Municipal de Graus', 'Biblioteca Municipal de Graus', 'Plaza Compañía 1', 'Graus', '22430', 42.171347661, 0.35551895800006),
    ('GRAÑEN', 'GRAÑEN', 'Biblioteca Municipal de Grañén', 'Biblioteca Municipal de Grañén', 'Cuatro Esquinas 10', 'Grañén', '22260', 41.938165, -0.34672580399996),
    ('GURREA', 'GURREA', 'Biblioteca Municipal de Gurrea de Gállego', 'Biblioteca Municipal de Gurrea de Gállego', 'C/ Mayor 20', 'Gurrea de Gállego', '22280', 42.009222577, -0.71602043499996),
    ('HECHO', 'HECHO', 'Biblioteca Municipal de Hecho', 'Biblioteca Municipal de Hecho', 'Plaza Conde Xiquena, 1', 'Valle de Hecho', '22720', 42.703250206, -0.77638999999994),
    ('HIJAR', 'HIJAR', 'Biblioteca Municipal de Híjar', 'Biblioteca Municipal de Hijar', 'Cuesta Abadía 2', 'Híjar', '44530', 41.14075, -0.40480012599994),
    ('IAM', 'IAM', 'Instituto Aragonés de la Mujer', 'Instituto Aragonés de la Mujer', 'Paseo María Agustín, planta 5', 'Zaragoza', '50071', 41.66742, -0.893771),
    ('IBA', 'IBA', 'Instituto Bibliográfico Aragonés', 'Instituto Bibliográfico Aragonés', 'Dr. Cerrada, 22', 'Zaragoza', '50005', 41.645815, -0.89444384099994),
    ('ILLUEC', 'ILLUEC', 'Biblioteca Municipal de Illueca', 'Biblioteca Municipal de Illueca', 'C/ Benedicto XIII, 54', 'Illueca', '50250', 41.532139581, -1.63407),
    ('JACA', 'JACA', 'Biblioteca Municipal de Jaca', 'Biblioteca Municipal de Jaca', 'C/ Levante, 4', 'Jaca', '22700', 42.563799637, -0.55377999999996),
    ('LAALMU', 'LAALMU', 'Biblioteca Municipal de La Almunia de Doña Godina', 'Biblioteca Municipal de La Almunia de Doña Godina', 'C/ San Juan s/n', 'Almunia de Doña Godina, La', '50100', 41.475115, -1.3389509679999),
    ('LAFUEV', 'LAFUEV', 'Biblioteca Municipal de La Fueva', 'Biblioteca Municipal de La Fueva', 'Plaza Mayor s/n', 'Aínsa-Sobrarbe', '22336', 42.332855933, 0.29616500000003),
    ('LALUEZ', 'LALUEZ', 'Biblioteca Municipal de Lalueza y San Lorenzo del Flumen', 'Biblioteca Municipal de Lalueza y San Lorenzo del Flumen', 'Calle San Lorenzo 4 (Lalueza)', 'Lalueza', '22214', 41.840185, -0.26257450499998),
    ('LAMUEL', 'LAMUEL', 'Biblioteca Municipal de La Muela', 'Biblioteca Municipal de La Muela', 'Plaza D. Vicente Tena, s.n', 'Muela, La', '50196', 41.576766708, -1.1210649999999),
    ('MALLEN', 'MALLEN', 'Biblioteca Municipal de Mallén', 'Biblioteca Municipal de Mallén', 'C/ Padre Ibañez 21', 'Mallén', '50550', 41.890795, -1.4088819149999),
    ('MARIAH', 'MARIAH', 'Biblioteca Municipal de María de Huerva', 'Biblioteca Municipal de María de Huerva', 'Pza. de España, 1-4', 'María de Huerva', '50430', 41.507725, -0.97802754399993),
    ('MEQUI', 'MEQUI', 'Biblioteca Municipal de Mequinenza', 'Biblioteca Municipal de Mequinenza', 'Carretera de Fraga s/n', 'Mequinenza', '50170', 41.328395, 0.23707623200005),
    ('MMATAS', 'MMATAS', 'Biblioteca Municipal de Mas de las Matas', 'Biblioteca Municipal de Mas de las Matas', 'C/ Las escuelas', 'Mas de las Matas', '44564', 40.849475, -0.26201492599995),
    ('MONRE', 'MONRE', 'Biblioteca Municipal de Monreal del Campo', 'Biblioteca Municipal de Monreal del Campo', 'Plaza Mayor 10', 'Monreal del Campo', '44300', 40.77456, -1.3492885119999),
    ('MONTAL', 'MONTAL', 'Biblioteca Municipal de Montalbán', 'Biblioteca Municipal de Montalbán', 'Plaza Carlos Castel', 'Montalbán', '44700', 40.84038, -0.79430947399993),
    ('MONZON', 'MONZON', 'Biblioteca Municipal de Monzón', 'Biblioteca Municipal de Monzón', 'Avenida del Pilar 47', 'Monzón', '22400', 41.894065, 0.22032343700005),
    ('MORATA', 'MORATA', 'Biblioteca Municipal de Morata de Jalón', 'Biblioteca Municipal de Morata de Jalón', 'Plaza Agustina de Aragón S/N, 2ª planta', 'Morata de Jalón', '50260', 41.44258, -1.4582734749999),
    ('MOSQUE', 'MOSQUE', 'Biblioteca Municipal de Mosqueruela', 'Biblioteca Municipal de Mosqueruela', 'Calle Ricos Hombres 4', 'Mosqueruela', '44410', 40.390025, -0.42880711199996),
    ('MSPEDA', 'MSPEDA', 'Museo Pedagógico de Aragón', 'Museo Pedagógico de Aragón', 'Plaza de López Allue s/n', 'Huesca', '22001', 42.140096113, -0.40508499999993),
    ('MSPSER', 'MSPSER', 'IAACC Pablo Serrano', 'IAACC Pablo Serrano', 'Paseo María Agustín, 20', 'Zaragoza', '50004', 41.65252, -0.88875748199996),
    ('MUEL', 'MUEL', 'Biblioteca Municipal de Muel', 'Biblioteca Municipal de Muel', 'C/ El Molino', 'Muel', '50450', 41.47356, -1.112933894),
    ('ONTINA', 'ONTINA', 'Biblioteca Municipal de Ontinar de Salz', 'Biblioteca Municipal de Ontinar de Salz (Zuera)', 'Pza. Mayor, 4', 'Zuera', '50810', 41.936424687, -0.75694499999997),
    ('PANTI', 'PANTI', 'Biblioteca Municipal de Panticosa', 'Biblioteca Municipal de Panticosa', 'C/ Escuelas 5', 'Panticosa', '22661', 42.742815, -0.24296637199996),
    ('PEDRO', 'PEDRO', 'Biblioteca Municipal de Pedrola', 'Biblioteca Municipal de Pedrola', 'C/ Portillo Eras 20', 'Zaragoza', '50620', 41.720905, -1.0291899499999),
    ('PINA', 'PINA', 'Biblioteca Municipal de Pina de Ebro', 'Biblioteca Municipal de Pina de Ebro', 'C/ del Sol, 1', 'Pina de Ebro', '50750', 41.52717, -0.44571598499994),
    ('PINSEQ', 'PINSEQ', 'Biblioteca Municipal de  Pinseque', 'Biblioteca Municipal de Pinseque', 'Pza. de España, 1', 'Pinseque', '50298', 41.72998, -1.086325761),
    ('PUEALF', 'COLPUE', 'Red Bibliotecas escolares de La Puebla de Alfindén', 'Biblioteca Municipal de La Puebla de Alfindén', 'C/ Iglesia 2', 'Puebla de Alfindén, La', '50171', 41.636365, -0.75365238599994),
    ('PUEALF', 'PUEALF', 'Biblioteca Municipal de La Puebla de Alfinden', 'Biblioteca Municipal de La Puebla de Alfindén', 'C/ Iglesia 2', 'Puebla de Alfindén, La', '50171', 41.636365, -0.75365238599994),
    ('PUEALF', 'PUEINS', 'Puebla de Alfindén Instituto', 'Biblioteca Municipal de La Puebla de Alfindén', 'Calle Iglesia 2', 'Puebla de Alfindén, La', '50171', 41.636365, -0.75365238599994),
    ('PUEHIJ', 'PUEHIJ', 'Biblioteca Municipal de La Puebla de Hijar', 'Biblioteca Municipal de La Puebla de Híjar', 'C/ Lorente 45', 'Puebla de Híjar, La', '44510', 41.229396575, -0.46436999999997),
    ('REMOLI', 'REMOLI', 'Biblioteca Municipal de Remolinos', 'Biblioteca Municipal de Remolinos', 'Calle Mayor 7', 'Remolinos', '50637', 41.843885, -1.1759032699999),
    ('RICLA', 'RICLA', 'Biblioteca Municipal de Ricla', 'Biblioteca Municipal de Ricla', 'Pza. España, 1', 'Ricla', '50270', 41.51929256, -1.39942),
    ('RUBIEL', 'RUBIEL', 'Biblioteca Municipal de Rubielos de Mora', 'Biblioteca Municipal de Rubielos de Mora', 'C/ Esterrador nº 3', 'Rubielos de Mora', '44415', 40.17579, -0.64118069799997),
    ('SABI', 'SABI', 'Biblioteca Municipal de Sabiñánigo-Rosa Regás', 'Biblioteca Municipal de Sabiñánigo-Rosa Regás', 'Ramón J. Sender 1', 'Sabiñánigo', '22600', 42.521205, -0.36669591799995),
    ('SADABA', 'SADABA', 'Biblioteca Municipal de Sádaba', 'Biblioteca Municipal de Sádaba', 'Avda. Pirineos s/n', 'Sádaba', '50679', 42.280647472, -1.3514749999999),
    ('SALLEN', 'SALLEN', 'Biblioteca Municipal de Sallent de Gállego', 'Biblioteca Municipal de Sallent de Gállego', 'C/ La Iglesia, 27', 'Sallent de Gállego', '22640', 42.784935, -0.35202194699997),
    ('SANMAT', 'SANMAT', 'Biblioteca Municipal de San Mateo de Gállego', 'Biblioteca Municipal de San Mateo de Gállego', 'Plaza de España 5', 'San Mateo de Gállego', '50840', 41.844905, -0.73438281199998),
    ('SANTAE', 'SANTAE', 'Biblioteca Municipal de Santa Eulalia del Campo', 'Biblioteca Municipal de Santa Eulalia del Campo', 'Pza. Antillón, 7', 'Santa Eulalia', '44360', 40.54586, -1.332303666),
    ('SARINE', 'SARINE', 'Biblioteca Municipal de Sariñena', 'Biblioteca Municipal de Sariñena', 'C/ Soldevilla 3, Bajos', 'Sariñena', '22200', 41.77127, -0.15289606399995),
    ('SOBRA', 'SOBRA', 'Biblioteca Municipal de Sobradiel', 'Biblioteca Municipal de Sobradiel', 'C/ Cortes de Aragón, 3', 'Sobradiel', '50629', 41.742216399, -1.0332299999999),
    ('SOS', 'SOS', 'Biblioteca Municipal de Sos del Rey Católico', 'Biblioteca Municipal de Sos del Rey Católico', 'C/ Manuela Pérez de Biel', 'Sos del Rey Católico', '50680', 42.453965, -1.2130385089999),
    ('TAMARI', 'TAMARI', 'Biblioteca Municipal de Tamarite de Litera', 'Biblioteca Municipal de Tamarite de Litera', 'C/ San Miguel s/n', 'Tamarite de Litera', '22550', 41.83556, 0.42356339000003),
    ('TARAZO', 'TARAZO', 'Biblioteca Municipal de Tarazona', 'Biblioteca Municipal de Tarazona', 'Virgen del Río, 3  2ª Planta', 'Tarazona', '50500', 41.89275, -1.689947644),
    ('TARDIE', 'TARDIE', 'Biblioteca Municipal de Tardienta', 'Biblioteca Municipal de Tardienta', 'C/ José Maria Peleato, s/n', 'Tardienta', '22240', 41.949225, -0.58706780699993),
    ('TAUSTE', 'TAUSTE', 'Biblioteca Municipal de Tauste', 'Biblioteca Municipal de Tauste', 'Pza. de España, s/n', 'Tauste', '50660', 41.939075, -1.1486936379999),
    ('TORREB', 'TORREB', 'Biblioteca Municipal de Torres de Berrellén', 'Biblioteca Municipal de Torres de Berrellén', 'Pza. Bonet, 11', 'Torres de Berrellén', '50693', 41.837713874, -1.12459),
    ('TORREN', 'TORREN', 'Biblioteca Municipal de Torrente de Cinca', 'Biblioteca Municipal de Torrente de Cinca', 'Calle Torralba 1 (Casa Ferrabrás)', 'Torrente de Cinca', '22590', 41.45095, 0.30308782100002),
    ('UTEBO', 'UTEBO', 'Biblioteca Municipal de Utebo', 'Biblioteca Municipal de Utebo', 'Pza. Constitución, 1', 'Utebo', '50180', 41.71515, -0.99164209499997),
    ('UTRI', 'UTRI', 'Biblioteca Municipal de Utrillas', 'Biblioteca Municipal de Utrillas', 'Plaza Ayuntamiento 8', 'Utrillas', '44760', 40.80021, -0.85602656999993),
    ('VALDER', 'VALDER', 'Biblioteca Municipal de Valderrobres', 'Biblioteca Municipal de Valderrobres', 'C/ La Paz 4, bjs', 'Valderrobres', '44580', 40.888586977, 0.14760500000006),
    ('VILLAG', 'VILLAG', 'Biblioteca Municipal de Villanueva de Gállego', 'Biblioteca Municipal de Villanueva de Gállego', 'C/ Goya 16-Centro de día-2ªpta', 'Zuera', '50830', 41.785075, -0.85616351699997),
    ('VILLAM', 'VILLAM', 'Biblioteca Municipal de Villamayor de Gállego', 'Biblioteca Municipal de Villamayor de Gállego', 'C/ del Santuario 36', 'Villamayor de Gállego', '50162', 41.69434, -0.73064788299996),
    ('ZAIDIN', 'ZAIDIN', 'Biblioteca Municipal de Zaidín', 'Biblioteca Municipal de Zaidín', 'Pza. Constitución, 1', 'Zaidín', '22530', 41.623745, 0.27882832000006),
    ('ZUERA', 'ZUERA', 'Biblioteca Municipal de Zuera', 'Biblioteca Municipal de Zuera', 'Plaza de España 8', 'Zuera', '50800', 41.912737188, -0.86386999999996);

CREATE TEMP TABLE tmp_resumen_aragon (
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
        FROM tmp_directorio_aragon
        ORDER BY
            codigo_biblioteca,
            (codigo_sucursal = codigo_biblioteca) DESC,
            codigo_sucursal
    ) AS d
    CROSS JOIN fuentes AS f
    WHERE f.codigo = 'aragon'
    ON CONFLICT (fuente_id, codigo) DO UPDATE SET
        nombre = EXCLUDED.nombre,
        municipio = COALESCE(EXCLUDED.municipio, bibliotecas.municipio),
        direccion = COALESCE(EXCLUDED.direccion, bibliotecas.direccion),
        codigo_postal = COALESCE(EXCLUDED.codigo_postal, bibliotecas.codigo_postal),
        latitud = COALESCE(EXCLUDED.latitud, bibliotecas.latitud),
        longitud = COALESCE(EXCLUDED.longitud, bibliotecas.longitud)
    RETURNING (xmax = 0) AS creada
)
INSERT INTO tmp_resumen_aragon (tabla, creadas, actualizadas)
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
    FROM tmp_directorio_aragon AS d
    JOIN fuentes AS f
        ON f.codigo = 'aragon'
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
INSERT INTO tmp_resumen_aragon (tabla, creadas, actualizadas)
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
        WHERE f.codigo = 'aragon') AS total,
    (SELECT count(*) FROM bibliotecas b
        JOIN fuentes f ON f.id = b.fuente_id
        WHERE f.codigo = 'aragon'
          AND b.codigo_postal IS NOT NULL) AS con_codigo_postal,
    (SELECT count(*) FROM bibliotecas b
        JOIN fuentes f ON f.id = b.fuente_id
        WHERE f.codigo = 'aragon'
          AND b.latitud IS NOT NULL AND b.longitud IS NOT NULL) AS con_coordenadas
FROM tmp_resumen_aragon AS r
WHERE r.tabla = 'bibliotecas'
UNION ALL
SELECT
    r.tabla,
    r.creadas,
    r.actualizadas,
    (SELECT count(*) FROM sucursales s
        JOIN fuentes f ON f.id = s.fuente_id
        WHERE f.codigo = 'aragon') AS total,
    (SELECT count(*) FROM sucursales s
        JOIN fuentes f ON f.id = s.fuente_id
        WHERE f.codigo = 'aragon'
          AND s.codigo_postal IS NOT NULL) AS con_codigo_postal,
    (SELECT count(*) FROM sucursales s
        JOIN fuentes f ON f.id = s.fuente_id
        WHERE f.codigo = 'aragon'
          AND s.latitud IS NOT NULL AND s.longitud IS NOT NULL) AS con_coordenadas
FROM tmp_resumen_aragon AS r
WHERE r.tabla = 'sucursales'
ORDER BY tabla;

COMMIT;
