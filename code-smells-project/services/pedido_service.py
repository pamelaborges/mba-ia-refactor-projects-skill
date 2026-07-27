from models import pedido_model
from services import notification_service


def criar_pedido(usuario_id, itens):
    resultado = pedido_model.criar_pedido(usuario_id, itens)
    if "erro" not in resultado:
        notification_service.notify_pedido_criado(usuario_id, resultado["pedido_id"])
    return resultado


def atualizar_status_pedido(pedido_id, novo_status):
    pedido_model.atualizar_status_pedido(pedido_id, novo_status)
    notification_service.notify_status_pedido(pedido_id, novo_status)
