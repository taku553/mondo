import re
import os

def update_dataset_py(quiz_metadata, questions, dataset_path,
                      metadata_line=None, questions_line=None):
    """
    dataset.pyファイルを直接更新して、メタデータと質問を追加する
    
    Args:
        quiz_metadata (dict): メタデータの辞書
        questions (list): 質問のリスト
        dataset_path (str): dataset.pyのファイルパス
        metadata_line (int, optional): メタデータを挿入する行番号
        questions_line (int, optional): 質問データを挿入する行番号        
    """
    # ファイル全体を読み込み
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 質問リストとメタデータリストの終端位置を特定
    questions_end = find_list_end(lines, "questions = [")
    metadata_end = find_list_end(lines, "quiz_metadata = [")
    
    if questions_end:
        print(f"questions[]の終端は{questions_end+1}行目です")
    if metadata_end:
        print(f"quiz_metadata[]の終端は{metadata_end+1}行目です")
    
    # 指定がなければ検出した終端の手前に挿入する
    if questions_line is None and questions_end is not None:
        questions_line = questions_end
        print(f"質問データは{questions_line+1}行目に挿入することを推奨します")
    
    if metadata_line is None and metadata_end is not None:
        metadata_line = metadata_end
        print(f"メタデータは{metadata_line+1}行目に挿入することを推奨します")
    
    # まず質問データを挿入
    if questions and questions_line is not None:
        _insert_questions(questions, dataset_path, questions_line)
    elif questions:
        _insert_questions(questions, dataset_path)
    
    # 次にメタデータを挿入
    if quiz_metadata and metadata_line is not None:
        _insert_metadata(quiz_metadata, dataset_path, metadata_line)
    elif quiz_metadata:
        _insert_metadata(quiz_metadata, dataset_path)
    
    print(f"データセットを更新しました: {len(questions)}問の質問と1件のメタデータを追加")

def find_list_end(lines, start_pattern):
    """
    指定したパターンで始まるリストの終端行番号を検索する
    括弧の深さを追跡して正確に親リストの終端を特定する
    
    Args:
        lines (list): ファイルの内容を1行ずつ格納したリスト
        start_pattern (str): 検索するリストの開始パターン
        
    Returns:
        int or None: 終端行の番号（0起算）または見つからない場合はNone
    """
    # リストの開始行を特定
    start_line = None
    # より柔軟なパターンマッチングのために空白を無視
    # 特に '[' はエスケープが必要
    escaped_start_pattern = start_pattern.replace("[", r"\[")
    search_pattern = escaped_start_pattern.replace(" ", r"\s*")    
    
    print(f"検索パターン: '{start_pattern}', 正規表現: '{search_pattern}'")
    
    for i, line in enumerate(lines):
        if re.search(search_pattern, line):  # 正規表現でマッチング
            start_line = i
            print(f"パターン '{start_pattern}' が {i+1} 行目で見つかりました")
            break
    
    if start_line is None:
        print(f"警告: パターン '{start_pattern}' が見つかりませんでした")
        # より緩いパターンで再試行
        for i, line in enumerate(lines):
            if start_pattern.split()[0] in line and "[" in line:
                start_line = i
                print(f"緩いパターンマッチ: '{start_pattern.split()[0]}' が {i+1} 行目で見つかりました")
                break
    
    if start_line is None:
        print(f"警告: '{start_pattern}' のリスト開始位置を特定できませんでした")
        return None
    
    # 括弧の深さを追跡
    bracket_depth = 0
    in_string = False  # 文字列内部フラグ
    string_char = None  # 文字列の区切り文字
    in_comment = False  # コメント内部フラグ
    
    # 開始行で最初の開き括弧を見つける
    found_first_bracket = False
    
    print(f"パターン '{start_pattern}' のリスト解析を開始します（{start_line+1}行目から）")
    
    for i in range(start_line, len(lines)):
        line = lines[i]
        j = 0
        
        while j < len(line):
            char = line[j]
            
            # コメントの開始をチェック
            if not in_string and char == '#':
                in_comment = True
                j += 1
                continue
            
            # コメント内の文字はスキップ
            if in_comment:
                j += 1
                continue
            
            # 文字列の開始/終了をチェック
            if char in ['"', "'"]:
                if not in_string:
                    in_string = True
                    string_char = char
                elif string_char == char:
                    # 直前の文字がエスケープされていなければ、文字列終了
                    if j > 0 and line[j-1] != '\\':
                        in_string = False
            
            # 文字列内の文字はカウントしない
            elif not in_string:
                if char == '[':
                    found_first_bracket = True
                    bracket_depth += 1
                    # print(f"{i+1}行目: 開き括弧を検出 (深さ: {bracket_depth})")
                elif char == ']':
                    if found_first_bracket:  # 最初の開き括弧を見つけた後のみカウント
                        bracket_depth -= 1
                        # print(f"{i+1}行目: 閉じ括弧を検出 (深さ: {bracket_depth})")
                        # 深さが0になったとき、これが親リストの終端
                        if bracket_depth == 0:
                            print(f"リストの終端を {i+1} 行目で検出しました")
                            return i
            
            j += 1
        
        # 行末でコメントフラグをリセット
        in_comment = False
    
    print(f"警告: リストの終端が見つかりませんでした")
    return None

