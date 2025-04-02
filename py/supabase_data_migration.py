import os
import sys
from supabase import create_client
from py.dataset import questions, quiz_metadata
from dotenv import load_dotenv
import logging
import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)

# 外部キー制約のチェック関数
def check_foreign_keys(questions_data, choices_data):
    """テーブル間の関係が正しく設定されているか確認"""
    try:
        question_ids = {q["id"] for q in questions_data}
        for choice in choices_data:
            if choice["question_id"] not in question_ids:
                raise ValueError(
                    f"Question ID {choice['question_id']} not found for choice {choice['id']}"
                )
        logging.info("Foreign key checks passed successfully")
    except Exception as e:
        logging.error(f"Foreign key check failed: {str(e)}")
        raise


def verify_data_consistency():
    """データセットの基本的な整合性をチェックし、概要を出力する"""
    try:
        logging.info("Verifying data consistency...")
        
        # データセットの基本チェック
        total_questions = len(questions)
        unique_categories = set(q['category'] for q in questions if q['category'])
        choice_counts = {q['id']: len(q['choices']) for q in questions}
        
        # 結果をログに出力
        logging.info(f"Total questions: {total_questions}")
        logging.info(f"Unique categories: {unique_categories}")
        logging.info(f"Choice counts per question: {choice_counts}")
        
        return True
    except Exception as e:
        logging.error(f"Data consistency verification failed: {str(e)}")
        raise

# データの整合性チェックの追加: 各questionのIDがユニークであることを確認
def validate_data():
    """データの整合性を検証する拡張版の関数"""
    try:
        # 各questionのIDがユニークであることを確認
        question_ids = set()
        for q in questions:
            # ID値の型チェックを追加
            if not isinstance(q["id"], int):
                raise ValueError(f"Question ID must be integer, found {type(q['id'])} for question {q['id']}")
            
            # ID重複チェック（既存）
            if q["id"] in question_ids:
                raise ValueError(f"Duplicate question ID found: {q['id']}")
            question_ids.add(q["id"])
            
            # 必須フィールドの存在チェックを追加
            required_fields = ["text", "choices", "correct_choice_id", "explanation"]
            for field in required_fields:
                if field not in q or not q[field]:
                    raise ValueError(f"Required field '{field}' missing or empty in question {q['id']}")
            
            # correct_choice_idの有効性確認（既存）
            choice_ids = {c["id"] for c in q["choices"]}
            if q["correct_choice_id"] not in choice_ids:
                raise ValueError(f"Invalid correct_choice_id for question {q['id']}")
            
            # 選択肢の数が適切か確認
            if len(q["choices"]) < 2:
                raise ValueError(f"Question {q['id']} has fewer than 2 choices")
                
        logging.info("Data validation completed successfully")
        return True

    except Exception as e:
        logging.error(f"Data validation failed: {str(e)}")
        raise
        
def batch_insert(table_name, data, batch_size=100):
    """データを指定されたバッチサイズで分割して挿入する"""
    try:
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            logging.info(f"Inserting batch {i//batch_size + 1} into {table_name} table...")
            result = supabase.table(table_name).insert(batch).execute()
            logging.info(f"Successfully inserted batch {i//batch_size + 1} ({len(batch)} records)")

            # resultを参照する処理を追加
            logging.debug(f"Insert result: {result}") 
                       
        return True
    except Exception as e:
        logging.error(f"Error inserting batch into {table_name}: {str(e)}")
        raise

def update_sequences():
    """シーケンスを現在の最大IDに更新"""
    try:
        # choicesテーブルのシーケンスを更新
        max_choice_id_result = supabase.rpc(
            'get_max_id',
            {'table_name': 'choices'}
        ).execute()
        
        if max_choice_id_result.data:
            max_choice_id = max_choice_id_result.data + 1
            supabase.rpc(
                'set_sequence_value',
                {'sequence_name': 'choices_id_seq', 'value': max_choice_id}
            ).execute()
            
        logging.info("Sequences updated successfully")
    except Exception as e:
        logging.error(f"Error updating sequences: {str(e)}")
        raise

def migrate_data(dry_run=False):
    """
    dry_run=True の場合は検証のみを行い、実際のデータ挿入は行わない
    """    
    
