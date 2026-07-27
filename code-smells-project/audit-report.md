# Relatório de Auditoria Arquitetural — code-smells-project

**Data:** 2026-07-27
**Stack detectada:** Python 3 / Flask 3.1.1 / SQLite (acesso direto via `sqlite3`, sem ORM)
**Baseado na Fase 1:** ver "Resumo da Análise" — arquitetura monolítica em 4 arquivos, sem separação de camadas

## Sumário executivo

O projeto concentra toda a lógica (SQL, regra de negócio, validação e resposta HTTP)
em 4 arquivos sem camada de serviço. O risco dominante é segurança: SQL Injection
sistêmico por concatenação de string em praticamente toda query, incluindo o
login — o que permite bypass de autenticação — e duas rotas administrativas
(`/admin/reset-db`, `/admin/query`) publicamente acessíveis sem qualquer verificação.
Padrão de duplicação recorrente: a lógica de itens de pedido está copiada
integralmente entre `get_pedidos_usuario` e `get_todos_pedidos`.

## Achados por severidade

| # | Severidade | Problema | Localização | Observações | Ação proposta |
|---|:----------:|---|---|---|---|
| 1 | CRITICAL | SQL Injection por concatenação | `models.py` (14 ocorrências) | login em `models.py:109-111` permite bypass com `' OR '1'='1' --` | Parametrizar todas as queries |
| 2 | CRITICAL | Endpoints admin sem autenticação | `app.py:47-78` | reset de banco e SQL arbitrário públicos | Middleware de auth + guarda de ambiente |
| 3 | CRITICAL | Exposição de credenciais/segredos | `app.py:7-8`, `controllers.py:285-289` | `SECRET_KEY` hardcoded e devolvida no `/health` junto com `debug:true` | Variável de ambiente |
| 4 | CRITICAL | Exposição de senha na resposta da API | `models.py:79-86, 94-102` | `get_todos_usuarios`/`get_usuario_por_id` retornam campo `senha` | Serialização com allowlist |
| 5 | HIGH | Ausência de transação em `criar_pedido` | `models.py:133-169` | falha no meio do loop deixa insert parcial sem rollback | Transação explícita com rollback |
| 6 | MEDIUM | Queries N+1 e duplicação de função | `models.py:171-233` | `get_pedidos_usuario` e `get_todos_pedidos` são a mesma lógica copiada | Extrair função única + join |
| 7 | MEDIUM | Regra de negócio no controller | `controllers.py:208-210, 247-250` | notificação simulada via `print` direto no handler HTTP | Extrair `NotificationService` |
| 8 | MEDIUM | Validação divergente entre criar/atualizar | `controllers.py:28-54` vs `72-90` | `atualizar_produto` perdeu a checagem de tamanho de nome e categoria válida | Função de validação única |
| 9 | LOW | Tratamento de erro genérico | `controllers.py` (16 handlers) | `except Exception as e: return jsonify({"erro": str(e)})` em todos | Exceções específicas + status correto |
| 10 | LOW | CORS irrestrito | `app.py:9` | `CORS(app)` sem allowlist | Restringir por `ALLOWED_ORIGINS` |

## Detalhamento

### [CRITICAL-1] SQL Injection por concatenação de strings

- **Local:** `models.py:109-111` (mais crítico), também em `models.py:28,48,58,68,92,126,140,148,155,163,174,188,192,206,220,224,279,289-297`
- **Evidência:**
  ```python
  cursor.execute(
      "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
  )
  ```
- **Impacto:** bypass de autenticação com `email = "' OR '1'='1' --"`; leitura/escrita arbitrária no banco em qualquer outro endpoint que recebe input do usuário.
- **Correção proposta:** playbook item 1 — queries parametrizadas com `?`.
- **Risco da correção:** baixo — não muda contrato de resposta.

### [CRITICAL-2] Endpoints administrativos sem autenticação

