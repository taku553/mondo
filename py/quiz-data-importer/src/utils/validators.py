# filepath: /quiz-data-importer/quiz-data-importer/src/utils/markdown_parser.py
# データ検証用ユーティリティ
import markdown
import re

def parse_markdown_to_dict(markdown_text):
    """
    マークダウン形式のテキストを辞書形式に変換します。
    
    Args:
        markdown_text (str): マークダウン形式のテキスト

    Returns:
        dict: メタデータと質問データを含む辞書
    """
    lines = markdown_text.strip().split('\n')
    data = {}
    current_question = None

    for line in lines:
        line = line.strip()
        if line.startswith('# クイズタイトル:'):
            data['quiz_title'] = line.split(':', 1)[1].strip()
        elif line.startswith('- ID(id):'):
            data['id'] = line.split(':', 1)[1].strip().strip(',')
        elif line.startswith('- タイトル(title)：'):
            data['title'] = line.split('：', 1)[1].strip().strip(',')
        elif line.startswith('- イメージ(image):'):
            data['image'] = line.split(':', 1)[1].strip().strip(',')
        elif line.startswith('- タグ(tags):'):
            tags = line.split(':', 1)[1].strip().strip('[]').split(',')
            data['tags'] = [tag.strip().strip('"') for tag in tags]
        elif line.startswith('- 説明(description):'):
            data['description'] = line.split(':', 1)[1].strip().strip(',')
        elif line.startswith('- 日付(date):'):
            data['date'] = line.split(':', 1)[1].strip().strip(',')
        elif line.startswith('- カテゴリ(category):'):
            data['category'] = line.split(':', 1)[1].strip().strip(',')
        elif line.startswith('- 全質問数(total_questions)：'):
            data['total_questions'] = int(line.split('：', 1)[1].strip().strip(','))
        elif line.startswith('- ジャンル(subject)：'):
            data['subject'] = line.split('：', 1)[1].strip().strip(',')
        elif line.startswith('- 出題範囲(period)：'):
            data['period'] = line.split('：', 1)[1].strip().strip(',')
        elif line.startswith('- ID(id):') and 'questions' not in data:
            current_question = {}
            current_question['id'] = line.split(':', 1)[1].strip().strip(',')
            data.setdefault('questions', []).append(current_question)
        elif current_question is not None:
            if line.startswith('- テキスト(text):'):
                current_question['text'] = line.split(':', 1)[1].strip().strip(',')
            elif line.startswith('- 選択肢'):
                choice_number = re.search(r'\d+', line).group()
                current_question[f'choice_{choice_number}'] = line.split(':', 1)[1].strip().strip(',')
            elif line.startswith('- 正解(correct_choice_id):'):
                current_question['correct_choice_id'] = int(line.split(':', 1)[1].strip().strip(','))
            elif line.startswith('- 解説(explanation):'):
                current_question['explanation'] = line.split(':', 1)[1].strip().strip(',')
            elif line.startswith('- カテゴリ(category):'):
                current_question['category'] = line.split(':', 1)[1].strip().strip(',')

    return data