# データの移行処理
    try:
        # データの検証
        logging.info("Starting data verification...")
        verify_data_consistency()        

        logging.info("Validating data...")        
        validate_data()
        
        # トランザクション的な処理のために配列にデータを格納
        questions_data = []
        choices_data = []
        choice_id_counter = 1  # 選択肢用の連番カウンター
        

        for q in questions:
            question_data = {
                "id": q["id"],
                "text": q["text"],
                "image": q["image"] if q["image"] and q["image"] != "" else None,
                "correct_choice_id": q["correct_choice_id"],
                "explanation": q["explanation"],
                "category": q["category"] if q["category"] != "" else None
            }
            questions_data.append(question_data)
            
            # 選択肢の処理
            for choice in q["choices"]:
                choice_data = {
                    "id": choice_id_counter,
                    "question_id": q["id"],
                    "text": choice["text"]
                }
                
                # correct_choice_idの更新
                if q["correct_choice_id"] == choice["id"]:
                    question_data["correct_choice_id"] = choice_id_counter
                
                choices_data.append(choice_data)
                choice_id_counter += 1
                                    
        # 外部キー制約のチェック
        check_foreign_keys(questions_data, choices_data)

        # 移行前の最終確認
        logging.info(f"準備完了: {len(questions_data)}件の質問と{len(choices_data)}件の選択肢を移行します")
        if not dry_run:
            user_input = input("移行を開始しますか？ (y/n): ")
            if user_input.lower() != 'y':
                logging.info("移行がキャンセルされました")
                return
            
        # データ削除処理を最初に配置
        if not dry_run:
            logging.info("Checking existing data...")
            questions_exists = supabase.table("questions").select("*").execute()
            choices_exists = supabase.table("choices").select("*").execute()
            
            if len(questions_exists.data) > 0 or len(choices_exists.data) > 0:
                logging.warning("Tables contain existing data")
                user_input = input("Do you want to clear existing data? (y/n): ")
                if user_input.lower() == 'y':
                    logging.info("Clearing existing data...")
                    # 外部キー制約があるため、choicesを先に削除
                    supabase.table("choices").delete().neq('id', 0).execute()
                    supabase.table("questions").delete().neq('id', 0).execute()
                    logging.info("Existing data cleared")
                else:
                    logging.info("Migration cancelled by user")
                    return
                
        # トランザクション的な処理
        logging.info("Checking existing data...")
        data = supabase.table("questions").select("*").execute()
        if len(data.data) > 0:
            logging.warning("Questions table is not empty")
            user_input = input("Do you want to proceed? (y/n): ")
            if user_input.lower() != 'y':
                logging.info("Migration cancelled by user")
                return
            
        if dry_run:
            logging.info("Dry run completed successfully. No data was inserted.")
            return True        

        # バッチ処理によるデータ挿入
        logging.info("Starting questions insertion...")
        if batch_insert("questions", questions_data, batch_size=50):
            logging.info(f"Successfully inserted all questions ({len(questions_data)} records)")

        logging.info("Starting choices insertion...")
        if batch_insert("choices", choices_data, batch_size=100):
            logging.info(f"Successfully inserted all choices ({len(choices_data)} records)")

        logging.info("Data migration completed successfully!")
        
    except ValueError as ve:
        logging.error(f"Data validation failed: {str(ve)}")
        raise
    except Exception as e:
        logging.error(f"Error during migration: {str(e)}")
        raise
    
