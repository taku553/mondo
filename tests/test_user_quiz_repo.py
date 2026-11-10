import unittest
import unittest.mock

from py.repositories import user_quiz_repo as repo


class NormalizeTagsTest(unittest.TestCase):
    def test_non_admin_cannot_keep_official_tag(self):
        self.assertEqual(repo.normalize_tags(['公式', '歴史'], admin=False), ['歴史'])

    def test_admin_quiz_gets_official_tag_first(self):
        self.assertEqual(repo.normalize_tags(['歴史'], admin=True), ['公式', '歴史'])
        self.assertEqual(repo.normalize_tags(['公式', '歴史'], admin=True), ['公式', '歴史'])


class _Snapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
        self.exists = data is not None
        self.reference = None

    def to_dict(self):
        return dict(self._data) if self._data is not None else None


class _Doc:
    def __init__(self, db, collection, doc_id):
        self.db, self.collection_name, self.id = db, collection, doc_id
        self.reference = self

    def get(self):
        return _Snapshot(self.id, self.db.store[self.collection_name].get(self.id))

    def update(self, data):
        self.db.store[self.collection_name][self.id].update(data)


class _Db:
    def __init__(self, store):
        self.store = store
        self.batches = []

    def collection(self, name):
        db = self
        class _Col:
            def document(self, doc_id=None):
                return _Doc(db, name, doc_id or f'auto-{name}')
        return _Col()

    def batch(self):
        db = self

        class _Batch:
            def __init__(self):
                self.ops = []

            def set(self, ref, data, merge=False):
                self.ops.append(('set', ref, data))

            def update(self, ref, data):
                self.ops.append(('update', ref, data))

            def delete(self, ref):
                self.ops.append(('delete', ref))

            def commit(self):
                db.batches.append(self.ops)
        return _Batch()


QUIZ = {'title': 'T', 'tags': ['歴史'], 'status': 'published', 'text': 'Q',
        'choices': [{'id': 1, 'text': 'a'}] * 4, 'correct_choice_id': 1, 'explanation': ''}


class OwnerGuardTest(unittest.TestCase):
    def setUp(self):
        self.db = _Db({
            'quizzes': {
                'q1': {'source': 'user', 'author_uid': 'owner', 'moderation': 'none'},
                'q2': {'source': 'user', 'author_uid': 'owner', 'moderation': 'hidden'},
                'off': {'source': 'official', 'author_uid': None, 'moderation': 'none'},
            },
            'questions': {},
        })
        self.patch = unittest.mock.patch.object(repo, '_db', return_value=self.db)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_other_users_cannot_update_or_delete(self):
        self.assertEqual(repo.update_quiz('q1', 'intruder', QUIZ, admin=True), repo.NOT_FOUND)
        self.assertFalse(repo.delete_quiz('q1', 'intruder'))
        self.assertEqual(self.db.batches, [])

    def test_official_quiz_is_never_editable_by_owner_path(self):
        self.assertEqual(repo.update_quiz('off', 'owner', QUIZ, admin=True), repo.NOT_FOUND)
        self.assertFalse(repo.delete_quiz('off', None))

    def test_owner_cannot_update_moderated_quiz(self):
        self.assertEqual(repo.update_quiz('q2', 'owner', QUIZ, admin=False), repo.MODERATED)
        self.assertEqual(self.db.batches, [])

    def test_owner_update_writes_quiz_and_question(self):
        self.assertEqual(repo.update_quiz('q1', 'owner', QUIZ, admin=False), repo.UPDATED)
        self.assertEqual(len(self.db.batches[-1]), 2)

    def test_set_moderation_only_touches_user_quizzes(self):
        self.assertFalse(repo.set_moderation('off', 'hidden'))
        self.assertTrue(repo.set_moderation('q1', 'hidden'))


if __name__ == '__main__':
    unittest.main()
