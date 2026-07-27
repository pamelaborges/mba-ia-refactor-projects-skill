# Relatório de Auditoria Arquitetural — ecommerce-api-legacy

**Data:** 2026-07-27
**Stack detectada:** Node.js / Express 4.18.2 / SQLite (`sqlite3`, acesso direto, sem ORM)
**Baseado na Fase 1:** ver "Resumo da Análise" — uma classe (`AppManager`) concentra toda a aplicação, sem separação de camadas

## Sumário executivo

Toda a aplicação vive em `AppManager.js`: conexão de banco, schema, rotas HTTP,
validação, decisão de pagamento e persistência no mesmo arquivo/classe. O maior
risco não é SQL Injection (as queries já usam `?` parametrizado) — é exposição
de dados sensíveis: número de cartão e chave de gateway de pagamento impressos
em log a cada checkout, e duas rotas (`financial-report`, `delete user`)
públicas sem qualquer autenticação.

## Achados por severidade

| # | Severidade | Problema | Localização | Observações | Ação proposta |
|---|:----------:|---|---|---|---|
| 1 | CRITICAL | Credenciais de produção hardcoded | `utils.js:1-7` | `dbPass` e `paymentGatewayKey` (`pk_live_...`) versionados no código | Variáveis de ambiente |
| 2 | CRITICAL | Exposição de dado sensível em log | `AppManager.js:45` | número do cartão completo impresso a cada checkout — violação de PCI-DSS | Remover PAN do log |
| 3 | CRITICAL | Criptografia insegura / reversível | `utils.js:17-23` | `badCrypto` é concatenação de base64, sem salt, não é hash | Substituir por bcrypt/argon2 |
| 4 | CRITICAL | Ausência de autenticação/autorização | `AppManager.js:80, 131` | relatório financeiro e delete de usuário públicos | Middleware de auth real |
| 5 | HIGH | Ausência de transação multi-etapa | `AppManager.js:50-62` | enrollment → payment → audit_log encadeados sem rollback; falha no meio deixa matrícula sem pagamento | Transação explícita |
| 6 | HIGH | God Object / baixa coesão | `AppManager.js` (toda a classe) | conexão, DDL, seed, rotas, validação, pagamento e persistência no mesmo lugar | Split por domínio |
| 7 | MEDIUM | Regra de negócio mockada no controller | `AppManager.js:46` | aprovação de pagamento decidida por `cc.startsWith("4")` dentro do handler HTTP | Extrair `PaymentGateway` |
| 8 | MEDIUM | Callback hell + erro ignorado + N+1 | `AppManager.js:80-129` | 5 níveis de aninhamento, `err` de `db.all` (linha 92) nunca checado, 2 queries por matrícula | Refatorar com async/await + join |
| 9 | LOW | Ausência de integridade referencial | `AppManager.js:131-137` | delete de usuário deixa matrículas/pagamentos órfãos; `err` do callback nunca checado, sempre responde 200 | FK + checar `err` |
| 10 | LOW | Nomenclatura críptica | `AppManager.js:29-33` | variáveis `u`, `e`, `p`, `cid`, `cc` e body com `usr`, `eml`, `pwd`, `c_id` | Renomear |
| 11 | LOW | Magic number na regra de aprovação | `AppManager.js:46` | `"4"` sem nome/constante que explique o critério | Extrair constante nomeada |

## Detalhamento

### [CRITICAL-1] Credenciais de produção hardcoded

- **Local:** `utils.js:1-7`
- **Evidência:**
  ```js
  const config = {
      dbUser: "admin_master",
      dbPass: "senha_super_secreta_prod_123",
      paymentGatewayKey: "pk_live_1234567890abcdef",
      smtpUser: "no-reply@fullcycle.com.br",
      port: 3000
  };
  ```
- **Impacto:** comprometimento total de banco e gateway de pagamento se o repositório vazar.
- **Correção proposta:** playbook item 2 — `process.env.*`.
- **Risco da correção:** baixo.

### [CRITICAL-2] Exposição de dado sensível em log

