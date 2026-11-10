"""ユーザー作成問題のFirestore保存。

Admin SDK経由のアクセスのため、クライアント側のセキュリティルールは適用されない。
所有者チェックはこのモジュールとルート側で行う。
"""
from firebase_admin import firestore
from google.cloud.firestore import FieldFilter

from py.auth.firebase import get_firestore_client

COLLECTION = 'questions'


def _col():
    return get_firestore_client().collection(COLLECTION)


def _serialize(doc_id, data):
    result = {**data, 'id': doc_id}
    for key in ('created_at', 'updated_at'):
        if hasattr(result.get(key), 'isoformat'):
            result[key] = result[key].isoformat()
    return result


def create_question(author_uid, quiz):
    now = firestore.SERVER_TIMESTAMP
    ref = _col().document()
    ref.set({
        'source': 'user',
        'author_uid': author_uid,
        'status': 'published',
        'quiz_id': None,
        'text': quiz['text'],
        'choices': quiz['choices'],
        'correct_choice_id': quiz['correct_choice_id'],
        'explanation': quiz['explanation'],
        'image': '',
        'created_at': now,
        'updated_at': now,
    })
    snapshot = ref.get()
    return _serialize(snapshot.id, snapshot.to_dict())


def list_by_author(author_uid):
    query = _col().where(filter=FieldFilter('author_uid', '==', author_uid))
    return [_serialize(doc.id, doc.to_dict()) for doc in query.stream()]


def _owned_ref(question_id, author_uid):
    """所有者が一致するユーザー問題の参照を返す。存在しない・他人の問題・公式問題ならNone。"""
    ref = _col().document(question_id)
    snapshot = ref.get()
    if not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    if data.get('source') != 'user' or data.get('author_uid') != author_uid:
        return None
    return ref


def update_question(question_id, author_uid, quiz):
    ref = _owned_ref(question_id, author_uid)
    if ref is None:
        return False
    ref.update({
        'text': quiz['text'],
        'choices': quiz['choices'],
        'correct_choice_id': quiz['correct_choice_id'],
        'explanation': quiz['explanation'],
        'updated_at': firestore.SERVER_TIMESTAMP,
    })
    return True


def delete_question(question_id, author_uid):
    ref = _owned_ref(question_id, author_uid)
    if ref is None:
        return False
    ref.delete()
    return True