def migrate_incremental_data(dry_run=False):
    """既存のデータを保持したまま、新しいデータのみを追加する"""
    try:
        # 既存のデータのIDを取得
        existing_question_ids = set()
        existing_questions = supabase.table("questions").select("id").execute()
        for q in existing_questions.data:
            existing_question_ids.add(q['id'])

        # 新しいデータのみをフィルタリング
        new_questions_data = []
        new_choices_data = []
        
        # 最後の選択肢IDを取得して、そこから連番を継続
        last_choice = supabase.table("choices").select("id").order("id.desc").limit(1).execute()
        choice_id_counter = last_choice.data[0]['id'] + 1 if last_choice.data else 1

        # 新しい質問のみを処理
        for q in questions:
            if q['id'] not in existing_question_ids:
                question_data = {
                    "id": q["id"],
                    "text": q["text"],
                    "image": q["image"] if q["image"] and q["image"] != "" else None,
                    "correct_choice_id": None,  # 後で更新
                    "explanation": q["explanation"],
                    "category": q["category"] if q["category"] != "" else None
                }
                new_questions_data.append(question_data)

                # 選択肢の処理
                for choice in q["choices"]:
                    choice_data = {
                        "id": choice_id_counter,
                        "question_id": q["id"],
                        "text": choice["text"]
                    }
                    
                    # correct_choice_idの更新
                    if q["correct_choice_id"] == choice["id"]:
                        question_data["correct_choice_id"] = choice_id_counter
                    
                    new_choices_data.append(choice_data)
                    choice_id_counter += 1

        if not new_questions_data:
            logging.info("新しい質問データはありません")
            return

        if dry_run:
            logging.info(f"追加予定: 質問 {len(new_questions_data)}件、選択肢 {len(new_choices_data)}件")
            return

        # データの挿入
        if new_questions_data:
            logging.info("新しい質問を追加中...")
            batch_insert("questions", new_questions_data, batch_size=50)

        if new_choices_data:
            logging.info("新しい選択肢を追加中...")
            batch_insert("choices", new_choices_data, batch_size=100)

        logging.info("増分更新が完了しました")

    except Exception as e:
        logging.error(f"増分更新中にエラーが発生: {str(e)}")
        raise

# quiz_metadataテーブルの移行スクリプト
def migrate_quiz_metadata(dry_run=False):
    """
    quiz_metadata辞書リストをsupabaseのquiz_metadataテーブルに移行する
    dry_run=True の場合は検証のみを行い、実際のデータ挿入は行わない
    """
    try:
        from py.dataset import quiz_metadata
        
        # 日付形式をISO形式の文字列に変換（JSONシリアル化可能な形式）
        processed_metadata = []
        for meta in quiz_metadata:
            meta_copy = meta.copy()  # 元のデータを変更しないようにコピー
            if 'date' in meta and meta['date']:
                # YYYY/MM/DD形式を日付オブジェクトに変換
                try:
                    date_parts = meta['date'].split('/')
                    # datetime.dateオブジェクトではなく、ISO形式の文字列に変換
                    meta_copy['date'] = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
                except Exception as e:
                    logging.warning(f"日付形式の変換に失敗: {meta['date']}, エラー: {str(e)}")        
            processed_metadata.append(meta_copy)

        # データの検証
        # データ挿入時にはprocessed_metadataを使用
        logging.info("クイズメタデータの検証を開始...")
        
        if not processed_metadata:
            logging.warning("quiz_metadataが空です")
            return False
            
        # メタデータの基本的な整合性チェック
        required_fields = ["id", "title", "category"]
        for meta in processed_metadata:
            for field in required_fields:
                if field not in meta or not meta[field]:
                    raise ValueError(f"必須フィールド '{field}' がメタデータ {meta.get('id', '不明')} に存在しないか空です")
            
            # IDが整数であることを確認
            if not isinstance(meta["id"], int):
                raise ValueError(f"メタデータID '{meta['id']}' は整数である必要があります")
                
            # tagsが配列であることを確認
            if "tags" in meta and not isinstance(meta["tags"], list):
                raise ValueError(f"メタデータ {meta['id']} のtags属性はリスト形式である必要があります")
        
        # IDの重複チェック
        meta_ids = set()
        for meta in processed_metadata:
            if meta["id"] in meta_ids:
                raise ValueError(f"重複するメタデータID '{meta['id']}' が見つかりました")
            meta_ids.add(meta["id"])
            
        logging.info(f"検証完了: {len(processed_metadata)}件のクイズメタデータを移行します")
        
        # ドライラン確認
        if dry_run:
            logging.info("ドライラン完了。データは挿入されていません。")
            return True
            
        # 既存データ確認
        data = supabase.table("quiz_metadata").select("*").execute()
        if len(data.data) > 0:
            logging.warning("quiz_metadataテーブルは空ではありません")
            user_input = input("既存のデータをクリアしますか？ (y/n): ")
            if user_input.lower() == 'y':
                logging.info("既存のメタデータをクリア中...")
                supabase.table("quiz_metadata").delete().neq('id', 0).execute()
                logging.info("既存のメタデータがクリアされました")
            else:
                user_input = input("それでも続行しますか？ (y/n): ")
                if user_input.lower() != 'y':
                    logging.info("移行がキャンセルされました")
                    return False
        
        # データ挿入
        logging.info("クイズメタデータの挿入を開始...")
        result = batch_insert("quiz_metadata", processed_metadata, batch_size=50)
        
        if result:
            logging.info(f"メタデータの移行完了: {len(processed_metadata)}件追加されました")
            return True
            
    except Exception as e:
        logging.error(f"クイズメタデータの移行中にエラーが発生: {str(e)}")
        raise
        
    return False

