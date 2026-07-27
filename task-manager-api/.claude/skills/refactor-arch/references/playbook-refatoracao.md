# Playbook de Refatoração

Um padrão de transformação por anti-pattern do catálogo. Exemplos em Python e
Node.js — a ideia de cada transformação se aplica na sua stack equivalente
mesmo quando o exemplo é só de uma linguagem.

Regra geral de execução: aplicar uma transformação por vez, confirmar que a
aplicação ainda sobe, só então seguir para a próxima.

---

## 1. SQL Injection → Queries parametrizadas

**Antes (Python/sqlite3):**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```

**Depois:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```

**Antes (Node.js):**
```js
db.run(`INSERT INTO users (name, email) VALUES ('${name}', '${email}')`);
```

**Depois:**
```js
db.run("INSERT INTO users (name, email) VALUES (?, ?)", [name, email]);
```

Com ORM (SQLAlchemy/Sequelize/Prisma), o equivalente é usar sempre o query
builder/ORM — nunca `.execute(raw_sql_concatenado)`.

---

## 2. Credenciais hardcoded → Variáveis de ambiente

**Antes:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**Depois:**
```python
import os
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]  # falha explícito se ausente
```

```js
// Antes
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_..." };

// Depois
const config = {
  dbPass: process.env.DB_PASS,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
};
```

Adicionar `.env.example` (com chaves vazias) e `.env` ao `.gitignore`. Nunca
commitar o `.env` real.

---

## 3. Exposição de dados sensíveis na resposta → Serialização com allowlist

**Antes:**
```python
def to_dict(self):
    return {
        'id': self.id, 'name': self.name, 'email': self.email,
        'password': self.password,  # nunca deveria sair
        'role': self.role,
    }
```

**Depois:**
```python
def to_dict(self):
    return {
        'id': self.id, 'name': self.name, 'email': self.email,
        'role': self.role,
    }
    # campo password nunca serializado; se precisar em contexto interno,
    # crie to_dict_internal() usado só server-side, nunca em jsonify()
```

**Risco de contrato:** se algum consumidor dependia do campo removido, isso é
uma mudança de contrato — deve estar marcada como tal no relatório aprovado.

---

## 4. Ausência de autenticação → Middleware/decorator de auth real

**Antes (token gerado e nunca verificado):**
```python
return jsonify({'token': 'fake-jwt-token-' + str(user.id)})
# nenhuma outra rota lê esse token
```

**Depois:**
```python
import jwt
from functools import wraps

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Token ausente'}), 401
        try:
            payload = jwt.decode(auth[7:], app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user_id = payload['user_id']
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        return f(*args, **kwargs)
    return wrapper

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    ...
```

Para checagem de role, um decorator adicional (`@admin_required`) que valida
`request.user_id` carrega o `role` antes de prosseguir. Em Node/Express, o
equivalente é um middleware registrado na rota:
`router.delete('/users/:id', requireAuth, requireAdmin, handler)`.

Se o projeto já tem infraestrutura pronta e não usada (`is_admin()`,
`check_password()`), **reaproveitar essas funções** dentro do middleware em
vez de reescrever a checagem.

Depois de aplicar middleware, auditar a tabela completa de rotas: relatórios,
listagens globais, escrita, deleção e rotas administrativas devem estar
protegidas. Em endpoints públicos de cadastro/login, ignorar ou rejeitar campos
privilegiados vindos do cliente (`role`, `is_admin`, `active`, permissões);
atribua defaults seguros no servidor e mova mudanças de papel para uma rota
administrativa protegida.

Quando o domínio tiver proprietário do recurso (`user_id`, `owner_id`,
`account_id`), a correção não termina no token: controllers devem verificar
`current_user.id == recurso.user_id` ou `current_user.is_admin()` antes de
retornar, atualizar, reatribuir ou deletar. Listagens globais devem virar
admin-only ou filtrar por `current_user.id` para usuários comuns.

Validação mínima: chamar cada rota sensível sem token e esperar 401/403; chamar
cadastro público com `role=admin` e confirmar que o usuário resultante não vira
admin; autenticar como usuário comum e tentar ler/alterar recurso de outro
usuário, esperando 403.

---

## 5. Operações multi-etapa sem transação → Transação explícita com rollback

**Antes:**
```python
cursor.execute("INSERT INTO pedidos (...) VALUES (...)")
pedido_id = cursor.lastrowid
for item in itens:
    cursor.execute("INSERT INTO itens_pedido (...) VALUES (...)")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (...))
db.commit()
```

