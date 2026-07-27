import logging

from flask import request, jsonify

from models import usuario_model
from errors import ValidationError

logger = logging.getLogger(__name__)


def listar_usuarios():
    try:
        usuarios = usuario_model.get_todos_usuarios()
        return jsonify({"dados": usuarios, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar usuarios")
        return jsonify({"erro": "Erro interno"}), 500


def buscar_usuario(id):
    try:
        usuario = usuario_model.get_usuario_por_id(id)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception:
        logger.exception("Erro ao buscar usuario %s", id)
        return jsonify({"erro": "Erro interno"}), 500


def criar_usuario():
    try:
        dados = request.get_json()
        if not dados:
            raise ValidationError("Dados inválidos")

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")

        id = usuario_model.criar_usuario(nome, email, senha)
        logger.info("Usuário criado: %s", email)
        return jsonify({"dados": {"id": id}, "sucesso": True}), 201
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao criar usuario")
        return jsonify({"erro": "Erro interno"}), 500


def login():
    try:
        dados = request.get_json()
        email = dados.get("email", "") if dados else ""
        senha = dados.get("senha", "") if dados else ""

        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")

        usuario = usuario_model.login_usuario(email, senha)
        if usuario:
            logger.info("Login bem-sucedido: %s", email)
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

        logger.info("Login falhou: %s", email)
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro no login")
        return jsonify({"erro": "Erro interno"}), 500
