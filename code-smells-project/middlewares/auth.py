import logging
from functools import wraps

from flask import request, jsonify

import config

logger = logging.getLogger(__name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if config.ENV == "production":
            return jsonify({"erro": "Indisponível em produção"}), 403

        token = request.headers.get("X-Admin-Token", "")
        if token != config.ADMIN_TOKEN:
            logger.warning("Tentativa de acesso admin sem token válido")
            return jsonify({"erro": "Não autorizado"}), 401

        return f(*args, **kwargs)

    return wrapper
