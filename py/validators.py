MAX_TITLE = 60
MAX_TAG = 20
MAX_TAGS = 5
MAX_TEXT = 500
MAX_CHOICE = 200
MAX_EXPLANATION = 2000
CHOICE_COUNT = 4
STATUSES = ('draft', 'published')


def validate_quiz(data):
    """ユーザー作成クイズを検証し、(整形済みデータ, エラー一覧)を返す。"""
    errors = []
    if not isinstance(data, dict):
        return None, ['invalid payload']

    title = str(data.get('title', '')).strip()
    text = str(data.get('text', '')).strip()
    explanation = str(data.get('explanation', '')).strip()
    choices = data.get('choices')
    correct = data.get('correct_choice_id')
    raw_tags = data.get('tags', [])
    status = data.get('status')

    if not title or len(title) > MAX_TITLE:
        errors.append(f'title must be 1-{MAX_TITLE} chars')
    if not text or len(text) > MAX_TEXT:
        errors.append(f'text must be 1-{MAX_TEXT} chars')
    if len(explanation) > MAX_EXPLANATION:
        errors.append(f'explanation must be <= {MAX_EXPLANATION} chars')
    if not isinstance(choices, list) or len(choices) != CHOICE_COUNT:
        errors.append(f'exactly {CHOICE_COUNT} choices required')
        choices = []
    cleaned = [str(c).strip() for c in choices]
    if any(not c or len(c) > MAX_CHOICE for c in cleaned):
        errors.append(f'each choice must be 1-{MAX_CHOICE} chars')
    is_int = isinstance(correct, int) and not isinstance(correct, bool)
    if not is_int or not 1 <= correct <= CHOICE_COUNT:
        errors.append('correct_choice_id must be 1-4')

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

    if errors:
        return None, errors
    return {
        'title': title,
        'tags': tags,
        'status': status,
        'text': text,
        'explanation': explanation,
        'choices': [{'id': i + 1, 'text': t} for i, t in enumerate(cleaned)],
        'correct_choice_id': correct,
    }, []