**Depois:**
```python
try:
    cursor.execute("BEGIN")
    cursor.execute("INSERT INTO pedidos (...) VALUES (...)")
    pedido_id = cursor.lastrowid
    for item in itens:
        cursor.execute("INSERT INTO itens_pedido (...) VALUES (...)")
        cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (...))
    db.commit()
except Exception:
    db.rollback()
    raise
```

Com SQLAlchemy, o equivalente é garantir `db.session.rollback()` no `except` de
**todo** bloco que faz `db.session.commit()` (muitos handlers já fazem isso
individualmente — o padrão aqui é generalizar a operação multi-tabela dentro de
uma única unidade de trabalho, não múltiplos commits parciais).

Em Node.js com callbacks aninhados, envolver a cadeia em
`db.serialize()`/`BEGIN TRANSACTION` e emitir `ROLLBACK` no primeiro `err`
recebido em qualquer callback da cadeia — hoje o `err` costuma ser ignorado.

---

## 6. Queries N+1 → Eager loading / join

**Antes (SQLAlchemy):**
```python
tasks = Task.query.all()
for t in tasks:
    user = User.query.get(t.user_id)      # 1 query por task
    cat = Category.query.get(t.category_id)  # +1 query por task
```

**Depois:**
```python
from sqlalchemy.orm import joinedload

tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
for t in tasks:
    user = t.user       # já carregado, sem query adicional
    cat = t.category
```

**Antes (SQL bruto, pedidos → itens → produto):**
```python
for pedido in pedidos:
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido['id'],))
    for item in itens:
        cursor.execute("SELECT nome FROM produtos WHERE id = ?", (item['produto_id'],))
```

**Depois:**
```python
cursor.execute("""
    SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, p.nome
    FROM itens_pedido ip JOIN produtos p ON p.id = ip.produto_id
    WHERE ip.pedido_id IN (%s)
""" % ",".join("?" * len(pedido_ids)), pedido_ids)
# uma query para todos os itens de todos os pedidos, depois agrupar em memória
```

---

## 7. Regra de negócio no controller → Camada de serviço extraída

**Antes:**
```python
def criar_pedido():
    dados = request.get_json()
    resultado = models.criar_pedido(dados['usuario_id'], dados['itens'])
    print("ENVIANDO EMAIL: Pedido criado")  # efeito colateral inline
    return jsonify(resultado), 201
```

**Depois:**
```python
# services/pedido_service.py
class PedidoService:
    def __init__(self, pedido_repo, notification_service):
        self.pedido_repo = pedido_repo
        self.notifications = notification_service

    def criar_pedido(self, usuario_id, itens):
        resultado = self.pedido_repo.criar(usuario_id, itens)
        self.notifications.notify_pedido_criado(usuario_id, resultado['pedido_id'])
        return resultado

# controllers/pedido_controller.py
def criar_pedido():
    dados = request.get_json()
    resultado = pedido_service.criar_pedido(dados['usuario_id'], dados['itens'])
    return jsonify(resultado), 201
```

`PedidoService.criar_pedido` agora é testável com repositório e serviço de
notificação mockados, sem subir Flask nem SQLite.

Mesmo padrão para "pagamento mockado no handler" (`ecommerce-api-legacy`):
extrair para um `PaymentGateway` (interface) com uma implementação mock
isolada — a decisão de aprovar/negar deixa de estar hardcoded no controller.

---

## 8. Duplicação de código / abstração não usada → Consolidar no ponto único

**Antes:** `is_overdue()` existe em `Task` e a mesma cadeia de `if` está
copiada em 5 rotas diferentes.

```python
# em 5 lugares diferentes:
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            overdue = True
```

**Depois:**
```python
# usar o método já existente em todos os pontos:
overdue = t.is_overdue()
```

Para validação duplicada e divergente entre criar/atualizar, extrair uma única
função de validação chamada pelos dois fluxos:

```python
# Antes: criar_produto e atualizar_produto repetem as mesmas 8 checagens,
# mas atualizar_produto perdeu duas delas.

# Depois:
def validar_produto(dados, parcial=False):
    erros = []
    if not parcial or 'nome' in dados:
        if len(dados.get('nome', '')) < 2 or len(dados.get('nome', '')) > 200:
            erros.append('Nome inválido')
    if not parcial or 'categoria' in dados:
        if dados.get('categoria') not in CATEGORIAS_VALIDAS:
            erros.append('Categoria inválida')
    return erros

# criar_produto e atualizar_produto chamam validar_produto() — uma só fonte de verdade
```

---

## 9. Tratamento de erro genérico → Exceções específicas + status correto

**Antes:**
```python
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```

