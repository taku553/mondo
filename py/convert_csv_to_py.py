import csv
import os

# CSVファイルのパス
csv_file_path = 'py/dataset.csv'
# 出力するPythonファイルのパス
py_file_path = 'py/dataset.py'

# CSVファイルを読み込み、辞書リストに変換
questions = []
with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        choices = [
            {'id': i+1, 'text': row[f'choice{i+1}']} for i in range(4)
        ]
        correct_choice_id = next((i + 1 for i, choice in enumerate(choices) if choice['text'] == row['correct_choice']), None)
        explanation = row['explanation'].replace('"', '').replace('|','<br>')
        questions.append({
            'id': int(row['id']),
            'text': row['question'],
            'image': row['image'],
            'choices': choices,
            'correct_choice_id': correct_choice_id,
            'explanation': explanation,
            'category': row['category']
        })

# Pythonファイルとして保存
with open(py_file_path, 'w', encoding='utf-8') as pyfile:
    pyfile.write(f"questions = {questions}")