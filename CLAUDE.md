# Claude Instructions

This file contains instructions for Claude to better assist with this project.

## Project Overview

「Mondo（ながれじゃく）」は歴史クイズWebアプリケーションです。Python/Flaskで構築され、時代別（第一～第三千年紀）やチェスのオープニングなどのカテゴリ別に四択クイズを提供します。

## Development Workflows

### Running the application locally
```bash
sh start-app.sh
```

### Common Commands

- Code quality check:
```bash
python -m pylint py/*.py
```

## File Structure

- `py/main.py`: メインのFlaskアプリケーションコード
- `py/repositories/quiz_catalog.py`: Firestore から読み込むクイズ一覧・問題の取得
- `templates/`: HTMLテンプレート
- `public/static/`: CSS、JavaScript、画像などの静的ファイル（VercelのCDNから配信）
- `api/index.py`: Vercelのサーバーレス関数のエントリーポイント
- `vercel.json`: Vercelのデプロイ設定

## Deployment

- Vercelにデプロイ。セッションはUpstash Redis（環境変数 `REDIS_URL` または `KV_URL`）
- 本番の必須環境変数: `SECRET_KEY`, `REDIS_URL`（`APP_ENV` 未設定時はproductionとして動作）, `FIREBASE_CREDENTIALS`（サービスアカウントJSON）, `ADMIN_UIDS`（公式クイズの作成者UID、カンマ区切り）
- Firestore のデータ・ルールは Firebase プロジェクト `mondo-6f159` で管理。ルール反映は `firebase deploy --only firestore:rules --project mondo-6f159`

## Notes

- このプロジェクトはFlaskとRedisを使用しています
- セッション管理にRedisを使用しています
- フロントエンドはHTML/CSS/JavaScriptで実装されています