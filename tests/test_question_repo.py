import unittest
from unittest import mock

from flask import Flask

from py.repositories import question_repo
from py.routes import quiz_create

VALID = {'text': 'Q', 'explanation': '', 'choices': ['a', 'b', 'c', 'd'], 'correct_choice_id': 2}


class _Snapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return dict(self._data)

    def get(self, key):
        return self._data[key]


class QuestionRepoTest(unittest.TestCase):
    def setUp(self):
        self.collection = mock.MagicMock()
        patcher = mock.patch.object(question_repo, '_col', return_value=self.collection)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_stores_published_user_question(self):
        ref = self.collection.document.return_value
        ref.get.return_value = _Snapshot('abc', {'source': 'user', 'status': 'published'})
        result = question_repo.create_question('uid1', {**VALID, 'choices': []})
        saved = ref.set.call_args.args[0]
        self.assertEqual((saved['source'], saved['status'], saved['author_uid']), ('user', 'published', 'uid1'))
        self.assertIsNone(saved['quiz_id'])
        self.assertNotIn('category', saved)
        self.assertEqual(result['id'], 'abc')

    def test_update_and_delete_reject_other_owner(self):
        ref = self.collection.document.return_value
        ref.get.return_value = _Snapshot('abc', {'source': 'user', 'author_uid': 'owner'})
        self.assertFalse(question_repo.update_question('abc', 'other', VALID))
        self.assertFalse(question_repo.delete_question('abc', 'other'))
        ref.update.assert_not_called()
        ref.delete.assert_not_called()

    def test_update_and_delete_reject_official_question_even_for_owner_uid(self):
        ref = self.collection.document.return_value
        ref.get.return_value = _Snapshot('official-001', {'source': 'official', 'author_uid': 'admin'})
        self.assertFalse(question_repo.update_question('official-001', 'admin', VALID))
        self.assertFalse(question_repo.delete_question('official-001', 'admin'))
        ref.update.assert_not_called()
        ref.delete.assert_not_called()

    def test_update_and_delete_allow_owner(self):
        ref = self.collection.document.return_value
        ref.get.return_value = _Snapshot('abc', {'source': 'user', 'author_uid': 'owner'})
        self.assertTrue(question_repo.update_question('abc', 'owner', VALID))
        self.assertTrue(question_repo.delete_question('abc', 'owner'))
        ref.update.assert_called_once()
        ref.delete.assert_called_once()

    def test_missing_question_is_not_found(self):
        self.collection.document.return_value.get.return_value = _Snapshot('x', None)
        self.assertFalse(question_repo.delete_question('x', 'owner'))


class QuizCreateRoutesTest(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(quiz_create.bp)
        self.client = app.test_client()
        auth = mock.patch('py.auth.decorators.verify_id_token', return_value={'uid': 'owner'})
        auth.start()
        self.addCleanup(auth.stop)
        self.headers = {'Authorization': 'Bearer token'}

    def test_requires_login(self):
        self.assertEqual(self.client.get('/api/my_quizzes').status_code, 401)

    def test_string_id_is_routed_to_repo(self):
        with mock.patch.object(question_repo, 'delete_question', return_value=True) as delete:
            response = self.client.delete('/api/my_quizzes/abc123', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        delete.assert_called_once_with('abc123', 'owner')

    def test_invalid_payload_is_rejected_before_repo(self):
        with mock.patch.object(question_repo, 'create_question') as create:
            response = self.client.post('/api/my_quizzes', json={'text': ''}, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        create.assert_not_called()


if __name__ == '__main__':
    unittest.main()
