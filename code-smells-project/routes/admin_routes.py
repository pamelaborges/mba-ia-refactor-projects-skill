import logging

from flask import Blueprint, request, jsonify

from database import get_db
from middlewares.auth import admin_required

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/reset-db", methods=["POST"])
@admin_required
def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@admin_bp.route("/query", methods=["POST"])
@admin_required
def executar_query():
    dados = request.get_json()
    query = dados.get("sql", "") if dados else ""
    if not query:
        return jsonify({"erro": "Query não informada"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            return jsonify({"dados": result, "sucesso": True}), 200
        db.commit()
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao executar query administrativa")
        return jsonify({"erro": "Erro ao executar query"}), 500
