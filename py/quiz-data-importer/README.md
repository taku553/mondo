# quiz-data-importer

このプロジェクトは、マークダウン形式のクイズデータを読み込み、データベースに追加するためのツールです。以下の機能を提供します。

## 機能

- **マークダウンファイルの読み込みと解析**: `src/importer.py`を使用して、指定されたマークダウンファイルからメタデータと質問データを抽出します。
- **データの追加**: `src/dataset_updater.py`を使用して、抽出したデータを`dataset.py`に追加します。
- **ユーティリティ**: データの解析や検証を行うためのユーティリティが含まれています。

## ディレクトリ構造

```
/Users/takahashitakuya/Desktop/history_flow_quiz/py/quiz-data-importer
├── main.py
├── README.md
├── sample_quiz.md
├── src
│   ├── dataset_updater.py
│   ├── importer.py
│   └── utils
│       ├── __init__.py
│       ├── markdown_parser.py
│       └── validators.py
└── tests
    ├── __init__.py
    ├── test_data
    │   └── sample_quiz.md  # テスト用サンプルデータ
    ├── test_dataset_updater.py
    └── test_importer.py

6 directories, 11 files
```

## 使用方法

1. 必要なパッケージをインストールします。
   ```
   pip install -r requirements.txt
   ```

2. `main.py`を実行して、マークダウンファイルを指定します。
   ```
   python main.py <path_to_markdown_file>
   ```

3. データが`dataset.py`に追加されます。

## テスト

テストは`tests`ディレクトリ内に含まれています。ユニットテストを実行するには、以下のコマンドを使用します。

```
pytest tests/
```

## ライセンス

このプロジェクトはMITライセンスの下で提供されています。