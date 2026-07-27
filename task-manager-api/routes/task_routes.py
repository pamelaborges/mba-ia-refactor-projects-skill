import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from services.notification_service import NotificationService
from utils.helpers import process_task_data
from middlewares.auth import login_required

logger = logging.getLogger(__name__)
task_bp = Blueprint('tasks', __name__)
notification_service = NotificationService()


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
        result = []
        for t in tasks:
            task_data = t.to_dict()
            task_data['overdue'] = t.is_overdue()
            task_data['user_name'] = t.user.name if t.user else None
            task_data['category_name'] = t.category.name if t.category else None
            result.append(task_data)

        return jsonify(result), 200
    except Exception:
        logger.exception("Erro ao listar tasks")
        return jsonify({'error': 'Erro interno'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return jsonify(data), 200


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    title = data.get('title')
    if not title:
        return jsonify({'error': 'Título é obrigatório'}), 400

    campos, erro = process_task_data(data)
    if erro:
        return jsonify({'error': erro}), 400

    user_id = data.get('user_id')
    category_id = data.get('category_id')

    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

    if category_id:
        cat = Category.query.get(category_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

    task = Task()
    task.title = campos.get('title', title)
    task.description = campos.get('description', data.get('description', ''))
    task.status = campos.get('status', data.get('status', 'pending'))
    task.priority = campos.get('priority', data.get('priority', 3))
    task.user_id = user_id
    task.category_id = category_id
    task.due_date = campos.get('due_date')
    if 'tags' in campos:
        task.tags = campos['tags']

    try:
        db.session.add(task)
        db.session.commit()
        logger.info("Task criada: %s - %s", task.id, task.title)

        if task.user_id:
            notification_service.notify_task_assigned(task.user, task)

        return jsonify(task.to_dict()), 201
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao criar task")
        return jsonify({'error': 'Erro ao criar task'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    campos, erro = process_task_data(data)
    if erro:
        return jsonify({'error': erro}), 400

    if 'user_id' in data:
        if data['user_id']:
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id']:
            cat = Category.query.get(data['category_id'])
            if not cat:
                return jsonify({'error': 'Categoria não encontrada'}), 404
        task.category_id = data['category_id']

    for campo in ('title', 'description', 'status', 'priority', 'tags'):
        if campo in campos:
            setattr(task, campo, campos[campo])
    if 'due_date' in campos:
        task.due_date = campos['due_date']

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        logger.info("Task atualizada: %s", task.id)
        return jsonify(task.to_dict()), 200
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao atualizar task %s", task_id)
        return jsonify({'error': 'Erro ao atualizar'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info("Task deletada: %s", task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao deletar task %s", task_id)
        return jsonify({'error': 'Erro ao deletar'}), 500


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    results = tasks.all()
    return jsonify([t.to_dict() for t in results]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }

    return jsonify(stats), 200
