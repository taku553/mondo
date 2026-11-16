"""ユーザー作成クイズのFirestore保存。

1クイズは quizzes/{id}（紹介情報）、questions/{id}-{n}（問題、n=1〜20の順番）、
quiz_images/{id}（画像のbase64）に分けて保存する。旧形式（問題IDがクイズIDと同じ）も読み取れる。
Admin SDK経由のアクセスのため、クライアント側のセキュリティルールは適用されない。
所有者・管理者の判定はこのモジュールとルート側で行う。
"""
from datetime import datetime, timedelta, timezone

from firebase_admin import firestore
from google.cloud.firestore import FieldFilter

from py.auth.firebase import get_firestore_client

QUIZZES = 'quizzes'
QUESTIONS = 'questions'
QUIZ_IMAGES = 'quiz_images'
QUESTION_IMAGES = 'question_images'
IMAGE_URL_PREFIX = '/api/quiz_images/'
QUESTION_IMAGE_URL_PREFIX = '/api/question_images/'
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


def _image_url(quiz_id):
    return f'{IMAGE_URL_PREFIX}{quiz_id}'


def _question_image_url(image_id):
    return f'{QUESTION_IMAGE_URL_PREFIX}{image_id}'


def _question_image_id(url):
    return url[len(QUESTION_IMAGE_URL_PREFIX):]


def _question_ref(db, quiz_id, number):
    return db.collection(QUESTIONS).document(f'{quiz_id}-{number}')


def _stage_question_images(db, batch, quiz_id, questions, saved_urls, now):
    """問題ごとの画像URLを決め、新しい画像をbatchに追加する。

    saved_urls は保存済みの問題画像URL。ここに含まれるURLだけをそのまま残し、それ以外は画像なしとする。
    """
    urls = []
    for question in questions:
        if question.get('image_data'):
            image_ref = db.collection(QUESTION_IMAGES).document()
            batch.set(image_ref, {'data': question['image_data'], 'quiz_id': quiz_id, 'created_at': now})
            urls.append(_question_image_url(image_ref.id))
        elif question.get('image_url') in saved_urls:
            urls.append(question['image_url'])
        else:
            urls.append('')
    return urls


def _question_fields(quiz_id, number, question, author_uid, status, now, image_url):
    return {
        'quiz_id': quiz_id,
        'order': number,
        'source': 'user',
        'author_uid': author_uid,
        'status': status,
        'text': question['text'],
        'choices': question['choices'],
        'correct_choice_id': question['correct_choice_id'],
        'explanation': question['explanation'],
        'image': image_url,
        'created_at': now,
        'updated_at': now,
    }


def _serialize(quiz_id, quiz, questions):
    return {
        'id': quiz_id,
        'title': quiz.get('title', ''),
        'genre': quiz.get('genre', ''),
        'summary': quiz.get('summary', ''),
        'image': quiz.get('image', ''),
        'tags': quiz.get('tags', []),
        'status': quiz.get('status'),
        'author_uid': quiz.get('author_uid'),
        'moderation': quiz.get('moderation', MODERATION_NONE),
        'date': quiz.get('date', ''),
        'created_at': _iso(quiz.get('created_at')),
        'updated_at': _iso(quiz.get('updated_at')),
        'questions': [
            {
                'id': question['id'],
                'text': question.get('text', ''),
                'choices': question.get('choices', []),
                'correct_choice_id': question.get('correct_choice_id'),
                'explanation': question.get('explanation', ''),
                'image': question.get('image', ''),
            }
            for question in questions
        ],
    }


def _group_questions(snapshots):
    """問題をquiz_id別にまとめ、順番どおりに並べる。order がない旧データは1問目扱い。"""
    grouped = {}
    for snapshot in snapshots:
        data = snapshot.to_dict() or {}
        grouped.setdefault(data.get('quiz_id'), []).append({**data, 'id': snapshot.id})
    for questions in grouped.values():
        questions.sort(key=lambda question: (question.get('order', 1), question['id']))
    return grouped


def _with_questions(quiz_snapshots, grouped_questions):
    return [
        _serialize(snapshot.id, snapshot.to_dict() or {}, grouped_questions.get(snapshot.id, []))
        for snapshot in quiz_snapshots
    ]


def _questions_of(db, quiz_id):
    query = db.collection(QUESTIONS).where(filter=FieldFilter('quiz_id', '==', quiz_id))
    return list(query.stream())


