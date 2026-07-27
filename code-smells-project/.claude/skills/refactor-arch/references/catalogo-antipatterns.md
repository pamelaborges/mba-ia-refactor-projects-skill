# Catálogo de Anti-Patterns

12 anti-patterns, cada um com sinais de detecção agnósticos de linguagem e a
correção correspondente no `playbook-refatoracao.md` (mesmo número/nome).

A severidade abaixo é a que se aplica na maioria dos casos reais dos 3 projetos
analisados. Contexto pode justificar subir ou descer um nível (ex.: item 4 em
uma rota interna sem dado sensível vira HIGH em vez de CRITICAL) — mas registre
o motivo no relatório quando divergir do padrão, não deixe em aberto.

---

## 1. SQL Injection por concatenação de strings — CRITICAL

**Descrição:** query montada por concatenação/interpolação de input do usuário
em vez de parâmetros bindados.

**Sinais de detecção:**
- Python: `execute(` seguido de `+` ou f-string/`.format()` contendo variável
- Node.js: template string em `query(`/`run(`/`get(`/`all(` com `${var}` vindo de
  `req.body`/`req.params`/`req.query`
- Qualquer SQL onde uma variável de request aparece dentro da string da query

**Impacto:** bypass de autenticação, leitura/escrita arbitrária no banco,
exfiltração de dados.

---

## 2. Exposição de credenciais e segredos hardcoded — CRITICAL

**Descrição:** senhas, chaves de API, `SECRET_KEY`, credenciais de banco/SMTP
escritas diretamente no código-fonte.

**Sinais de detecção:**
- grep por `password`, `senha`, `secret`, `api_key`, `token` seguido de `=` e uma
  string literal (não `os.environ`/`process.env`)
- Valores com cara de segredo real: `pk_live_`, `sk_`, strings longas
  alfanuméricas atribuídas a variáveis de config
- `debug=True`/`DEBUG = True` em conjunto com config de produção

**Impacto:** comprometimento total se o repositório vazar; mistura config de
ambiente com código.

---

## 3. Exposição de dados sensíveis na resposta da API — CRITICAL

**Descrição:** endpoint devolve campos que nunca deveriam sair do backend (hash
de senha, segredo interno, dado de outro usuário).

**Sinais de detecção:**
- Função de serialização (`to_dict`, `toJSON`, montagem manual de dict/objeto)
  que inclui um campo de senha/hash
