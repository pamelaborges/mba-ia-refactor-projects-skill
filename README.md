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

---

### 2. Construção da Skill

A skill `refactor-arch` vive em `.claude/skills/refactor-arch/`, copiada dentro
de cada um dos 3 projetos. `SKILL.md` define 3 fases sequenciais (Análise →
Auditoria → Refatoração) e 5 arquivos de referência em Markdown:

| Arquivo | Área de conhecimento |
|---|---|
| `references/analise-projeto.md` | Heurísticas para detectar linguagem, framework, banco e mapear arquitetura |
| `references/catalogo-antipatterns.md` | 12 anti-patterns, cada um com sinais de detecção e severidade |
| `references/template-relatorio.md` | Formato padronizado do relatório de auditoria |
| `references/diretrizes-arquitetura.md` | Regras do padrão MVC alvo (camadas e responsabilidades) |
| `references/playbook-refatoracao.md` | 12 padrões de transformação com exemplos de código antes/depois |

**Decisões de design**

- **Catálogo derivado da análise manual, não do zero.** Os 12 anti-patterns do
  catálogo mapeiam diretamente para os problemas documentados na Seção 1 —
  SQL Injection, exposição de credenciais/dados sensíveis, ausência de
  autenticação, ausência de transação, N+1, lógica de negócio fora do
  domínio, duplicação/abstração não usada, tratamento de erro genérico, APIs
  deprecated, God Object, e CORS/superfície pública. Isso garante que a skill
  resolve exatamente os problemas que motivaram sua criação, não uma lista
  genérica de boas práticas.
- **Severidade decisiva, não hedgeada.** Cada anti-pattern tem uma severidade
  padrão única (nunca "MEDIUM/HIGH"), com uma frase explícita de quando ela
  sobe ou desce — por exemplo, ausência de autenticação é CRITICAL por
  padrão, mas cai para HIGH quando o dado exposto não é sensível.
- **Fase 2 é um portão, não uma sugestão.** O SKILL.md declara como regra
  inviolável que nenhum arquivo é modificado antes da confirmação explícita
  do usuário, e o template de relatório termina com a pergunta de confirmação
  formatada (todos / só CRITICAL+HIGH / itens específicos / nenhum agora).
- **Agnosticismo testado, não assumido.** Todo sinal de detecção no catálogo
  tem uma variante por stack (ex.: SQLi é "`execute(` + concatenação" em
  Python e "template string em `query()`" em Node.js). Isso foi validado na
  prática rodando a skill nos 3 projetos (Seção 3).
- **Escopo de correção rastreável ao relatório aprovado.** Nenhuma correção
  da Fase 3 foi aplicada sem corresponder a um item numerado do relatório —
  evitando "melhorias de carona" que tornariam a skill imprevisível.

**Desafios encontrados**

- A primeira versão do catálogo tinha várias severidades duplas (`MEDIUM /
  HIGH`) e uma tabela-resumo redundante no fim — sintomas de texto gerado sem
  uma posição definida. Foi revisado para severidade única por item com
  justificativa de quando ela escala.
- No `ecommerce-api-legacy` (Node.js), o schema init original dependia de
  `db.serialize()` para garantir a ordem de execução das queries; ao
  reescrever para repositórios com Promises, a primeira versão sem
  `serialize()` quebrou o boot (`no such table: users`) porque o driver
  `sqlite3` não garante ordem entre chamadas não encadeadas — corrigido
  reintroduzindo `db.serialize()` só na inicialização do schema.
- Habilitar `PRAGMA foreign_keys = ON` no mesmo projeto mudou o comportamento
  de `DELETE /api/users/:id`: em vez de sempre responder 200 e deixar
  matrículas/pagamentos órfãos, agora falha com 409 quando há vínculos — uma
  mudança de contrato deliberada e aprovada, documentada no relatório.