**Depois:**
```python
class ValidationError(Exception):
    pass

try:
    ...
except ValidationError as e:
    return jsonify({"erro": str(e)}), 400
except Exception as e:
    app.logger.exception("Erro inesperado")  # log completo, servidor
    return jsonify({"erro": "Erro interno"}), 500  # mensagem genérica, cliente
```

Em Node.js, checar `err` em **todo** callback antes de prosseguir, em vez de
ignorá-lo silenciosamente:

```js
// Antes
this.db.run(sql, params, (err) => { res.send("ok"); });

// Depois
this.db.run(sql, params, (err) => {
  if (err) return res.status(500).json({ error: "Erro ao processar" });
  res.status(200).json({ ok: true });
});
```

---

## 10. APIs deprecated → Substituto moderno

**Antes:**
```python
created_at = datetime.utcnow()
```

**Depois (Python 3.12+):**
```python
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

**Antes (hash de senha com MD5):**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

**Depois:**
```python
from werkzeug.security import generate_password_hash, check_password_hash
self.password = generate_password_hash(pwd)
# checagem: check_password_hash(self.password, pwd)
```

Antes de aplicar qualquer troca desta categoria, confirmar a versão real da
linguagem/framework instalada (Fase 1) — não trocar uma API que ainda é válida
na versão em uso.

---

## 11. God Object / baixa coesão → Split por domínio

**Antes (Node.js, uma classe concentra conexão + rotas + regra de negócio):**
```js
class AppManager {
    constructor() {
        this.db = new sqlite3.Database(':memory:');
    }
    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => {
            // valida input, decide aprovação de pagamento, faz INSERT direto
            this.db.run("INSERT INTO enrollments ...", [...], (err) => { ... });
        });
        app.get('/api/admin/financial-report', (req, res) => { /* SQL direto */ });
    }
}
```

**Depois:** conexão isolada, rota fina, regra de negócio em serviço próprio:
```js
// db/connection.js — única fonte de conexão, reutilizada por todos os repositórios
const db = new sqlite3.Database(process.env.DB_PATH || ':memory:');
module.exports = db;

// repositories/enrollmentRepository.js
const db = require('../db/connection');
function createEnrollment(userId, courseId) {
    return new Promise((resolve, reject) => {
        db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            [userId, courseId], function (err) { err ? reject(err) : resolve(this.lastID); });
    });
}
module.exports = { createEnrollment };

// services/checkoutService.js
const { createEnrollment } = require('../repositories/enrollmentRepository');
async function checkout(userId, courseId, card) {
    const status = paymentGateway.charge(card);       // decisão de pagamento isolada
    if (status === 'DENIED') throw new PaymentDeniedError();
    return createEnrollment(userId, courseId);
}
module.exports = { checkout };

// routes/checkout.js — só HTTP: extrai request, chama serviço, traduz resposta
router.post('/api/checkout', async (req, res) => {
    try {
        const enrollmentId = await checkoutService.checkout(req.body.usr, req.body.c_id, req.body.card);
        res.status(200).json({ enrollment_id: enrollmentId });
    } catch (e) {
        res.status(e instanceof PaymentDeniedError ? 400 : 500).json({ error: e.message });
    }
});
```

Mesmo padrão em Python: `models.py` monolítico (produtos+usuários+pedidos) vira
`models/produto.py`, `models/usuario.py`, `models/pedido.py`, cada um só com o
acesso a dados da própria entidade — a conexão sai para `database.py` e passa a
ser importada, nunca reaberta dentro de cada model.

---

## 12. CORS irrestrito / rotas administrativas públicas → Allowlist e guarda de ambiente

**Antes:**
```python
CORS(app)  # qualquer origem
app.add_url_rule("/admin/reset-db", ..., methods=["POST"])  # sem guarda nenhuma
```

**Depois:**
```python
CORS(app, origins=os.environ.get("ALLOWED_ORIGINS", "").split(","))

@app.route("/admin/reset-db", methods=["POST"])
@login_required
@admin_required
def reset_database():
    if os.environ.get("ENV") == "production":
        return jsonify({"erro": "Indisponível em produção"}), 403
    ...
```

---

## Ordem de aplicação

Comece pelo item 11 (split estrutural) quando aprovado — ele muda onde os
arquivos vivem, e fazer isso depois das outras correções significa refazer o
mesmo diff duas vezes. Depois, siga a ordem de severidade do relatório
(CRITICAL → LOW): a maioria das correções de segurança (1–4) são locais e não
dependem umas das outras, então cabem em qualquer ordem entre si. Deixe a
modernização de APIs deprecated (10) por último — é a que menos quebra nada se
for interrompida no meio.
