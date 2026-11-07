import os

from supabase import create_client

_client = None


def _db():
    global _client
    if _client is None:
        _client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])
    return _client


def create_quiz(author_uid, quiz):
    row = {
        'author_uid': author_uid,
        'text': quiz['text'],
        'explanation': quiz['explanation'],
        'category': quiz['category'],
        'choices': quiz['choices'],
        'correct_choice_id': quiz['correct_choice_id'],
    }
    return _db().table('user_quizzes').insert(row).execute().data[0]


def list_by_author(author_uid):
    return _db().table('user_quizzes').select('*').eq('author_uid', author_uid).execute().data


def update_quiz(quiz_id, author_uid, quiz):
    """author_uidが一致する行のみ更新する(所有者チェック)。"""
    return (_db().table('user_quizzes').update(quiz)
            .eq('id', quiz_id).eq('author_uid', author_uid).execute().data)


def delete_quiz(quiz_id, author_uid):
    return (_db().table('user_quizzes').delete()
            .eq('id', quiz_id).eq('author_uid', author_uid).execute().data)
