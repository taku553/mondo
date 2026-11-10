import base64
import binascii
import io

from PIL import Image, UnidentifiedImageError

MAX_TITLE = 60
MAX_TAG = 20
MAX_TAGS = 5
MAX_GENRE = 20
MAX_SUMMARY = 100
MAX_QUESTIONS = 20
MAX_TEXT = 500
MAX_CHOICE = 200
MAX_EXPLANATION = 2000
CHOICE_COUNT = 4
STATUSES = ('draft', 'published')
IMAGE_PREFIX = 'data:image/jpeg;base64,'
IMAGE_WIDTH = 800
IMAGE_HEIGHT = 450
MAX_IMAGE_BYTES = 100 * 1024


def validate_image(value):
    """JPEGのData URLを検証し、(base64文字列, エラー一覧)を返す。"""
    if not isinstance(value, str) or not value.startswith(IMAGE_PREFIX):
        return None, ['image must be a JPEG data URL']
    encoded = value[len(IMAGE_PREFIX):]
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return None, ['image is not valid base64']
    if len(raw) > MAX_IMAGE_BYTES:
        return None, [f'image must be <= {MAX_IMAGE_BYTES // 1024}KB']
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format != 'JPEG':
                return None, ['image must be JPEG']
            if image.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
                return None, [f'image must be {IMAGE_WIDTH}x{IMAGE_HEIGHT}px']
    except (UnidentifiedImageError, OSError):
        return None, ['image could not be read']
    return encoded, []


def _validate_question(raw, number, errors):
    """1問分を検証し、整形済みの問題を返す。エラーはerrorsに追加する。"""
    if not isinstance(raw, dict):
        errors.append(f'question {number}: invalid')
        return None
    text = str(raw.get('text', '')).strip()
    explanation = str(raw.get('explanation', '')).strip()
    choices = raw.get('choices')
    correct = raw.get('correct_choice_id')
    error_count = len(errors)

    if not text or len(text) > MAX_TEXT:
        errors.append(f'question {number}: text must be 1-{MAX_TEXT} chars')
    if len(explanation) > MAX_EXPLANATION:
        errors.append(f'question {number}: explanation must be <= {MAX_EXPLANATION} chars')
    if not isinstance(choices, list) or len(choices) != CHOICE_COUNT:
        errors.append(f'question {number}: exactly {CHOICE_COUNT} choices required')
        choices = []
    cleaned = [str(c).strip() for c in choices]
    if any(not c or len(c) > MAX_CHOICE for c in cleaned):
        errors.append(f'question {number}: each choice must be 1-{MAX_CHOICE} chars')
    is_int = isinstance(correct, int) and not isinstance(correct, bool)
    if not is_int or not 1 <= correct <= CHOICE_COUNT:
        errors.append(f'question {number}: correct_choice_id must be 1-{CHOICE_COUNT}')

    if len(errors) != error_count:
        return None
    return {
        'text': text,
        'choices': [{'id': i + 1, 'text': t} for i, t in enumerate(cleaned)],
        'correct_choice_id': correct,
        'explanation': explanation,
    }


def validate_quiz(data, require_image=True):
    """ユーザー作成クイズを検証し、(整形済みデータ, エラー一覧)を返す。

    require_image=True（新規作成）では画像必須。False（更新）では画像省略時に既存画像を残す。
    """
    errors = []
    if not isinstance(data, dict):
        return None, ['invalid payload']

    title = str(data.get('title', '')).strip()
    genre = str(data.get('genre', '')).strip()
    summary = str(data.get('summary', '')).strip()
    questions_raw = data.get('questions')
    raw_tags = data.get('tags', [])
    status = data.get('status')

    if not title or len(title) > MAX_TITLE:
        errors.append(f'title must be 1-{MAX_TITLE} chars')
    if not genre or len(genre) > MAX_GENRE:
        errors.append(f'genre must be 1-{MAX_GENRE} chars')
    if not summary or len(summary) > MAX_SUMMARY:
        errors.append(f'summary must be 1-{MAX_SUMMARY} chars')
    if not isinstance(questions_raw, list) or not 1 <= len(questions_raw) <= MAX_QUESTIONS:
        errors.append(f'questions must be a list of 1-{MAX_QUESTIONS} items')
        questions = []
    else:
        questions = [_validate_question(raw, i, errors) for i, raw in enumerate(questions_raw, 1)]

    tags = []
    if not isinstance(raw_tags, list):
        errors.append('tags must be a list')
    else:
        for raw in raw_tags:
            name = str(raw).strip()
            if name and name not in tags:
                tags.append(name)
    if len(tags) > MAX_TAGS or any(len(tag) > MAX_TAG for tag in tags):
        errors.append(f'tags must be <= {MAX_TAGS} items of <= {MAX_TAG} chars')

    if status not in STATUSES:
        errors.append('status must be draft or published')

    image = None
    image_value = data.get('image')
    if image_value or require_image:
        image, image_errors = validate_image(image_value)
        errors.extend(image_errors)

    if errors or any(question is None for question in questions):
        return None, errors
    return {
        'title': title,
        'genre': genre,
        'summary': summary,
        'tags': tags,
        'status': status,
        'image': image,
        'questions': questions,
    }, []
