"""クイズ紹介情報と問題の参照窓口（Firestore版）。

公開済み（status == published）のクイズ・問題だけを返す。
読み取り結果はプロセス内に CACHE_SECONDS 秒キャッシュし、出題のたびにFirestoreへ問い合わせないようにする。
"""
import time

from google.cloud.firestore import FieldFilter

from py.auth.firebase import get_firestore_client

CACHE_SECONDS = 300
_cache = {'loaded_at': None, 'quizzes': [], 'questions': []}

# 画面やセッションで使わないタイムスタンプは返さない（JSON化できないため）
_HIDDEN_FIELDS = ('created_at', 'updated_at')


def _load_published(collection):
    query = get_firestore_client().collection(collection).where(
        filter=FieldFilter('status', '==', 'published'))
    documents = []
    for snapshot in query.stream():
        data = {key: value for key, value in snapshot.to_dict().items() if key not in _HIDDEN_FIELDS}
        documents.append({**data, 'id': snapshot.id})
    return sorted(documents, key=lambda document: document['id'])


def _published():
    loaded_at = _cache['loaded_at']
    if loaded_at is None or time.monotonic() - loaded_at > CACHE_SECONDS:
        _cache.update(
            loaded_at=time.monotonic(),
            quizzes=_load_published('quizzes'),
            questions=_load_published('questions'),
        )
    return _cache['quizzes'], _cache['questions']


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
