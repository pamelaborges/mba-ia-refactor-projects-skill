from functools import wraps

import jwt
from flask import request, jsonify

import config
from models.user import User

JWT_ALGORITHM = "HS256"


def generate_token(user_id):
    return jwt.encode({"user_id": user_id}, config.SECRET_KEY, algorithm=JWT_ALGORITHM)


def _get_current_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(auth_header[7:], config.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    return User.query.get(payload.get("user_id"))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if not user:
            return jsonify({"error": "Não autorizado"}), 401
        request.current_user = user
        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if not user:
            return jsonify({"error": "Não autorizado"}), 401
        if not user.is_admin():
            return jsonify({"error": "Acesso restrito a administradores"}), 403
        request.current_user = user
        return f(*args, **kwargs)

    return wrapper
