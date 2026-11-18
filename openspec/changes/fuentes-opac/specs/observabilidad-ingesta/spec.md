# Spec Delta

## MODIFIED Requirements

### Requirement: Métricas de ingesta

El sistema SHALL registrar y exponer, por fuente y de forma agregada, métricas de fichas procesadas, errores, captchas detectados, captchas resueltos, captchas fallidos, renovaciones de sesión y tiempo medio por ficha.

#### Scenario: Errores y captcha

- **WHEN** una ejecución encuentra un reCAPTCHA en una fuente
- **THEN** incrementa el contador de captchas detectados de esa fuente
- **AND** incrementa el contador de captchas resueltos o fallidos de esa fuente según el resultado
- **AND** el trabajo continúa o se reprograma según la política

#### Scenario: Captcha resuelto

- **WHEN** una ejecución detecta un reCAPTCHA y FlareSolverr lo resuelve
- **THEN** incrementa los contadores de captchas detectados y resueltos de esa fuente
- **AND** la ficha se procesa con la respuesta resuelta

#### Scenario: Captcha no resuelto

- **WHEN** una ejecución detecta un reCAPTCHA y no hay FlareSolverr configurado o la resolución falla
- **THEN** incrementa los contadores de captchas detectados y fallidos de esa fuente
- **AND** el trabajo se detiene o se reprograma según la política

#### Scenario: Consulta de métricas

- **WHEN** el operador consulta el estado de ingesta por API, CLI o dashboard
- **THEN** ve los captchas detectados, resueltos y fallidos por fuente
- **AND** ve el total agregado de todas las fuentes
- **AND** los contadores se agregan a partir de las estadísticas persistidas de los trabajos

### Requirement: Logs estructurados

Los logs de ingesta MUST incluir `job_id`, `job_type`, `fuente`, `record_id`, `titn`, `doc`, `result` y `duration_ms` en formato estructurado. El `TITN` SHALL acompañarse siempre de su fuente o de un `record_id` que la incluya.

#### Scenario: Ficha fallida

- **WHEN** una ficha no se puede procesar
- **THEN** el log incluye la fuente, el `TITN`, el error y el número de intento
- **AND** no se registra información personal

#### Scenario: Distinguir el mismo TITN en dos fuentes

- **WHEN** dos fuentes procesan un registro con el mismo `TITN`
- **THEN** sus entradas de log se distinguen por `fuente` o `record_id`
- **AND** no se confunden en las consultas por fuente
