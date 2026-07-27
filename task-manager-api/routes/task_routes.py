from flask import Blueprint

from controllers import task_controller
from middlewares.auth import login_required

task_bp = Blueprint('tasks', __name__)

task_bp.add_url_rule('/tasks', 'get_tasks', login_required(task_controller.get_tasks), methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', 'get_task', login_required(task_controller.get_task), methods=['GET'])
task_bp.add_url_rule('/tasks', 'create_task', login_required(task_controller.create_task), methods=['POST'])
task_bp.add_url_rule('/tasks/<int:task_id>', 'update_task', login_required(task_controller.update_task), methods=['PUT'])
task_bp.add_url_rule('/tasks/<int:task_id>', 'delete_task', login_required(task_controller.delete_task), methods=['DELETE'])
task_bp.add_url_rule('/tasks/search', 'search_tasks', login_required(task_controller.search_tasks), methods=['GET'])
task_bp.add_url_rule('/tasks/stats', 'task_stats', login_required(task_controller.task_stats), methods=['GET'])
