"""クイズ紹介情報と問題の参照窓口（Firestore版）。

公開済み（status == published）のクイズ・問題だけを返す。
読み取り結果はプロセス内に CACHE_SECONDS 秒キャッシュし、出題のたびにFirestoreへ問い合わせないようにする。
"""
import time

from google.cloud.firestore import FieldFilter

from py.auth.firebase import get_firestore_client

CACHE_SECONDS = 300
MODERATION_HIDDEN = 'hidden'
_cache = {'loaded_at': None, 'quizzes': [], 'questions': []}

# 画面やセッションに出さない項目（作成者UIDや運営の判定は公開しない）
_HIDDEN_FIELDS = ('author_uid', 'moderation', 'updated_at')


def _load_published(collection):
    query = get_firestore_client().collection(collection).where(
        filter=FieldFilter('status', '==', 'published'))
    return [{**snapshot.to_dict(), 'id': snapshot.id} for snapshot in query.stream()]


def _public(document):
    # created_atはISO文字列にして並び替えに使えるようにする（JSON化もできる）
    return {
        key: value.isoformat() if hasattr(value, 'isoformat') else value
        for key, value in document.items()
        if key not in _HIDDEN_FIELDS
    }


def _published():
    loaded_at = _cache['loaded_at']
    if loaded_at is None or time.monotonic() - loaded_at > CACHE_SECONDS:
        quizzes = [quiz for quiz in _load_published('quizzes')
                   if quiz.get('moderation') != MODERATION_HIDDEN]
        visible_ids = {quiz['id'] for quiz in quizzes}
        questions = [question for question in _load_published('questions')
                     if question.get('quiz_id') in visible_ids]
        _cache.update(
            loaded_at=time.monotonic(),
            quizzes=sorted((_public(quiz) for quiz in quizzes), key=lambda quiz: quiz['id']),
            questions=sorted((_public(question) for question in questions), key=lambda question: question['id']),
        )
    return _cache['quizzes'], _cache['questions']


def invalidate_cache():
    """書き込み直後に呼び、同じプロセスでは次の読み取りで最新を取り直す。"""
    _cache.update(loaded_at=None)


def list_quizzes():
    return list(_published()[0])


def get_quiz(quiz_id):
    return next((quiz for quiz in _published()[0] if quiz['id'] == quiz_id), None)


def get_published_questions(quiz_id):
    return [question for question in _published()[1] if question['quiz_id'] == quiz_id]


def get_published_question(question_id):
    return next((question for question in _published()[1] if question['id'] == question_id), None)


def list_published_questions():
    return list(_published()[1])
