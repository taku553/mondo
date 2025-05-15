#!/usr/bin/env python3
# filepath: /Users/takahashitakuya/Desktop/history_flow_quiz/py/quiz-data-importer/main.py
import sys
import os
import argparse
import pprint
import textwrap
import json
from src.importer import import_quiz_data
from src.dataset_updater import find_list_end # find_list_end をインポート

def update_dataset_revised(args, new_questions, new_quiz_metadata_dict):
    try:
        with open(args.dataset, 'r', encoding='utf-8') as f:
            dataset_lines = list(f) # ファイル内容を行ごとのリストとして読み込む

        # 1. 質問データの挿入
        if new_questions:
            questions_insert_target_line_idx = args.questions_line
            if questions_insert_target_line_idx is None:
                questions_insert_target_line_idx = find_list_end(dataset_lines, "questions = [")
            
            if questions_insert_target_line_idx is not None:
                # find_list_end は閉じ括弧 ']' のある行のインデックス(0起算)を返す
                # 挿入はそのインデックスの場所に行う (元の行はその下にずれる)
                
                questions_data_to_insert = []
                for q_dict in new_questions:
                    # json.dumps でダブルクォーテーションで囲まれた文字列を生成
                    # ensure_ascii=False で日本語をそのまま出力
                    # indent=4 で dataset.py のインデントに合わせる
                    formatted_q_str = json.dumps(q_dict, indent=4, ensure_ascii=False)
                    # textwrap.indent で全体のインデントを調整 (dataset.py のリスト内のインデントに合わせる)
                    # dataset.py の questions = [ の次の行のインデントが8スペースの場合
                    indented_q_str = textwrap.indent(formatted_q_str, '    ') + ',\n' # 辞書ごとにカンマと改行を追加
                    questions_data_to_insert.append(indented_q_str)
                
                # 挿入位置の直前の行にカンマがなければ追加
                if questions_insert_target_line_idx > 0:
                    prev_line_idx_q = questions_insert_target_line_idx - 1
                    # リストの最後の要素の行を探す (空行やコメント行をスキップ)
                    while prev_line_idx_q >= 0 and (not dataset_lines[prev_line_idx_q].strip() or dataset_lines[prev_line_idx_q].strip().startswith('#')):
                        prev_line_idx_q -= 1
                        
                    if prev_line_idx_q >= 0:
                        stripped_prev_line_q = dataset_lines[prev_line_idx_q].rstrip()
                        if stripped_prev_line_q.endswith('}') and not stripped_prev_line_q.endswith(','):
                            dataset_lines[prev_line_idx_q] = stripped_prev_line_q + ',\n'
                
                dataset_lines[questions_insert_target_line_idx:questions_insert_target_line_idx] = questions_data_to_insert
                print(f"{len(new_questions)}問の質問データを挿入しました。")
            else:
                print("警告: questionsリストの終端が見つからず、質問データを挿入できませんでした。")
        
        # 2. メタデータの挿入
        if new_quiz_metadata_dict: # new_quiz_metadata_dict は単一の辞書
            metadata_insert_target_line_idx = args.metadata_line
            if metadata_insert_target_line_idx is None:
                # 質問データ挿入後の dataset_lines を使ってメタデータの終端を再検索
                metadata_insert_target_line_idx = find_list_end(dataset_lines, "quiz_metadata = [")

            if metadata_insert_target_line_idx is not None:
                # json.dumps で整形
                formatted_m_str = json.dumps(new_quiz_metadata_dict, indent=4, ensure_ascii=False)
                indented_m_str = textwrap.indent(formatted_m_str, '    ') + ',\n' # 辞書ごとにカンマと改行を追加
                
                if metadata_insert_target_line_idx > 0:
                    prev_line_idx_m = metadata_insert_target_line_idx - 1
                    # リストの最後の要素の行を探す (空行やコメント行をスキップ)
                    while prev_line_idx_m >= 0 and (not dataset_lines[prev_line_idx_m].strip() or dataset_lines[prev_line_idx_m].strip().startswith('#')):
                        prev_line_idx_m -= 1

                    if prev_line_idx_m >= 0:
                        stripped_prev_line_m = dataset_lines[prev_line_idx_m].rstrip()                    
                    if stripped_prev_line_m.endswith('}') and not stripped_prev_line_m.endswith(','):
                         dataset_lines[prev_line_idx_m] = stripped_prev_line_m + ',\n'

                dataset_lines[metadata_insert_target_line_idx:metadata_insert_target_line_idx] = [indented_m_str]
                print(f"メタデータを挿入しました。")
            else:
                print("警告: quiz_metadataリストの終端が見つからず、メタデータを挿入できませんでした。")

        # 3. 更新された内容でファイルに書き込む
        with open(args.dataset, 'w', encoding='utf-8') as f:
            f.writelines(dataset_lines)
        
    except FileNotFoundError:
        print(f"エラー: データセットファイル '{args.dataset}' が見つかりません。")
    except Exception as e:
        print(f"データセットの更新中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='マークダウン形式のクイズデータを読み込み、dataset.pyに追加します。')
    parser.add_argument('markdown_file', help='読み込むマークダウンファイルのパス')
    parser.add_argument('--dataset', default='../dataset.py', help='更新するdataset.pyのパス（デフォルト: ../dataset.py）')
    parser.add_argument('--metadata-line', type=int, help='メタデータを挿入する行番号')
    parser.add_argument('--questions-line', type=int, help='質問データを挿入する行番号')    
    
    args = parser.parse_args()

    # マークダウンファイルの存在確認
    if not os.path.exists(args.markdown_file):
        print(f"エラー: マークダウンファイル '{args.markdown_file}' が見つかりません。")
        return 1

    try:
        # マークダウンファイルを読み込んで解析
        parsed_data = import_quiz_data(args.markdown_file)
        quiz_metadata_from_md = parsed_data['metadata']
        questions_from_md = parsed_data['questions']
        
        # データの検証
        if not quiz_metadata_from_md:
            print("警告: メタデータが空です。")
        if not questions_from_md:
            print("警告: 質問データが空です。")
        
        # 必要なキーの確認
        required_metadata = ["ID", "タイトル", "イメージ", "タグ", "説明", "日付", "カテゴリ", "全質問数", "ジャンル", "出題範囲"]
        missing = [key for key in required_metadata if key not in quiz_metadata_from_md]
        if missing:
            print(f"警告: メタデータに必要なキーが不足しています: {', '.join(missing)}")
        
        if missing:
            print(f"警告: メタデータに必須キーがありません: {', '.join(missing)}")
            # return 1 # 処理を継続するか、ここで終了するかは要件による

        # dataset.pyの総行数を取得と終端位置の特定
        try:
            with open(args.dataset, 'r', encoding='utf-8') as f:
                dataset_lines = f.readlines()
            print(f"dataset.pyの総行数: {len(dataset_lines)}")

            # find_list_end を使って正確な終端位置を特定し、表示
            # この時点で find_list_end 内のデバッグプリントが出力されます
            questions_actual_end_line = find_list_end(dataset_lines, "questions = [")
            metadata_actual_end_line = find_list_end(dataset_lines, "quiz_metadata = [")

            if args.questions_line is None:
                if questions_actual_end_line is not None:
                    print(f"質問データの挿入行が指定されていません。推奨挿入行: {questions_actual_end_line + 1} (questionsリストの終端括弧の行)")
                else:
                    print(f"質問データの挿入行が指定されていません。questionsリストの終端を自動検出できませんでした。")
            
            if args.metadata_line is None:
                if metadata_actual_end_line is not None:
                    print(f"メタデータの挿入行が指定されていません。推奨挿入行: {metadata_actual_end_line + 1} (quiz_metadataリストの終端括弧の行)")
                else:
                    print(f"メタデータの挿入行が指定されていません。quiz_metadataリストの終端を自動検出できませんでした。")

        except FileNotFoundError:
            print(f"エラー: データセットファイル '{args.dataset}' が見つかりません。")
            return 1
        
        print(f"抽出されたメタデータ: {len(quiz_metadata_from_md)} 項目")
        print(f"メタデータの項目: {quiz_metadata_from_md}")
        print(f"抽出された質問数: {len(questions_from_md)}問")

        # ユーザーに確認
        confirm = input(f"このデータを{args.dataset}に追加しますか？ (y/n): ")
        if confirm.lower() == 'y':
            update_dataset_revised(args, questions_from_md, quiz_metadata_from_md)
            print(f"データの追加が完了しました。データセット '{args.dataset}' を確認してください。")
        else:
            print("処理を中断しました。")
               
    
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    

if __name__ == "__main__":
    sys.exit(main())