- No `task-manager-api`, a auditoria revelou que a estrutura de pastas já
  existia (`routes/`, `models/`, `services/`, `utils/`) mas as abstrações
  (`is_overdue()`, `NotificationService`, `process_task_data`) não eram
  usadas. Isso confirmou que o catálogo precisa detectar "abstração pronta e
  não usada" como categoria própria, não só duplicação literal de código. Na
  primeira passada da Fase 3, o esforço foi só em passar a chamar o que já
  existia sem tocar na estrutura de pastas — mas isso deixou a rota fazendo
  a mesma orquestração de sempre, sem um controller fino entre rota e
  domínio, contradizendo a própria proposta de reestruturação MVC do
  relatório (`reports/audit-project-3.md`). Corrigido extraindo uma camada
  `controllers/` (mesmo padrão dos outros 2 projetos), com as rotas virando
  apenas registro de `Blueprint.add_url_rule` + guarda de autenticação.
- Durante a validação, um processo de teste anterior (`code-smells-project`)
  ficou rodando em background e ocupou a porta 5000 ao validar o projeto
  seguinte — lembrete de que cada `Bash` do agente é um shell novo e `kill
  %1` não sobrevive entre chamadas; a solução foi localizar o PID via
  `lsof`/`ps` e encerrá-lo explicitamente.

---

### 3. Resultados

| Projeto | Stack | Findings (Fase 2) | Severidade | Fase 3 |
|---|---|---|---|---|
| `code-smells-project` | Python/Flask | 10 | 4 CRITICAL, 1 HIGH, 3 MEDIUM, 2 LOW | ✅ todos os 10 corrigidos |
| `ecommerce-api-legacy` | Node.js/Express | 11 | 4 CRITICAL, 2 HIGH, 2 MEDIUM, 3 LOW | ✅ todos os 11 corrigidos |
| `task-manager-api` | Python/Flask | 10 | 4 CRITICAL, 1 HIGH, 3 MEDIUM, 2 LOW | ✅ todos os 10 corrigidos |

Relatórios completos em [`reports/audit-project-1.md`](reports/audit-project-1.md),
[`reports/audit-project-2.md`](reports/audit-project-2.md) e
[`reports/audit-project-3.md`](reports/audit-project-3.md).

**Comparação antes/depois (destaques)**

| Problema | Antes | Depois |
|---|---|---|
| Login (`code-smells-project`) | `email = "' OR '1'='1' --"` autentica como qualquer usuário | queries parametrizadas — bypass testado e bloqueado |
| Rotas admin (3 projetos) | `/admin/*`, `/api/admin/*` públicas | exigem token/JWT; código-smells e ecommerce guardam por header, task-manager por JWT real |
| Senha (`code-smells-project`) | texto plano, devolvida em `GET /usuarios` | removida da serialização |
| Senha (`ecommerce-api-legacy`) | `badCrypto` reversível (base64 concatenado) | `bcryptjs` com salt |
| Senha (`task-manager-api`) | MD5 sem salt, devolvida até no `/login` | `werkzeug.security` + removida da serialização |
| Checkout (`ecommerce-api-legacy`) | 3 inserts encadeados sem transação | `BEGIN/COMMIT/ROLLBACK` explícito |
| Pedido (`code-smells-project`) | sem transação, sem rollback | rollback em qualquer falha no meio do fluxo |
| Relatório financeiro (`ecommerce-api-legacy`) | 5 níveis de callback aninhado, N+1, `err` ignorado | 1 query com JOIN |
| `is_overdue()` (`task-manager-api`) | existia, nunca chamado; lógica copiada em 5 rotas | usado nos 5 pontos |
| Delete de usuário (`ecommerce-api-legacy`) | sempre 200, deixava órfãos | FK + `PRAGMA foreign_keys=ON`, 409 se houver vínculo |