def migrate_incremental_quiz_metadata(dry_run=False):
    """
    既存のメタデータを保持したまま、新しいメタデータのみを追加する
    """
    try:
        from py.dataset import quiz_metadata
        
        # 既存のメタデータIDを取得
        existing_meta_ids = set()
        existing_meta = supabase.table("quiz_metadata").select("id").execute()
        for m in existing_meta.data:
            existing_meta_ids.add(m['id'])
            
        # 新しいメタデータのみをフィルタリング
        new_metadata_original = [meta for meta in quiz_metadata if meta['id'] not in existing_meta_ids]
        
        # 日付形式をISO形式の文字列に変換
        new_metadata = []
        for meta in new_metadata_original:
            meta_copy = meta.copy()
            if 'date' in meta_copy and meta_copy['date']:
                try:
                    date_parts = meta_copy['date'].split('/')
                    meta_copy['date'] = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
                except Exception as e:
                    logging.warning(f"日付形式の変換に失敗: {meta_copy['date']}, エラー: {str(e)}")
            new_metadata.append(meta_copy)        
        
        if not new_metadata:
            logging.info("新しいクイズメタデータはありません")
            return True
            
        if dry_run:
            logging.info(f"追加予定: メタデータ {len(new_metadata)}件")
            return True
            
        # 新メタデータの挿入
        logging.info("新しいメタデータを追加中...")
        result = batch_insert("quiz_metadata", new_metadata, batch_size=50)
        
        if result:
            logging.info(f"メタデータの増分更新完了: {len(new_metadata)}件追加されました")
            return True
            
    except Exception as e:
        logging.error(f"メタデータの増分更新中にエラーが発生: {str(e)}")
        raise
        
    return False
    
def main():
    try:
        # .envファイルから環境変数を読み込み
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        load_dotenv(dotenv_path=env_path)
        
        # Supabase接続情報を環境変数から取得
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # SERVICE_ROLE_KEY に変更      
        
        if not url or not key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        global supabase
        try:
            supabase = create_client(url, key)
            # 接続テストを追加
            test_response = supabase.table("questions").select("count").limit(1).execute()
            logging.info("Successfully connected to Supabase")
            if test_response.data is None:
                raise ConnectionError("Failed to get response from Supabase")
            logging.info(f"Successfully connected to Supabase. Test response: {test_response.data}")            
        except Exception as e:
            logging.error(f"Failed to connect to Supabase: {str(e)}")
            sys.exit(1)
        
        # データタイプと更新モードの選択
        data_type = input("移行するデータを選択してください（1: 問題データ, 2: メタデータ, 3: 両方）: ")
        update_mode = input("更新モードを選択してください（1: 全データ再構築, 2: 増分更新）: ")
        
        # 問題データの移行
        if data_type == "1" or data_type == "3":
            if update_mode == "1":
                migrate_data()
            elif update_mode == "2":
                migrate_incremental_data()
            else:
                logging.error("無効な選択です")
                return
                
        # メタデータの移行
        if data_type == "2" or data_type == "3":
            if update_mode == "1":
                migrate_quiz_metadata()
            elif update_mode == "2":
                migrate_incremental_quiz_metadata()
            else:
                logging.error("無効な選択です")
                return
                
    except Exception as e:
        logging.error(f"Migration failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()