def _insert_questions(questions, dataset_path, line=None):
    """質問データをdataset.pyに挿入する"""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 質問データを整形
    escaped_quote = "\\\""
    formatted_questions = []
    for q in questions:
        # エスケープ処理をf-string外で実行
        text = q['text'].replace('"', escaped_quote)
        explanation = q['explanation'].replace('"', escaped_quote)
        category = q['category'].replace('"', escaped_quote)
        
        q_text = f"""
                {{
                    "id": {q['id']}, 
                    "text": "{text}", 
                    "image": "", 
                    "choices": {format_choices(q['choices'])}, 
                    "correct_choice_id": {q['correct_choice_id']}, 
                    "explanation": "{explanation}", 
                    "category": "{category}",
                }},"""
        formatted_questions.append(q_text)
    
    # 挿入位置の決定
    if line is not None:
        insert_at = min(line, len(lines))
        for i, question_text in enumerate(formatted_questions):
            lines.insert(insert_at + i, question_text)
        print(f"{len(formatted_questions)}問の質問データを行{insert_at+1}に挿入しました")
    else:
        # 親リストの終端を特定する
        questions_end = find_list_end(lines, "questions = [")
        if questions_end is not None:
            for j, question_text in enumerate(formatted_questions):
                lines.insert(questions_end, question_text)
                questions_end += 1  # 挿入後は位置が1つずつ後ろにずれる
            print(f"質問リストの終端手前に{len(formatted_questions)}問のデータを挿入しました")
        else:
            print("警告: 質問リストの終端が見つかりません。データは追加されませんでした。")
            return
    
    # ファイルに書き戻す
    with open(dataset_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def _insert_metadata(quiz_metadata, dataset_path, line=None):
    """メタデータをdataset.pyに挿入する"""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # メタデータを整形
    escaped_quote = "\\\""
    
    # IDは数値として扱う
    quiz_id = int(quiz_metadata["ID"]) if "ID" in quiz_metadata else 999
    
    # タグの処理
    tags_value = quiz_metadata["タグ"]
    if isinstance(tags_value, str) and tags_value.startswith("[") and tags_value.endswith("]"):
        tags_content = tags_value.strip("[]").split(",")
        tags_list = [tag.strip().strip('"\'') for tag in tags_content]
        tags_formatted = str(tags_list)
    else:
        tags_formatted = tags_value
    
    # テキストフィールドをエスケープ（f-string外で処理）
    title = quiz_metadata["タイトル"].replace('"', escaped_quote)
    description = quiz_metadata["説明"].replace('"', escaped_quote)
    subject = quiz_metadata["ジャンル"].replace('"', escaped_quote)
    period = quiz_metadata["出題範囲"].replace('"', escaped_quote)
    
    formatted_metadata = f"""
            {{
                "id": {quiz_id},
                "title": "{title}",
                "image": "{quiz_metadata["イメージ"]}",
                "tags": {tags_formatted},
                "description": "{description}",
                "date": "{quiz_metadata["日付"]}",
                "category": "{quiz_metadata["カテゴリ"]}",
                "total_questions": {quiz_metadata["全質問数"]},
                "subject": "{subject}",
                "period": "{period}",
            }},"""
    
    # 挿入位置の決定
    if line is not None:
        insert_at = min(line, len(lines))
        lines.insert(insert_at, formatted_metadata)
        print(f"メタデータを行{insert_at+1}に挿入しました")
    else:
        # 親リストの終端を特定する
        metadata_end = find_list_end(lines, "quiz_metadata = [")
        if metadata_end is not None:
            lines.insert(metadata_end, formatted_metadata)
            print(f"メタデータリストの終端手前にデータを挿入しました")
        else:
            print("警告: メタデータリストの終端が見つかりません。データは追加されませんでした。")
            return
    
    # ファイルに書き戻す
    with open(dataset_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def format_choices(choices):
    """選択肢のリストを整形する"""
    escaped_quote = "\\\""
    formatted = []
    for choice in choices:
        # エスケープ処理をf-string外で実行
        text = choice['text'].replace('"', escaped_quote)
        formatted.append(f'{{"id": {choice["id"]}, "text": "{text}"}}')
    return "[" + ", ".join(formatted) + "]"