**Checklist de validação (preenchido nos 3 projetos)**

Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python/Flask ×2, Node.js/Express ×1)
- [x] Framework detectado corretamente (versões lidas do manifesto)
- [x] Domínio da aplicação descrito corretamente
- [x] Número de arquivos analisados condiz com a realidade

Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (10, 11 e 10 respectivamente)
- [x] Detecção de APIs deprecated incluída no catálogo (MD5/`utcnow()` acionados nos 3 projetos)
- [x] Skill pausou e pediu confirmação antes da Fase 3 (nos 3 projetos)

Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC (nos 2 projetos que não tinham; mantida e reforçada no 3º)
- [x] Configuração extraída para módulo/variável de ambiente (sem hardcoded)
- [x] Models/repositórios criados ou corrigidos para abstrair dados
- [x] Rotas separadas do roteamento de negócio
- [x] Error handling centralizado (`logging`, exceções específicas)
- [x] Entry point claro (`app.py` / `src/app.js` como composition root)
- [x] Aplicação inicia sem erros (validado com boot real, não só leitura de código)
- [x] Endpoints originais respondem corretamente (validado com `curl` em todos os 3 projetos)

**Evidência de execução** (excerto real do `code-smells-project` após a Fase 3):

```
$ curl -X POST http://localhost:5000/login -d '{"email":"admin@loja.com","senha":"admin123"}'
{"dados":{"email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"},"mensagem":"Login OK","sucesso":true}

$ curl -X POST http://localhost:5000/login -d '{"email":"'"'"' OR '"'"'1'"'"'='"'"'1","senha":"x"}'
{"erro":"Email ou senha inválidos","sucesso":false}   # bypass de SQLi bloqueado

$ curl -X POST http://localhost:5000/admin/reset-db
{"erro":"Não autorizado"}   # 401 sem token

$ curl -X POST http://localhost:5000/admin/reset-db -H "X-Admin-Token: ..."
{"mensagem":"Banco de dados resetado","sucesso":true}   # 200 com token
```

---

### 4. Como Executar

**Pré-requisitos**

- Python 3.11+ (para `code-smells-project` e `task-manager-api`)
- Node.js 18+ (para `ecommerce-api-legacy`)
- Claude Code (a skill usa `.claude/skills/refactor-arch/`)

**Rodar a skill em cada projeto**

```bash
# Projeto 1 — code-smells-project
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api
cd ../task-manager-api
claude "/refactor-arch"
```

A Fase 2 sempre pausa e pergunta quais correções aplicar antes de tocar em
qualquer arquivo — responda a pergunta de confirmação para prosseguir à Fase 3.

**Subir cada API refatorada e validar manualmente**

`code-smells-project` (Python/Flask):
```bash
cd code-smells-project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha SECRET_KEY e ADMIN_TOKEN
export $(cat .env | xargs)
python app.py
# em outro terminal:
curl http://localhost:5000/produtos
curl -X POST http://localhost:5000/admin/reset-db -H "X-Admin-Token: <seu-token>"
```

`ecommerce-api-legacy` (Node.js/Express):
```bash
cd ecommerce-api-legacy
npm install
cp .env.example .env   # preencha DB_PASS, PAYMENT_GATEWAY_KEY, ADMIN_TOKEN
export $(cat .env | xargs)
npm start
# em outro terminal:
curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"teste@x.com","pwd":"123456","c_id":1,"card":"4111111111111111"}'
curl http://localhost:3000/api/admin/financial-report -H "X-Admin-Token: <seu-token>"
```

`task-manager-api` (Python/Flask):
```bash
cd task-manager-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha SECRET_KEY
export $(cat .env | xargs)
python seed.py
python app.py
# em outro terminal:
TOKEN=$(curl -s -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")
curl http://localhost:5000/users -H "Authorization: Bearer $TOKEN"
```

**Como validar que a refatoração funcionou**

1. O servidor deve subir sem traceback.
2. Os endpoints listados no "Resumo da Análise" da Fase 1 de cada projeto devem
   responder com o mesmo formato de antes (exceto as mudanças de contrato
   aprovadas e documentadas em cada relatório: remoção do campo de senha e
   guarda de autenticação nas rotas administrativas/sensíveis).
3. Os relatórios em `reports/audit-project-*.md` documentam, para cada
   achado, a correção aplicada — qualquer revisor pode conferir achado por
   achado contra o código final.