- Endpoint de health-check ou debug retornando config interna
- Ausência de qualquer lista de campos permitidos (serialização "tudo que o
  model tem")

**Impacto:** vazamento de credenciais e dados privados a qualquer chamador.

---

## 4. Ausência de autenticação/autorização — CRITICAL

Rotas que alteram estado ou expõem dados sensíveis sem verificar identidade nem
permissão. O caso mais revelador não é a rota óbvia sem decorator: é a
infraestrutura de auth que já existe e **não é chamada** — token gerado no
login e nunca validado depois, `role` no model e nenhuma rota lendo esse campo.
Isso indica que alguém começou a implementar auth e parou no meio, não que
ninguém pensou nisso.

**Sinais de detecção:**
- Handlers de rota sem decorator/middleware de auth antes da lógica
- Token retornado no login que não é lido em nenhuma outra rota (buscar o nome
  da variável do token em todo o projeto)
- Métodos como `is_admin()`/`check_password()` definidos e sem nenhum call site
- Prefixo de rota `/admin` sem checagem real (o prefixo é só nomenclatura)

Rebaixe para HIGH só quando o efeito de um acesso não autorizado é restrito
(ex.: leitura de um relatório sem PII) — escrita/deleção sem auth é sempre
CRITICAL.

---

## 5. Ausência de transação em operações multi-etapa — HIGH

**Descrição:** sequência de escritas relacionadas (ex.: criar pedido + baixar
estoque + registrar pagamento) sem transação — uma falha no meio deixa o
sistema em estado parcial permanente.

**Sinais de detecção:**
- Múltiplos `INSERT`/`UPDATE` em sequência sem `BEGIN`/`COMMIT` explícito
  envolvendo-os, ou sem uso do gerenciador de transação do ORM
  (`db.session` sem rollback no except, `db.transaction`)
- `return`/erro no meio de um bloco de escritas sem desfazer o que já foi
  persistido
- Callbacks aninhados (Node.js) onde um erro em callback interno não desfaz o
  insert do callback externo

**Impacto:** inconsistência de dados (estoque incorreto, matrícula sem
pagamento), difícil de reproduzir e depurar.

---

## 6. Queries N+1 — MEDIUM

**Descrição:** uma query para listar N registros seguida de uma query adicional
por registro para buscar dados relacionados, quando uma junção/eager load
resolveria em O(1) queries.

**Sinais de detecção:**
- Loop (`for`/`forEach`) sobre o resultado de uma query, contendo outra query
  dentro do corpo do loop
- Uso de `.get()`/`.query.get()` para relacionamento quando o ORM já declara
  `relationship`/`backref` para o mesmo campo
- Loop aninhado com query em cada nível (ex.: pedidos → itens → produto)

**Impacto:** degradação de performance proporcional ao volume de dados;
piora silenciosamente em produção.

---

## 7. Lógica de negócio fora da camada de domínio — MEDIUM

**Descrição:** regra de negócio (cálculo de desconto, decisão de aprovação de
pagamento, validação de domínio) implementada dentro do controller/handler
HTTP ou dentro da camada de acesso a dados, em vez de uma camada de
serviço/domínio isolada e testável sem HTTP/banco.

**Sinais de detecção:**
- Cálculo com múltiplos `if`/`elif` de regra de negócio dentro da função que
  também faz `request.get_json()`/lê `req.body` e retorna a resposta HTTP
- Decisão de negócio simulada inline (ex.: aprovação de pagamento decidida por
  uma checagem trivial no handler, sem chamada a um serviço/gateway)
- Efeito colateral de notificação (`print`/log simulando envio de email/SMS)
  disparado direto do controller

**Impacto:** regra de negócio não testável isoladamente; duplicação inevitável
quando a mesma regra é necessária em outro fluxo.

---

## 8. Duplicação de código / abstração existente não utilizada — MEDIUM

A mesma lógica (validação, cálculo, condição) copiada em vários lugares —
inclusive quando já existe um método que a encapsula e simplesmente não é
chamado.

**Sinais de detecção:**
- Mesmo bloco de `if` (3+ linhas, mesma condição) aparecendo em 2+ arquivos ou
  funções
- Método de model/util definido (`is_overdue`, `validate_x`) com zero
  referências no restante do código (grep pelo nome do método)
- Validação de criação e de atualização de um mesmo recurso com regras
  divergentes (uma tem uma checagem que a outra perdeu)

Sobe para HIGH quando a divergência já causou um bug real (uma cópia validando
menos que a outra) — nesse caso não é só débito técnico, é um defeito ativo.

---

## 9. Tratamento de erro genérico / silencioso — LOW

Captura ampla de exceção (`except Exception`, `except:` nu, callback de erro
ignorado) que esconde a causa raiz.

**Sinais de detecção:**
- `except:` sem tipo, ou `except Exception as e: return str(e)` devolvido na
  resposta HTTP
- Node.js: parâmetro `err` do callback nunca checado antes de prosseguir
- Mesma resposta genérica de erro (`"Erro interno"`) para qualquer falha,
  perdendo a distinção entre erro de validação (400) e erro de sistema (500)

Sobe para MEDIUM quando o `str(e)` devolvido no corpo da resposta vaza
stacktrace ou nome de tabela/coluna do banco para o cliente — nesse caso deixa
de ser só falta de debug e vira exposição de informação interna.

---

## 10. Uso de APIs/dependências deprecated — MEDIUM

Uso de API, função de biblioteca padrão ou pacote de terceiro marcado como
deprecated pela documentação oficial, com substituto moderno disponível.

**Sinais de detecção — verifique a versão instalada antes de aplicar:**

| Linguagem | API/padrão deprecated | Substituto moderno |
|---|---|---|
| Python | `datetime.utcnow()` (deprecated 3.12+) | `datetime.now(timezone.utc)` |
| Python | `hashlib.md5()`/`sha1()` para senha | `bcrypt`/`argon2`/`werkzeug.security` |
| Python | `sqlite3.connect()` sem pool em app multi-thread | pool de conexão do framework |
| Flask | `@app.before_first_request` (removido 2.3+) | setup no bootstrap da app |
| Node.js | callback-style `fs`/`crypto` quando `util.promisify`/`fs.promises` disponível | versão baseada em Promise/async-await |
| Node.js | `new Buffer()` (deprecated) | `Buffer.from()` |
| Express | corpo lido via `body-parser` externo em Express 4.16+ | `express.json()`/`express.urlencoded()` nativos |
| Qualquer | dependência do manifesto com major desatualizado e CVE conhecido | atualizar para versão suportada |

**Como confirmar:** cheque a versão da linguagem/framework detectada na Fase 1
contra a coluna acima — uma API só é "deprecated" na versão que a instalação
realmente usa.

Sobe para HIGH quando a API já é insegura na versão em uso, não só obsoleta —
caso do MD5 para hash de senha, que é sintaticamente válido e roda sem erro,
mas está quebrado como controle de segurança.

---

## 11. Acoplamento de infraestrutura ao domínio (God Object / baixa coesão) — HIGH

**Descrição:** uma única classe/módulo concentra conexão de banco, definição de
schema, seed, roteamento HTTP, validação, regra de negócio e persistência.

**Sinais de detecção:**
- Uma classe cujo construtor abre conexão de banco e cujos métodos também
  registram rotas HTTP (`setupRoutes`, `register`) na mesma classe
- Arquivo único (`models.py`, `AppManager.js`) com múltiplos domínios de
  negócio não relacionados (produtos, usuários, pedidos) misturados
- Import circular ou acoplamento direto entre camada HTTP e SQL bruto, sem
  nenhuma camada intermediária

**Impacto:** impossível testar regra de negócio sem subir servidor + banco;
qualquer mudança tem raio de efeito amplo.

---

## 12. Configuração insegura de CORS / superfície pública — LOW

CORS liberado para qualquer origem (`CORS(app)` sem allowlist,
`Access-Control-Allow-Origin: *`), ou rotas administrativas/debug acessíveis
publicamente sem flag de ambiente.

**Sinais de detecção:**
- `CORS(app)` sem parâmetros / `cors()` sem `origin` configurado
- Rota de reset de banco, execução de query arbitrária, ou relatório
  financeiro registrada sem diferenciação de ambiente

Sozinho é LOW — o browser ainda impõe same-origin por padrão em requisições
simples. Sobe para MEDIUM quando combinado com o item 4 (a rota exposta faz
algo destrutivo e ninguém verifica quem está chamando).
