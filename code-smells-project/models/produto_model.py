from database import get_db


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    return [_row_to_dict(row) for row in cursor.fetchall()]


def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def criar_produto(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar_produto(id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, id),
    )
    db.commit()
    return True


def deletar_produto(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    db.commit()
    return True


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    cursor = db.cursor()

    condicoes = []
    params = []
    if termo:
        condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        condicoes.append("categoria = ?")
        params.append(categoria)
    if preco_min:
        condicoes.append("preco >= ?")
        params.append(preco_min)
    if preco_max:
        condicoes.append("preco <= ?")
        params.append(preco_max)

    query = "SELECT * FROM produtos"
    if condicoes:
        query += " WHERE " + " AND ".join(condicoes)

    cursor.execute(query, params)
    return [_row_to_dict(row) for row in cursor.fetchall()]
