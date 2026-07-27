# Relatório de Auditoria Arquitetural — task-manager-api

**Data:** 2026-07-27
**Stack detectada:** Python 3 / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 / SQLite
**Baseado na Fase 1:** ver "Resumo da Análise" — projeto parcialmente organizado (blueprints/models/services/utils já separados), mas com abstrações prontas que nenhuma rota usa

## Sumário executivo

Diferente dos outros dois projetos, este já tem a forma de uma boa arquitetura
— blueprints, models SQLAlchemy, uma pasta `services/` e uma `utils/` — mas as
abstrações existem e não são usadas: `NotificationService` nunca é importado,
`is_overdue()` do model nunca é chamado (a mesma lógica está copiada em 5
rotas), e `utils.helpers.process_task_data`/constantes nunca são importados
pelas rotas que fazem a mesma validação inline. O achado mais grave é
estrutural, não sintático: nenhuma rota verifica identidade, e o campo
`password` vaza até na resposta do próprio `/login`.

## Achados por severidade

| # | Severidade | Problema | Localização | Observações | Ação proposta |
|---|:----------:|---|---|---|---|
| 1 | CRITICAL | Exposição de dados sensíveis | `models/user.py:16-25` | `to_dict()` inclui `password`; vaza em `GET /users`, `POST /users`, `PUT /users` e no `/login` | Serialização com allowlist |
| 2 | CRITICAL | Criptografia insegura | `models/user.py:27-32` | MD5 sem salt, senha mínima de 4 caracteres | bcrypt/argon2 |
| 3 | CRITICAL | Ausência de autenticação/autorização | `routes/*` (todas as rotas) | token do login (`user_routes.py:210`) nunca é verificado em nenhuma rota; `PUT /users/<id>` aceita mudança de `role` sem checagem | Middleware de auth real |
| 4 | CRITICAL | Exposição de credenciais | `services/notification_service.py:7-10`, `app.py:13` | SMTP e `SECRET_KEY` hardcoded | Variáveis de ambiente |
| 5 | HIGH | Abstração pronta e não utilizada | `models/task.py:50-60` | `is_overdue()` existe; a mesma lógica está copiada em `task_routes.py:30,71,284`, `user_routes.py:171`, `report_routes.py:34` | Usar o método existente |
| 6 | MEDIUM | Queries N+1 | `task_routes.py:41-57`, `report_routes.py:53-68` | busca usuário/categoria por task em loop, apesar dos relacionamentos declarados | `joinedload` |
| 7 | MEDIUM | Validação duplicada em 3 camadas | `utils/helpers.py:57-108`, `models/task.py:38-48`, `task_routes.py:110-114` | mesmas regras em 3 lugares; só a inline nas rotas roda | Consolidar em uma camada |
| 8 | MEDIUM | Ausência de integridade referencial explícita | `models/task.py:13`, `user_routes.py:140-142` | delete de usuário remove tasks em loop Python; delete de categoria não trata tasks vinculadas | FK com cascade |
| 9 | LOW | Tratamento de exceção genérico | `task_routes.py:62,137,204`, `user_routes.py:130` | `except:` nu descarta a causa raiz | Exceções específicas |
| 10 | LOW | Código morto | `services/notification_service.py` | não é importado por nenhuma rota, mas ainda expõe credencial SMTP | Remover ou integrar |

## Detalhamento

### [CRITICAL-1] Exposição de dados sensíveis na resposta da API

- **Local:** `models/user.py:16-25`
- **Evidência:**
  ```python
  def to_dict(self):
      return {
          'id': self.id, 'name': self.name, 'email': self.email,
          'password': self.password,
          'role': self.role, 'active': self.active,
          'created_at': str(self.created_at)
      }
  ```
- **Impacto:** o hash da senha de qualquer usuário vaza em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e na resposta do próprio `/login` (`user_routes.py:209`).
- **Correção proposta:** playbook item 3 — remover `password` do dict serializado.
- **Risco da correção:** médio — muda contrato de resposta desses endpoints.

