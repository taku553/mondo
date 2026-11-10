from flask import Blueprint, g, jsonify, request

from py.auth.admin import is_admin
from py.auth.decorators import admin_required, login_required
from py.repositories import quiz_catalog, user_quiz_repo
from py.validators import validate_quiz

bp = Blueprint('quiz_create', __name__, url_prefix='/api')

MODERATIONS = (user_quiz_repo.MODERATION_NONE, user_quiz_repo.MODERATION_HIDDEN)


@bp.route('/my_quizzes', methods=['GET'])
@login_required
def list_my_quizzes():
    return jsonify(is_admin=is_admin(g.user_uid), quizzes=user_quiz_repo.list_by_author(g.user_uid))


@bp.route('/my_quizzes', methods=['POST'])
@login_required
def create():
    quiz, errors = validate_quiz(request.get_json(silent=True))
    if errors:
        return jsonify(errors=errors), 400
    quiz_id = user_quiz_repo.create_quiz(g.user_uid, quiz, is_admin(g.user_uid))
    quiz_catalog.invalidate_cache()
    return jsonify(id=quiz_id), 201


@bp.route('/my_quizzes/<quiz_id>', methods=['PUT'])
@login_required
def update(quiz_id):
    quiz, errors = validate_quiz(request.get_json(silent=True))
    if errors:
        return jsonify(errors=errors), 400
    result = user_quiz_repo.update_quiz(quiz_id, g.user_uid, quiz, is_admin(g.user_uid))
    if result == user_quiz_repo.NOT_FOUND:
        return jsonify(error='not found'), 404
    if result == user_quiz_repo.MODERATED:
        return jsonify(error='quiz is hidden by moderation'), 403
    quiz_catalog.invalidate_cache()
    return jsonify(ok=True)


@bp.route('/my_quizzes/<quiz_id>', methods=['DELETE'])
@login_required
def delete(quiz_id):
    if not user_quiz_repo.delete_quiz(quiz_id, g.user_uid):
        return jsonify(error='not found'), 404
    quiz_catalog.invalidate_cache()
    return jsonify(ok=True)


@bp.route('/admin/my_quizzes', methods=['GET'])
@login_required
@admin_required
def list_all_user_quizzes():
    return jsonify(quizzes=user_quiz_repo.list_all_user_quizzes())


@bp.route('/admin/my_quizzes/<quiz_id>/moderation', methods=['PATCH'])
@login_required
@admin_required
def moderate(quiz_id):
    data = request.get_json(silent=True) or {}
    moderation = data.get('moderation')
    if moderation not in MODERATIONS:
        return jsonify(error='moderation must be none or hidden'), 400
    if not user_quiz_repo.set_moderation(quiz_id, moderation):
        return jsonify(error='not found'), 404
    quiz_catalog.invalidate_cache()
    return jsonify(ok=True)
