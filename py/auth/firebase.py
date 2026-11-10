import json
import os

import firebase_admin
from firebase_admin import auth, credentials, firestore

_app = None
_db = None


def _get_app():
    """firebase_adminを初回のみ初期化する。鍵はJSON文字列の環境変数FIREBASE_CREDENTIALSで渡す。"""
    global _app
    if _app is None:
        raw = os.environ.get('FIREBASE_CREDENTIALS')
        if not raw:
            raise RuntimeError('FIREBASE_CREDENTIALS must be set')
        _app = firebase_admin.initialize_app(credentials.Certificate(json.loads(raw)))
    return _app


def get_firestore_client():
    """同じAdminアプリに紐づくFirestoreクライアントを返す。Admin SDKのためセキュリティルールは適用されない。"""
    global _db
    if _db is None:
        _db = firestore.client(app=_get_app())
    return _db


def verify_id_token(id_token):
    """FirebaseのIDトークンを検証し、デコード済みクレーム(uid等)を返す。無効なら例外。"""
    return auth.verify_id_token(id_token, app=_get_app())
