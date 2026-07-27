import logging

from flask import request, jsonify

from models import pedido_model
from services import pedido_service
from errors import ValidationError

logger = logging.getLogger(__name__)


def criar_pedido():
    try:
        dados = request.get_json()
        if not dados:
            raise ValidationError("Dados inválidos")

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens:
            raise ValidationError("Pedido deve ter pelo menos 1 item")

        resultado = pedido_service.criar_pedido(usuario_id, itens)
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao criar pedido")
        return jsonify({"erro": "Erro interno"}), 500


def listar_pedidos_usuario(usuario_id):
    try:
        pedidos = pedido_model.get_pedidos_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar pedidos do usuario %s", usuario_id)
        return jsonify({"erro": "Erro interno"}), 500


def listar_todos_pedidos():
    try:
        pedidos = pedido_model.get_todos_pedidos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar pedidos")
        return jsonify({"erro": "Erro interno"}), 500


def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json()
        novo_status = dados.get("status", "") if dados else ""

        if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]:
            raise ValidationError("Status inválido")

        pedido_service.atualizar_status_pedido(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao atualizar status do pedido %s", pedido_id)
        return jsonify({"erro": "Erro interno"}), 500


def relatorio_vendas():
    try:
        relatorio = pedido_model.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao gerar relatorio de vendas")
        return jsonify({"erro": "Erro interno"}), 500
