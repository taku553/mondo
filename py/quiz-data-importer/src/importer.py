# マークダウンファイルの読み込みと解析を行う
import os
import re # 正規表現モジュールをインポート
import ast # astモジュールをインポート

def load_markdown_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    return content

def parse_metadata(content):
    lines = content.splitlines()
    metadata = {}
    questions = []
    current_question = None
    in_questions_section = False

    # デバッグ用
    print(f"マークダウンファイルの総行数: {len(lines)}")
    
    # メタデータのキーを日本語から英語の小文字にマッピング
    metadata_key_mapping = {
        "ID": "id",
        "タイトル": "title",
        "イメージ": "image",
        "タグ": "tags",
        "説明": "description",
        "日付": "date",
        "カテゴリ": "category",
        "全質問数": "total_questions",
        "ジャンル": "subject",
        "出題範囲": "period"
    }    
    
    for line in lines:
        line = line.strip()
                
        # セクション判定    
        if "## メタデータ" in line:
            in_questions_section = False
            print("メタデータセクションを検出しました")
            continue
        elif "## 質問" in line:
            in_questions_section = True
            current_question = None
            print("質問セクションを検出しました")
            continue

        # 空行またはその他の見出し行をスキップ
        if not line or (line.startswith('#') and not line.startswith('## ')):
            continue
        
        if in_questions_section:
            if line.startswith("- ID(id):"):
                # 前の質問があれば保存
                if current_question and current_question.get('id'):
                    questions.append(current_question)
                    
                # 新しい質問を作成
                current_question = {}
                value = line.split(":", 1)[1].strip().strip(',')
                current_question['id'] = int(value) # IDは整数に変換
                print(f"新しい質問を開始: ID={value}")
                                
            elif line.startswith("- テキスト(text):"):
                if current_question is None:
                    current_question = {}
                value = line.split(":", 1)[1].strip().strip(',')
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]  # 引用符を削除
                current_question['text'] = value
                                
            elif line.startswith("- 選択肢"):
                if current_question is None:
                    current_question = {}
                try:
                    parts = line.split(":", 1) # まずコロンで分割
                    if len(parts) == 2:
                        header_part = parts[0]
                        value_part = parts[1].strip().strip(',') # 末尾のカンマと空白を削除

                        # "- 選択肢1(choices[], id:1)" から選択肢番号を抽出
                        choice_id_match = re.search(r'id:(\d+)', header_part)
                        if choice_id_match:
                            choice_id = int(choice_id_match.group(1))
                        else:
                            # フォールバックとして、"選択肢" の後の数字をIDとする試み
                            choice_num_match = re.search(r'- 選択肢(\d+)', header_part)
                            if choice_num_match:
                                choice_id = int(choice_num_match.group(1))
                            else:
                                print(f"警告: 選択肢IDを抽出できませんでした: {line}")
                                continue

                        # value_part ("選択肢1") から引用符を除去
                        # 例: '"選択肢1"' -> '選択肢1'
                        # 例: '"1): \"選択肢1\""' -> '1): \"選択肢1\"' (この時点では内部の \" はそのまま)
                        if value_part.startswith('"') and value_part.endswith('"'):
                            # 両端の引用符のみ除去
                            cleaned_value = value_part[1:-1]
                            # "1): \"選択肢1\"" のようなパターンから "選択肢1" を抽出する試み
                            # まず "X): " の部分を削除
                            cleaned_value = re.sub(r'^\d+\):\s*', '', cleaned_value)
                            # もし内部にエスケープされた引用符があれば、それも考慮 (ただし、json.dumpsが処理するので基本不要)
                            # ここでは、マークダウン起因の余分なバックスラッシュや二重引用符を消すのが目的
                            # cleaned_value = cleaned_value.replace('\\"', '"') # 不要な場合が多い
                        else:
                            cleaned_value = value_part

                        if 'choices' not in current_question:
                            current_question['choices'] = []
                            
                        current_question['choices'].append({
                            'id': choice_id,
                            'text': cleaned_value
                        })
                except Exception as e:
                    print(f"選択肢の処理中にエラー: {e}, 行: {line}")
                    
            elif line.startswith("- 正解(correct_choice_id):"):
                if current_question is None:
                    current_question = {}
                value = line.split(":", 1)[1].strip().strip(',')
                current_question['correct_choice_id'] = int(value)                
                
            elif line.startswith("- 解説(explanation):"):
                if current_question is None:
                    current_question = {}
                value = line.split(":", 1)[1].strip().strip(',')
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]  # 引用符を削除
                current_question['explanation'] = value
                
            elif line.startswith("- カテゴリ(category):"):
                if current_question is None:
                    current_question = {}
                value = line.split(":", 1)[1].strip().strip(',')
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]  # 引用符を削除
                current_question['category'] = value

        else:  # メタデータセクション
            # メタデータ処理部分
            if line.startswith("- ") and (":" in line or "：" in line):
                # 全角コロンと半角コロンの両方に対応
                if "：" in line:
                    parts = line.split("：", 1)
                else:
                    parts = line.split(":", 1)
                
                if len(parts) == 2:
                    key_from_md, value = parts
                    key_from_md = key_from_md.strip().lstrip('- ')  # 先頭の「- 」も削除
                    
                    # 括弧内の英語名部分を削除した日本語キーを取得 (例: "タイトル(title)" -> "タイトル")
                    base_key_jp = key_from_md.split('(')[0].strip()
                    
                    # マッピングを使用して英語のキー名を取得
                    english_key = metadata_key_mapping.get(base_key_jp)
                    
                    if not english_key:
                        print(f"警告: メタデータキー '{base_key_jp}' のマッピングが見つかりません。元のキー '{key_from_md}' を使用します。")
                        # マッピングにない場合は、括弧を除いた日本語キーか、元のキーを使うか検討
                        # ここでは、括弧を除いた日本語キーをフォールバックとして使用
                        key_to_use = base_key_jp 
                    else:
                        key_to_use = english_key
                    
                    # 値の整形（余計なカンマや引用符を削除）
                    value = value.strip().strip(',')

                    if key_to_use == "tags":
                        try:
                            # '["サンプル", "テスト"]' のような文字列をPythonのリストに変換
                            evaluated_value = ast.literal_eval(value)
                            if isinstance(evaluated_value, list):
                                value = evaluated_value
                            else:
                                # リストに変換できなかった場合は、元の文字列をカンマで分割するなどフォールバック処理も検討可
                                print(f"警告: タグの値 '{value}' をリストとして評価できませんでした。文字列として扱います。")
                        except (ValueError, SyntaxError) as e:
                            print(f"警告: タグの値 '{value}' の評価中にエラー: {e}。文字列として扱います。")
                    elif key_to_use == "id" or key_to_use == "total_questions":
                        try:
                            value = int(value)
                        except ValueError:
                            print(f"警告: キー '{key_to_use}' の値 '{value}' を整数に変換できませんでした。")
                            pass
                    else: # tags, id, total_questions 以外の場合、文字列なら両端の引用符を削除
                        if isinstance(value, str):
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                    
                    metadata[key_to_use] = value
                    print(f"メタデータ追加: {key_to_use} = {value}")
            
            

    # 最後の質問がまだ追加されていない場合は追加
    if current_question and current_question.get('id'):
        print(f"最後の質問を追加: ID={current_question.get('id')}")
        questions.append(current_question)

    # デバッグ情報
    print(f"抽出されたメタデータ: {len(metadata)} 項目")
    print(f"メタデータの項目: {metadata}")
    print(f"抽出された質問数: {len(questions)}問")

    # テストが期待する形式で返す
    return {
        'metadata': metadata,
        'questions': questions
    }

def import_quiz_data(file_path):
    content = load_markdown_file(file_path)
    return parse_metadata(content)

# テストで参照されている名前と合わせるため関数を追加
def load_quiz_data(file_path):
    # 既存の関数を呼び出す
    return import_quiz_data(file_path)