def create_quiz(author_uid, quiz, admin):
    db = _db()
    quiz_ref = db.collection(QUIZZES).document()
    now = firestore.SERVER_TIMESTAMP
    today = datetime.now(JST).strftime('%Y/%m/%d')
    batch = db.batch()
    batch.set(quiz_ref, {
        'title': quiz['title'],
        'genre': quiz['genre'],
        'summary': quiz['summary'],
        'image': _image_url(quiz_ref.id),
        'tags': normalize_tags(quiz['tags'], admin),
        'date': today,
        'status': quiz['status'],
        'source': 'user',
        'author_uid': author_uid,
        'moderation': MODERATION_NONE,
        'created_at': now,
        'updated_at': now,
    })
    batch.set(db.collection(QUIZ_IMAGES).document(quiz_ref.id), {'data': quiz['image'], 'created_at': now})
    image_urls = _stage_question_images(db, batch, quiz_ref.id, quiz['questions'], set(), now)
    for number, (question, image_url) in enumerate(zip(quiz['questions'], image_urls), 1):
        batch.set(_question_ref(db, quiz_ref.id, number),
                  _question_fields(quiz_ref.id, number, question, author_uid, quiz['status'], now, image_url))
    batch.commit()
    return quiz_ref.id


def list_by_author(author_uid):
    db = _db()
    quizzes = db.collection(QUIZZES).where(filter=FieldFilter('author_uid', '==', author_uid)).stream()
    questions = db.collection(QUESTIONS).where(filter=FieldFilter('author_uid', '==', author_uid)).stream()
    return _with_questions(quizzes, _group_questions(questions))


def list_all_user_quizzes():
    """管理画面用。ユーザー作成クイズを全件返す（公式クイズは含めない）。"""
    db = _db()
    quizzes = db.collection(QUIZZES).where(filter=FieldFilter('source', '==', 'user')).stream()
    questions = db.collection(QUESTIONS).where(filter=FieldFilter('source', '==', 'user')).stream()
    return _with_questions(quizzes, _group_questions(questions))


def _is_public_user_quiz(db, quiz_id):
    """公開中・非表示でないユーザー作成クイズかどうか。"""
    if not quiz_id:
        return False
    snapshot = db.collection(QUIZZES).document(quiz_id).get()
    if not snapshot.exists:
        return False
    data = snapshot.to_dict() or {}
    return (data.get('source') == 'user' and data.get('status') == 'published'
            and data.get('moderation') != MODERATION_HIDDEN)


def get_public_image(quiz_id):
    """公開中・非表示でないユーザー作成クイズの画像（base64）を返す。該当しなければNone。"""
    db = _db()
    if not _is_public_user_quiz(db, quiz_id):
        return None
    image = db.collection(QUIZ_IMAGES).document(quiz_id).get()
    return (image.to_dict() or {}).get('data') if image.exists else None


def get_public_question_image(image_id):
    """公開中のユーザー作成クイズに含まれる問題画像（base64）を返す。該当しなければNone。"""
    db = _db()
    snapshot = db.collection(QUESTION_IMAGES).document(image_id).get()
    if not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    return data.get('data') if _is_public_user_quiz(db, data.get('quiz_id')) else None


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
    quiz_fields = {
        'title': quiz['title'],
        'genre': quiz['genre'],
        'summary': quiz['summary'],
        'tags': normalize_tags(quiz['tags'], admin),
        'status': quiz['status'],
        'updated_at': now,
    }
    batch = db.batch()
    if quiz['image']:
        quiz_fields['image'] = _image_url(quiz_id)
        batch.set(db.collection(QUIZ_IMAGES).document(quiz_id), {'data': quiz['image'], 'created_at': now})
    batch.update(snapshot.reference, quiz_fields)

    # 問題は作り直す。旧形式のID（クイズIDと同じ）も含め、新しいIDに無い古い問題を削除する
    old_questions = list(_questions_of(db, quiz_id))
    saved_urls = {(old.to_dict() or {}).get('image') for old in old_questions} - {'', None}
    image_urls = _stage_question_images(db, batch, quiz_id, quiz['questions'], saved_urls, now)
    for url in saved_urls - set(image_urls):
        batch.delete(db.collection(QUESTION_IMAGES).document(_question_image_id(url)))
    new_ids = {f'{quiz_id}-{number}' for number in range(1, len(quiz['questions']) + 1)}
    for old in old_questions:
        if old.id not in new_ids:
            batch.delete(old.reference)
    for number, (question, image_url) in enumerate(zip(quiz['questions'], image_urls), 1):
        batch.set(_question_ref(db, quiz_id, number),
                  _question_fields(quiz_id, number, question, author_uid, quiz['status'], now, image_url))
    batch.commit()
    return UPDATED


def delete_quiz(quiz_id, author_uid):
    db = _db()
    snapshot = _owned_quiz(db, quiz_id, author_uid)
    if snapshot is None:
        return False
    batch = db.batch()
    batch.delete(snapshot.reference)
    batch.delete(db.collection(QUIZ_IMAGES).document(quiz_id))
    for question in _questions_of(db, quiz_id):
        batch.delete(question.reference)
        url = (question.to_dict() or {}).get('image')
        if url:
            batch.delete(db.collection(QUESTION_IMAGES).document(_question_image_id(url)))
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
