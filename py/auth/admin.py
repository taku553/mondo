import os


def get_admin_uids():
    """環境変数ADMIN_UIDS（カンマ区切りのFirebase UID）を返す。公式クイズの作成者として使う。"""
    return [uid.strip() for uid in os.environ.get('ADMIN_UIDS', '').split(',') if uid.strip()]


def is_admin(uid):
    return bool(uid) and uid in get_admin_uids()
