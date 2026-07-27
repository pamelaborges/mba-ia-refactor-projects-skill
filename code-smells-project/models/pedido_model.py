from database import get_db


def criar_pedido(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()

    try:
        total = 0
        for item in itens:
            cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
            produto = cursor.fetchone()
            if produto is None:
                db.rollback()
                return {"erro": f"Produto {item['produto_id']} não encontrado"}
            if produto["estoque"] < item["quantidade"]:
                db.rollback()
                return {"erro": f"Estoque insuficiente para {produto['nome']}"}
            total += produto["preco"] * item["quantidade"]

        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            cursor.execute("SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],))
            produto = cursor.fetchone()
            cursor.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )

        db.commit()
        return {"pedido_id": pedido_id, "total": total}
    except Exception:
        db.rollback()
        raise


def _montar_pedidos(where_clause="", params=()):
    db = get_db()
    cursor = db.cursor()

    query = "SELECT * FROM pedidos"
    if where_clause:
        query += f" WHERE {where_clause}"
    cursor.execute(query, params)
    pedidos_rows = cursor.fetchall()
    if not pedidos_rows:
        return []

    pedido_ids = [row["id"] for row in pedidos_rows]
    placeholders = ",".join("?" * len(pedido_ids))
    cursor.execute(
        f"""
        SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, p.nome
        FROM itens_pedido ip
        LEFT JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id IN ({placeholders})
        """,
        pedido_ids,
    )
    itens_por_pedido = {}
    for item in cursor.fetchall():
        itens_por_pedido.setdefault(item["pedido_id"], []).append({
            "produto_id": item["produto_id"],
            "produto_nome": item["nome"] if item["nome"] else "Desconhecido",
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })

    return [
        {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": itens_por_pedido.get(row["id"], []),
        }
        for row in pedidos_rows
    ]


def get_pedidos_usuario(usuario_id):
    return _montar_pedidos("usuario_id = ?", (usuario_id,))


def get_todos_pedidos():
    return _montar_pedidos()


def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
