MAX_TEXT = 500
MAX_CHOICE = 200
MAX_EXPLANATION = 2000
CHOICE_COUNT = 4


def validate_quiz(data):
    """ユーザー投稿の四択クイズを検証し、(整形済みデータ, エラー一覧)を返す。"""
    errors = []
    if not isinstance(data, dict):
        return None, ['invalid payload']

    text = str(data.get('text', '')).strip()
    explanation = str(data.get('explanation', '')).strip()
    choices = data.get('choices')
    correct = data.get('correct_choice_id')

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
    if not isinstance(correct, int) or isinstance(correct, bool) or not 1 <= correct <= CHOICE_COUNT:
        errors.append('correct_choice_id must be 1-4')

    if errors:
        return None, errors
    return {
        'text': text,
        'explanation': explanation,
        'choices': [{'id': i + 1, 'text': t} for i, t in enumerate(cleaned)],
        'correct_choice_id': correct,
    }, []
