from flask import Blueprint

from controllers import sistema_controller

sistema_bp = Blueprint("sistema", __name__)

sistema_bp.add_url_rule("/health", "health_check", sistema_controller.health_check, methods=["GET"])
