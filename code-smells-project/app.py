import logging

from flask import Flask, jsonify
from flask_cors import CORS

import config
from database import get_db
from routes.produto_routes import produto_bp
from routes.usuario_routes import usuario_bp
from routes.pedido_routes import pedido_bp
from routes.sistema_routes import sistema_bp
from routes.admin_routes import admin_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["DEBUG"] = config.DEBUG

CORS(app, origins=config.ALLOWED_ORIGINS)

app.register_blueprint(produto_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(pedido_bp)
app.register_blueprint(sistema_bp)
app.register_blueprint(admin_bp)


@app.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


if __name__ == "__main__":
    get_db()
    logging.info("Servidor iniciado em http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
