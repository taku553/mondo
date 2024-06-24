# config.py
import os
from datetime import timedelta

#設定
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', default ='default_secret_key') #秘密鍵を環境変数"SECRET_KEY"に設定
    SESSION_TYPE = 'filesystem' # セッションタイプをファイルシステムに設定
    SESSION_FILE_DIR = os.path.join('/home/rhzcitfl/public_html/history_flow_quiz', 'sessions') # セッションファイルの保存先ディレクトリを指定
    SESSION_PERMANENT = False # セッションが永続的でないように設定
    PERMANENT_SESSION_LIFETIME = timedelta(days=1) # セッションの有効期限を1日に設定
    # print("SESSION_FILE_DIR:", SESSION_FILE_DIR)

class DevelopmentConfig(Config):
    DEBUG = True
    # SERVER_NAME = '127.0.0.1:5000'

class ProductionConfig(Config):
    DEBUG = False
    SERVER_NAME = os.environ.get('SERVER_NAME', 'ngrjaku.com') # ドメイン名を正確に設定
    APPLICATION_ROOT = '/'