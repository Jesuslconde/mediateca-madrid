# Spec Delta

## ADDED Requirements

### Requirement: Detección de captcha sin falsos positivos

El recolector MUST considerar que una respuesta contiene un captcha solo cuando incluye un desafío de reCAPTCHA real, como el script `g-recaptcha`, `grecaptcha` o el campo `g-recaptcha-response`. El texto de ayuda de AbsysNet que menciona `No soy un robot` SHALL NOT considerarse un captcha por sí solo.

#### Scenario: Listado con texto de ayuda

- **WHEN** el OPAC devuelve un listado de resultados con el texto de ayuda `Verifique que ha chequeado 'No soy un robot'` y sin desafío de reCAPTCHA
- **THEN** el recolector no incrementa el contador de captchas
- **AND** no lanza la detención por captcha
- **AND** el descubrimiento continúa con la siguiente página

#### Scenario: Página con desafío real

- **WHEN** la respuesta contiene `g-recaptcha`, `grecaptcha` o un campo `g-recaptcha-response`
- **THEN** el recolector la trata como una página de captcha
- **AND** incrementa el contador de captchas de la fuente
- **AND** aplica la política de FlareSolverr o la pausa configurada

#### Scenario: Ficha de detalle con texto de ayuda

- **WHEN** una ficha de detalle de Andalucía contiene el texto de ayuda pero no un desafío de reCAPTCHA
- **THEN** la ficha se parsea y se guarda sin lanzar la detención por captcha

#### Scenario: Respuesta resuelta por FlareSolverr

- **WHEN** FlareSolverr devuelve una página con el texto de ayuda y sin desafío de reCAPTCHA
- **THEN** el recolector considera el captcha resuelto
- **AND** no incrementa el contador de captchas fallidos

#### Scenario: Madrid sin captcha

- **WHEN** una página de Madrid no contiene un desafío de reCAPTCHA
- **THEN** el recolector no la marca como captcha
- **AND** el comportamiento de Madrid no cambia
