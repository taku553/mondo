from flask import Blueprint, g, jsonify, request

from py.auth.decorators import login_required
from py.repositories import question_repo
from py.validators import validate_quiz

bp = Blueprint('quiz_create', __name__, url_prefix='/api/my_quizzes')


@bp.route('', methods=['GET'])
@login_required
def list_my_quizzes():
    return jsonify(question_repo.list_by_author(g.user_uid))


@bp.route('', methods=['POST'])
@login_required
def create():
    quiz, errors = validate_quiz(request.get_json(silent=True))
    if errors:
        return jsonify(errors=errors), 400
    return jsonify(question_repo.create_question(g.user_uid, quiz)), 201


@bp.route('/<quiz_id>', methods=['PUT'])
@login_required
def update(quiz_id):
    quiz, errors = validate_quiz(request.get_json(silent=True))
    if errors:
        return jsonify(errors=errors), 400
    if not question_repo.update_question(quiz_id, g.user_uid, quiz):
        return jsonify(error='not found'), 404
    return jsonify(ok=True)


@bp.route('/<quiz_id>', methods=['DELETE'])
@login_required
def delete(quiz_id):
    if not question_repo.delete_question(quiz_id, g.user_uid):
        return jsonify(error='not found'), 404
    return jsonify(ok=True)
