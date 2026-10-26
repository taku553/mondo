# Vercelのサーバーレス関数のエントリーポイント
# vercel.jsonのrewritesで静的ファイル以外の全リクエストをここに集め、Flaskアプリに渡す
from py.main import app  # noqa: F401
