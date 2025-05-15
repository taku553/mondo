"""
マークダウン形式のクイズデータを解析するためのユーティリティモジュール
"""
import re
import logging

logger = logging.getLogger(__name__)

def read_markdown_file(file_path):
    """
    マークダウンファイルを読み込みます。

    Args:
        file_path (str): マークダウンファイルのパス

    Returns:
        str: マークダウンファイルの内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        logger.error(f"ファイル読み込みエラー: {str(e)}")
        raise IOError(f"ファイル'{file_path}'を読み込めませんでした: {str(e)}")

def extract_sections(content):
    """
    マークダウンの内容からメタデータセクションと質問セクションを抽出します。

    Args:
        content (str): マークダウンの内容

    Returns:
        tuple: (メタデータセクション, 質問セクション)
    """
    # メタデータセクションの抽出
    metadata_match = re.search(r'## メタデータ(.*?)## 質問', content, re.DOTALL)
    if not metadata_match:
        raise ValueError("メタデータセクションが見つかりませんでした。")
    
    metadata_section = metadata_match.group(1).strip()
    
    # 質問セクションの抽出
    questions_match = re.search(r'## 質問(.*?)$', content, re.DOTALL)
    if not questions_match:
        raise ValueError("質問セクションが見つかりませんでした。")
    
    questions_section = questions_match.group(1).strip()
    
    return metadata_section, questions_section

def parse_metadata(metadata_section):
    """
    メタデータセクションを解析し、辞書形式で返します。

    Args:
        metadata_section (str): メタデータセクション

    Returns:
        dict: メタデータの辞書
    """
    metadata = {}
    
    # 各メタデータ項目を抽出
    patterns = {
        'id': r'- ID\(id\): (.*?),',
        'title': r'- タイトル\(title\)： "(.*?)",',
        'image': r'- イメージ\(image\)："(.*?)",',
        'tags': r'- タグ\(tags\): \[(.*?)\],',
        'description': r'- 説明\(description\): "(.*?)",',
        'date': r'- 日付\(date\): (.*?),',
        'category': r'- カテゴリ\(category\): "(.*?)",',
        'total_questions': r'- 全質問数\(total_questions\)：(\d+),',
        'subject': r'- ジャンル\(subject\)："(.*?)",',
        'period': r'- 出題範囲\(period\)："(.*?)"'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, metadata_section, re.DOTALL)
        if match:
            metadata[key] = match.group(1).strip()
    
    # tagsを適切なリスト形式に変換
    if 'tags' in metadata:
        metadata['tags'] = [tag.strip() for tag in metadata['tags'].split(',')]
    
    return metadata

def parse_questions(questions_section):
    """
    質問セクションを解析し、質問リストを返します。

    Args:
        questions_section (str): 質問セクション

    Returns:
        list: 質問の辞書リスト
    """
    # 質問を区切るパターン
    question_pattern = r'- ID\(id\): (.*?)(?=- ID\(id\)|$)'
    question_matches = re.finditer(question_pattern, questions_section, re.DOTALL)
    
    questions = []
    for match in question_matches:
        question_text = match.group(0)
        question = {}
        
        # 各質問の要素を抽出
        patterns = {
            'id': r'- ID\(id\): (.*?),',
            'text': r'- テキスト\(text\): "(.*?)",',
            'choices': r'- 選択肢(\d+)\(choices\[\], id:\1\): "(.*?)",',
            'correct_choice_id': r'- 正解\(correct_choice_id\): (\d+),',
            'explanation': r'- 解説\(explanation\): "(.*?)",',
            'category': r'- カテゴリ\(category\): "(.*?)"'
        }
        
        for key, pattern in patterns.items():
            if key == 'choices':
                question['choices'] = []
                choice_matches = re.finditer(pattern, question_text)
                for choice_match in choice_matches:
                    choice_id = int(choice_match.group(1))
                    choice_text = choice_match.group(2)
                    question['choices'].append({
                        'id': choice_id,
                        'text': choice_text
                    })
            else:
                match = re.search(pattern, question_text, re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    # 数値の場合は整数に変換
                    if key == 'id' and value.isdigit():
                        question[key] = int(value)
                    elif key == 'correct_choice_id' and value.isdigit():
                        question[key] = int(value)
                    else:
                        question[key] = value
        
        questions.append(question)
    
    return questions