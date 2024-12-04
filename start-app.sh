#!/bin/zsh

# スクリプト名を取得
SCRIPT_NAME=$(basename "$0")

# 環境変数の設定
export FLASK_APP=py.main.py
export APP_ENV=development
export FLASK_DEBUG=1

# Redisサーバーが実行中かチェック
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis server..."
    redis-server &
    # Redisサーバーの起動を待つ
    sleep 2
else
    echo "Redis server is already running"
fi

# Flask アプリケーションを起動
echo "Starting Flask application..."
flask run

# スクリプト終了時にRedisサーバーを停止
cleanup() {
    echo "Stopping Redis server..."
    redis-cli shutdown
    exit 0
}

# SIGINT (Ctrl+C) と SIGTERM シグナルをトラップ
trap cleanup SIGINT SIGTERM

# 使用方法の関数
usage() {
    echo "Usage: ./$SCRIPT_NAME"
    echo "This script starts the Redis server and Flask application with development environment variables."
    exit 1
}

# -h または --help オプションが指定された場合、使用方法を表示
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    usage
fi