### [CRITICAL-2] Criptografia insegura

- **Local:** `models/user.py:27-32`
- **Evidência:**
  ```python
  def set_password(self, pwd):
      self.password = hashlib.md5(pwd.encode()).hexdigest()
  ```
- **Impacto:** MD5 sem salt é quebrável por rainbow table; combinado com senha mínima de 4 caracteres, o ataque é trivial.
- **Correção proposta:** playbook item 10 — `werkzeug.security.generate_password_hash`.
- **Risco da correção:** médio — invalida hashes existentes (requer reset de senha ou migração).

### [CRITICAL-3] Ausência de autenticação/autorização

- **Local:** todas as rotas em `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- **Evidência:**
  ```python
  return jsonify({..., 'token': 'fake-jwt-token-' + str(user.id)}), 200
  # nenhuma rota lê o header Authorization nem verifica esse token
  ```
- **Impacto:** qualquer chamador deleta usuários, promove a `role: admin` via `PUT /users/<id>`, ou acessa dados de qualquer conta.
- **Correção proposta:** playbook item 4 — middleware `login_required`, reaproveitando `check_password`/`is_admin` já existentes.
- **Risco da correção:** médio — requer que o cliente passe a enviar o token.

### [CRITICAL-4] Exposição de credenciais hardcoded

- **Local:** `services/notification_service.py:7-10`, `app.py:13`
- **Evidência:**
  ```python
  self.email_password = 'senha123'
  # app.py
  app.config['SECRET_KEY'] = 'super-secret-key-123'
  ```
- **Impacto:** credencial SMTP e chave de assinatura de sessão versionadas no código.
- **Correção proposta:** playbook item 2 — variáveis de ambiente.
- **Risco da correção:** baixo.

### [HIGH-1] Abstração pronta e não utilizada (duplicação)

- **Local:** `models/task.py:50-60` (`is_overdue`), copiado em 5 rotas
- **Evidência:**
  ```python
  # copiado em task_routes.py:30, :71, :284, user_routes.py:171, report_routes.py:34
  if t.due_date:
      if t.due_date < datetime.utcnow():
          if t.status != 'done' and t.status != 'cancelled':
              overdue = True
  ```
- **Impacto:** qualquer mudança na regra de "atrasado" precisa ser replicada manualmente em 5 lugares.
- **Correção proposta:** playbook item 8 — substituir todas as ocorrências por `t.is_overdue()`.
- **Risco da correção:** baixo.

## Resumo por severidade

| Severidade | Quantidade |
|---|---|
| CRITICAL | 4 |
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 2 |
| **Total** | **10** |

## Proposta de reestruturação MVC

O projeto já tem a divisão de pastas (`routes/`, `models/`, `services/`,
`utils/`), então a reestruturação aqui é menor que nos outros dois projetos:
introduzir uma camada `controllers/` fina entre rotas e domínio, e passar a
efetivamente usar o que já existe:

```
task-manager-api/
├── app.py
├── config.py                    # SECRET_KEY via variável de ambiente
├── database.py
├── routes/                      # mantém, mas delega tudo ao controller
├── controllers/                 # novo — orquestra rota → serviço → resposta
│   ├── task_controller.py
│   ├── user_controller.py
│   └── report_controller.py
├── middlewares/auth.py          # novo — login_required / admin_required
├── services/
│   └── notification_service.py  # mantém, passa a ser chamado
├── models/                      # mantém, passa a ser efetivamente usado
└── utils/helpers.py              # mantém, passa a ser efetivamente usado
```

## Pergunta de confirmação

Encontrei 10 problemas (4 críticos, 1 alto, 3 médios, 2 baixos). Quais devo corrigir?
1. Todos
2. Apenas CRITICAL + HIGH
3. Selecionar itens específicos (informe os números)
4. Nenhum agora (só o relatório)

**Não prosseguir para a Fase 3 sem uma resposta explícita a esta pergunta.**
