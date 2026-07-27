import logging

from flask import request, jsonify

from models import produto_model
from services.validacao_service import validar_produto
from errors import ValidationError

logger = logging.getLogger(__name__)


def listar_produtos():
    try:
        produtos = produto_model.get_todos_produtos()
        logger.info("Listando %d produtos", len(produtos))
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar produtos")
        return jsonify({"erro": "Erro interno"}), 500


def buscar_produto(id):
    try:
        produto = produto_model.get_produto_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception:
        logger.exception("Erro ao buscar produto %s", id)
        return jsonify({"erro": "Erro interno"}), 500


def criar_produto():
    try:
        dados = request.get_json()
        if not dados:
            raise ValidationError("Dados inválidos")

        erros = validar_produto(dados)
        if erros:
            raise ValidationError(erros[0])

        id = produto_model.criar_produto(
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )
        logger.info("Produto criado com ID: %s", id)
        return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao criar produto")
        return jsonify({"erro": "Erro interno"}), 500


def atualizar_produto(id):
    try:
        produto_existente = produto_model.get_produto_por_id(id)
        if not produto_existente:
            return jsonify({"erro": "Produto não encontrado"}), 404

        dados = request.get_json()
        if not dados:
            raise ValidationError("Dados inválidos")

        erros = validar_produto(dados)
        if erros:
            raise ValidationError(erros[0])

        produto_model.atualizar_produto(
            id,
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao atualizar produto %s", id)
        return jsonify({"erro": "Erro interno"}), 500


def deletar_produto(id):
    try:
        produto = produto_model.get_produto_por_id(id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        produto_model.deletar_produto(id)
        logger.info("Produto %s deletado", id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except Exception:
        logger.exception("Erro ao deletar produto %s", id)
        return jsonify({"erro": "Erro interno"}), 500


def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)

        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)

        resultados = produto_model.buscar_produtos(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao buscar produtos")
        return jsonify({"erro": "Erro interno"}), 500
