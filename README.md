# Criação de Skills — Refatoração Arquitetural Automatizada

### 1. Análise Manual dos Projetos

## 1.1. `code-smells-project`


| Severidade | Problema | Localização | Observações |
|:----------:|:--------:|:-----------:|:-----------:|
| CRITICAL | SQL Injection | models.py:28||
| CRITICAL | SQL Injection | models.py:48||
| CRITICAL | SQL Injection | models.py:110||
| CRITICAL | SQL Injection | models.py:291||
| CRITICAL |Exposição de dados sensíveis| models.py:83||
| CRITICAL |Exposição de dados sensíveis| models.py:99||
| CRITICAL |Exposição de Credenciais| database.py:76||
| CRITICAL |Exposição de Credenciais| app.py:7||
| CRITICAL |Exposição de Credenciais| app.py:7||
| CRITICAL |Exposição de Credenciais| controllers.py:289||
| CRITICAL |Ausência de Autenticação| app.py:47, app.py:59|Nenhum endpoint tem mas ações administrativas são um risco pois podem apagar o banco ou executar scripts maliciosos |
| HIGH |Baixa coesão| models.py| Varios dominios no mesmo arquivo de model|
| MEDIUM |Violação do SRP| models.py, controllers.py:208| model executando regras de negocio, ausência de camadas de serviços, alto acoplamento |
| MEDIUM | Queries N+1 | models.py:171-233 ||
|LOW|	Magic numbers | models.py:257||
|LOW|	Ausência de Logs estruturados | controllers.py:*||


## 1.2. `ecommerce-api-legacy`


| Severidade | Problema | Localização | Observações |
|:----------:|:--------:|:-----------:|:-----------:|
| CRITICAL |Exposição de Credenciais| utils.js:2-4| |
| CRITICAL |Exposição de dados sensíveis| AppManager.js:45| número do cartão e a chave do gateway impressos em log|
| CRITICAL |Senha default fraca| AppManager.js:68|  |
| CRITICAL |Ausência de Autenticação| AppManager.js:80, AppManager.js:131| delete de usuário públicos;|
| HIGH |God Object/Violação do SRP| AppManager.js| uma classe faz conexão, DDL, seed, rotas, validação, pagamento, persistência e auditoria |
| MEDIUM | Queries N+1 | AppManager.js:92-106||
| MEDIUM |Ausência de Try/catch| AppManager.js||
|LOW| Nomenclatura pouco descritiva | AppManager.js:29-33|variáveis `u`, `e`, `p`, `cid`, `cc`|
|LOW| Magic number | AppManager.js:46||



## 1.3. `task-manager-api`

| Severidade | Problema | Localização | Observações |
|:----------:|:--------:|:-----------:|:-----------:|
| CRITICAL |Exposição de dados sensíveis| models/user.py:21| `to_dict()` inclui `password` e vaza até na resposta do `/login`|
| CRITICAL |Exposição de Credenciais| services/notification_service.py:7-10| |
| CRITICAL |Exposição de Credenciais| app.py:13| |
| CRITICAL |Ausência de Autenticação| routes/*| token nunca é verificado; qualquer um pode fazer `PUT /users/<id>` e virar admin |
| HIGH |Código duplicado| models/task.py:50-60| `is_overdue()` existe e nunca é chamado — a mesma lógica está repetida em 5 rotas |
| MEDIUM | Queries N+1 | routes/task_routes.py:41-57, routes/report_routes.py:53-68||
| MEDIUM |Validação duplicada| utils/helpers.py:57, models/task.py:38-48, routes/task_routes.py:110-114| mesmas regras em 3 camadas, mas só a inline nas rotas é executada |
| MEDIUM |Baixa coesão| routes/report_routes.py:157-223| CRUD de categorias dentro de relatórios |
|LOW| Tratamento de exceção genérico | routes/task_routes.py:62, :137, :204||
|LOW| Ausência de Logs estruturados | routes/*||

