"""ユーザー作成クイズのFirestore保存。

1クイズにつき quizzes/{id}（紹介情報）と questions/{id}（問題文）を同じIDで対にして保存する。
Admin SDK経由のアクセスのため、クライアント側のセキュリティルールは適用されない。
所有者・管理者の判定はこのモジュールとルート側で行う。
"""
from datetime import datetime, timedelta, timezone

from firebase_admin import firestore
from google.cloud.firestore import FieldFilter

from py.auth.firebase import get_firestore_client

QUIZZES = 'quizzes'
QUESTIONS = 'questions'
OFFICIAL_TAG = '公式'
MODERATION_NONE = 'none'
MODERATION_HIDDEN = 'hidden'
JST = timezone(timedelta(hours=9))

# 所有者・管理者の更新結果
UPDATED = 'updated'
NOT_FOUND = 'not_found'
MODERATED = 'moderated'


def _db():
    return get_firestore_client()


def normalize_tags(tags, admin):
    """公式タグは管理者だけが付けられる。管理者が作るクイズには自動で付与する。"""
    tags = [tag for tag in tags if tag != OFFICIAL_TAG]
    return [OFFICIAL_TAG, *tags] if admin else tags


def _iso(value):
    return value.isoformat() if hasattr(value, 'isoformat') else value


def _serialize(quiz_id, quiz, question):
    return {
        'id': quiz_id,
        'title': quiz.get('title', ''),
        'tags': quiz.get('tags', []),
        'status': quiz.get('status'),
        'author_uid': quiz.get('author_uid'),
        'moderation': quiz.get('moderation', MODERATION_NONE),
        'date': quiz.get('date', ''),
        'created_at': _iso(quiz.get('created_at')),
        'updated_at': _iso(quiz.get('updated_at')),
        'text': question.get('text', ''),
        'choices': question.get('choices', []),
        'correct_choice_id': question.get('correct_choice_id'),
        'explanation': question.get('explanation', ''),
    }


def _with_questions(db, quiz_snapshots):
    snapshots = list(quiz_snapshots)
    if not snapshots:
        return []
    question_refs = [db.collection(QUESTIONS).document(snapshot.id) for snapshot in snapshots]
    questions = {snapshot.id: snapshot.to_dict() or {} for snapshot in db.get_all(question_refs)}
    return [
        _serialize(snapshot.id, snapshot.to_dict() or {}, questions.get(snapshot.id, {}))
        for snapshot in snapshots
    ]


def create_quiz(author_uid, quiz, admin):
    db = _db()
    quiz_ref = db.collection(QUIZZES).document()
    question_ref = db.collection(QUESTIONS).document(quiz_ref.id)
    now = firestore.SERVER_TIMESTAMP
    today = datetime.now(JST).strftime('%Y/%m/%d')
    batch = db.batch()
    batch.set(quiz_ref, {
        'title': quiz['title'],
        'image': '',
        'tags': normalize_tags(quiz['tags'], admin),
        'date': today,
        'status': quiz['status'],
        'source': 'user',
        'author_uid': author_uid,
        'moderation': MODERATION_NONE,
        'created_at': now,
        'updated_at': now,
    })
    batch.set(question_ref, {
        'quiz_id': quiz_ref.id,
        'source': 'user',
        'author_uid': author_uid,
        'status': quiz['status'],
        'text': quiz['text'],
        'choices': quiz['choices'],
        'correct_choice_id': quiz['correct_choice_id'],
        'explanation': quiz['explanation'],
        'image': '',
        'created_at': now,
        'updated_at': now,
    })
    batch.commit()
    return quiz_ref.id


def list_by_author(author_uid):
    db = _db()
    query = db.collection(QUIZZES).where(filter=FieldFilter('author_uid', '==', author_uid))
    return _with_questions(db, query.stream())


def list_all_user_quizzes():
    """管理画面用。ユーザー作成クイズを全件返す（公式クイズは含めない）。"""
    db = _db()
    query = db.collection(QUIZZES).where(filter=FieldFilter('source', '==', 'user'))
    return _with_questions(db, query.stream())


def _owned_quiz(db, quiz_id, author_uid):
    """所有者が一致するユーザー作成クイズのスナップショットを返す。該当しなければNone。"""
    snapshot = db.collection(QUIZZES).document(quiz_id).get()
    if not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    if data.get('source') != 'user' or data.get('author_uid') != author_uid:
        return None
    return snapshot


def update_quiz(quiz_id, author_uid, quiz, admin):
    db = _db()
    snapshot = _owned_quiz(db, quiz_id, author_uid)
    if snapshot is None:
        return NOT_FOUND
    if snapshot.to_dict().get('moderation') == MODERATION_HIDDEN:
        return MODERATED
    now = firestore.SERVER_TIMESTAMP
    batch = db.batch()
    batch.update(snapshot.reference, {
        'title': quiz['title'],
        'tags': normalize_tags(quiz['tags'], admin),
        'status': quiz['status'],
        'updated_at': now,
    })
    # 問題側はクイズ側と公開状態を揃える（出題はpublishedの問題だけを使うため）
    batch.set(db.collection(QUESTIONS).document(quiz_id), {
        'status': quiz['status'],
        'text': quiz['text'],
        'choices': quiz['choices'],
        'correct_choice_id': quiz['correct_choice_id'],
        'explanation': quiz['explanation'],
        'updated_at': now,
    }, merge=True)
    batch.commit()
    return UPDATED


def delete_quiz(quiz_id, author_uid):
    db = _db()
    snapshot = _owned_quiz(db, quiz_id, author_uid)
    if snapshot is None:
        return False
    batch = db.batch()
    batch.delete(snapshot.reference)
    batch.delete(db.collection(QUESTIONS).document(quiz_id))
    batch.commit()
    return True


def set_moderation(quiz_id, moderation):
    """運営の判定。hiddenにすると公開一覧から外れ、作成者も公開に戻せなくなる。"""
    db = _db()
    ref = db.collection(QUIZZES).document(quiz_id)
    snapshot = ref.get()
    if not snapshot.exists or (snapshot.to_dict() or {}).get('source') != 'user':
        return False
    ref.update({'moderation': moderation, 'updated_at': firestore.SERVER_TIMESTAMP})
    return True
