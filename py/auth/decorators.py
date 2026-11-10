from functools import wraps

from flask import g, jsonify, request

from py.auth.admin import is_admin
from py.auth.firebase import verify_id_token


def login_required(view):
    """Authorization: Bearer <IDトークン> を検証し、g.user_uid にuidを設定する。"""
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            return jsonify(error='login required'), 401
        try:
            claims = verify_id_token(header[len('Bearer '):])
        except Exception:
            return jsonify(error='invalid token'), 401
        g.user_uid = claims['uid']
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    """login_requiredの後に付け、ADMIN_UIDSに含まれるユーザーだけを通す。"""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_admin(g.user_uid):
            return jsonify(error='forbidden'), 403
        return view(*args, **kwargs)
    return wrapper