- **Local:** `AppManager.js:45`
- **Evidência:**
  ```js
  console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
  ```
- **Impacto:** número completo do cartão do cliente gravado em log de aplicação — violação direta de PCI-DSS.
- **Correção proposta:** remover o log ou mascarar (`cc.slice(-4)`), nunca logar a chave do gateway.
- **Risco da correção:** baixo.

### [CRITICAL-3] Criptografia insegura e reversível

- **Local:** `utils.js:17-23`
- **Evidência:**
  ```js
  function badCrypto(pwd) {
      let hash = "";
      for(let i = 0; i < 10000; i++) {
          hash += Buffer.from(pwd).toString('base64').substring(0, 2);
      }
      return hash.substring(0, 10);
  }
  ```
- **Impacto:** determinístico e sem salt — os 10 caracteres retornados são só o início do base64 da senha repetido; não protege a senha em caso de vazamento do banco.
- **Correção proposta:** playbook item 10 — `bcrypt`/`argon2`.
- **Risco da correção:** médio — invalida senhas já armazenadas com o esquema antigo (requer reset ou migração).

### [CRITICAL-4] Ausência de autenticação/autorização

- **Local:** `AppManager.js:80-129` (`GET /api/admin/financial-report`), `AppManager.js:131-137` (`DELETE /api/users/:id`)
- **Evidência:**
  ```js
  app.get('/api/admin/financial-report', (req, res) => { /* sem checagem de identidade */ });
  app.delete('/api/users/:id', (req, res) => { /* idem */ });
  ```
- **Impacto:** qualquer chamador lê receita e dados de alunos, ou apaga qualquer usuário.
- **Correção proposta:** playbook item 4 — middleware de auth real nas duas rotas.
- **Risco da correção:** baixo.

### [HIGH-1] Ausência de transação em operação multi-etapa

- **Local:** `AppManager.js:50-62`
- **Evidência:**
  ```js
  this.db.run("INSERT INTO enrollments ...", [userId, cid], function(err) {
      let enrId = this.lastID;
      self.db.run("INSERT INTO payments ...", [enrId, course.price, status], function(err) {
          self.db.run("INSERT INTO audit_logs ...", [...], (err) => { ... });
      });
  });
  ```
- **Impacto:** se o insert de `payments` falhar, o aluno já está matriculado sem pagamento registrado.
- **Correção proposta:** envolver a cadeia em transação (`BEGIN`/`COMMIT`/`ROLLBACK`), verificando `err` em cada callback.
- **Risco da correção:** baixo.

## Resumo por severidade

| Severidade | Quantidade |
|---|---|
| CRITICAL | 4 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 3 |
| **Total** | **11** |

## Proposta de reestruturação MVC

Projeto não segue MVC — estrutura alvo:

```
ecommerce-api-legacy/
├── src/
│   ├── app.js                        # bootstrap
│   ├── config.js                     # variáveis de ambiente
│   ├── db/connection.js              # única fonte de conexão SQLite
│   ├── middlewares/auth.js           # guarda de autenticação
│   ├── routes/
│   │   ├── checkoutRoutes.js
│   │   ├── adminRoutes.js
│   │   └── userRoutes.js
│   ├── controllers/
│   │   ├── checkoutController.js
│   │   ├── adminController.js
│   │   └── userController.js
│   ├── services/
│   │   ├── checkoutService.js        # decisão de pagamento + transação
│   │   └── paymentGateway.js
│   └── repositories/
│       ├── userRepository.js
│       ├── courseRepository.js
│       ├── enrollmentRepository.js
│       └── paymentRepository.js
```

`AppManager.js` é dividido por domínio; a conexão sai do construtor da classe
para `db/connection.js`, reutilizada por todos os repositórios.

## Pergunta de confirmação

Encontrei 11 problemas (4 críticos, 2 altos, 2 médios, 3 baixos). Quais devo corrigir?
1. Todos
2. Apenas CRITICAL + HIGH
3. Selecionar itens específicos (informe os números)
4. Nenhum agora (só o relatório)

**Não prosseguir para a Fase 3 sem uma resposta explícita a esta pergunta.**