- **Local:** `app.py:47-57` (`/admin/reset-db`), `app.py:59-78` (`/admin/query`)
- **Evidência:**
  ```python
  @app.route("/admin/query", methods=["POST"])
  def executar_query():
      dados = request.get_json()
      query = dados.get("sql", "")
      cursor.execute(query)  # SQL arbitrário do body, sem checagem de identidade
  ```
- **Impacto:** qualquer chamador externo apaga o banco inteiro ou executa SQL arbitrário — o prefixo `/admin` é apenas nomenclatura, não controle de acesso.
- **Correção proposta:** playbook item 12 (guarda de ambiente) + item 4 (middleware de auth real).
- **Risco da correção:** baixo, mas requer decidir se essas rotas devem existir em produção.

### [CRITICAL-3] Exposição de credenciais e segredos

- **Local:** `app.py:7-8`, `controllers.py:285-289`
- **Evidência:**
  ```python
  app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
  app.config["DEBUG"] = True
  # ...
  return jsonify({..., "debug": True, "secret_key": "minha-chave-super-secreta-123"}), 200
  ```
- **Impacto:** o `/health` devolve a própria `SECRET_KEY` usada para assinar sessão/token a qualquer chamador.
- **Correção proposta:** playbook item 2 — variável de ambiente, nunca no corpo de resposta.
- **Risco da correção:** baixo.

### [CRITICAL-4] Exposição de senha na resposta da API

- **Local:** `models.py:79-86` (`get_todos_usuarios`), `models.py:94-102` (`get_usuario_por_id`)
- **Evidência:**
  ```python
  result.append({
      "id": row["id"], "nome": row["nome"], "email": row["email"],
      "senha": row["senha"], "tipo": row["tipo"], "criado_em": row["criado_em"]
  })
  ```
- **Impacto:** `GET /usuarios` e `GET /usuarios/<id>` vazam a senha (texto plano, já que não há hashing em `criar_usuario`) de todos os usuários.
- **Correção proposta:** playbook item 3 — allowlist de campos serializados.
- **Risco da correção:** médio — muda o contrato de resposta desses 2 endpoints; deve ser aprovado explicitamente.

### [HIGH-1] Ausência de transação em operação multi-etapa

- **Local:** `models.py:133-169` (`criar_pedido`)
- **Evidência:**
  ```python
  for item in itens:
      cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
      produto = cursor.fetchone()
      if produto["estoque"] < item["quantidade"]:
          return {"erro": "Estoque insuficiente..."}  # sai sem rollback do que já rodou
  ```
- **Impacto:** condição de corrida entre checagem de estoque e decremento; múltiplas requisições concorrentes podem vender o mesmo estoque.
- **Correção proposta:** playbook item 5 — transação explícita com rollback.
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

Projeto não segue MVC — estrutura alvo:

```
code-smells-project/
├── app.py                      # bootstrap + registro de rotas
├── config.py                   # SECRET_KEY via variável de ambiente
├── database.py                 # conexão (mantém, ajustar para pool/factory)
├── routes/
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   └── pedido_routes.py
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── services/
│   ├── notification_service.py  # extrai os prints de controllers.py
│   └── pedido_service.py        # regra de negócio + transação de criar_pedido
└── models/
    ├── produto_model.py
    ├── usuario_model.py
    └── pedido_model.py
```

`models.py`, `controllers.py` e `app.py` atuais são divididos por domínio
(produtos/usuários/pedidos), cada um migrando para queries parametrizadas no
mesmo movimento.

## Pergunta de confirmação

Encontrei 10 problemas (4 críticos, 1 alto, 3 médios, 2 baixos). Quais devo corrigir?
1. Todos
2. Apenas CRITICAL + HIGH
3. Selecionar itens específicos (informe os números)
4. Nenhum agora (só o relatório)

**Não prosseguir para a Fase 3 sem uma resposta explícita a esta pergunta.**
