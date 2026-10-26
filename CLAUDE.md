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
- `py/dataset.py`: クイズのデータセット定義
- `templates/`: HTMLテンプレート
- `static/`: CSS、JavaScript、画像などの静的ファイル

## Notes

- このプロジェクトはFlaskとRedisを使用しています
- セッション管理にRedisを使用しています
- フロントエンドはHTML/CSS/JavaScriptで実装されています