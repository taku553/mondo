# Flaskとその他のモジュールをインポート
from flask import Flask, request, jsonify, session, render_template, url_for, redirect
from flask_session import Session  # Flask-Sessionを追加、ユーザーからの解答データ（セッションデータ）を管理するflaskのパッケージ
from datetime import timedelta #　セッションの有効期限を設定するためのモジュール
from flask_cors import CORS  # CORSをインポート
import random
# dataset.csvからデータセットをインポート
import csv
# ファイルパスの指定のためosをインポート
import os
# 送受信されるデータの状態をコンソールから確認するためloggingをインポート
import logging

# Flaskアプリケーションを初期化
app = Flask(__name__, template_folder=os.path.join('../templates'), static_folder='../static')
CORS(app)  # CORSをアプリケーションに適用
app.config["SESSION_TYPE"] = "filesystem"  # セッションタイプをファイルシステムに設定
app.config["SESSION_FILE_DIR"] = os.path.join("/Users/takahashitakuya/Desktop/history_flow_quiz", "sessions") # セッションファイルの保存先ディレクトリを指定
app.config["SESSION_PERMANENT"] = False # セッションが永続的でないように設定
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1) # セッションの有効期限を1日に設定
Session(app)

# ロガーを設定
logging.basicConfig(level=logging.DEBUG)

# Flaskのロガーにアクセス
logger = logging.getLogger('werkzeug')


# プロジェクトのルートディレクトリへの絶対パス
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# dataset.csvへの絶対パス
dataset_path = os.path.join(project_root, 'py', 'dataset.csv')

# CSVファイルからデータを読み込む
questions = [] # 辞書型：questions
with open(dataset_path, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader: # enumerateを使用してインデックスを追加
        choices = [
            {'id': 1, 'text': row['choice1']},
            {'id': 2, 'text': row['choice2']},
            {'id': 3, 'text': row['choice3']},
            {'id': 4, 'text': row['choice4']}
        ]
        # 整数型：correct_choice_id
        correct_choice_id = next((i + 1 for i, choice in enumerate(choices) if choice['text'] == row['correct_choice']), None)
        explanation = row['explanation'].replace('"', '').replace('|','<br>')
        questions.append({
            'id': int(row['id']),  # 各質問にインデックスを割り当てる
            'text': row['question'],
            'choices': choices,
            'correct_choice_id': correct_choice_id,
            'explanation': explanation
        })

TOTAL_QUESTIONS = 7  # 問題総数

# render_temlpate関数を使い、フロントエンドとバックエンドの連携
# 再利用可能なコンポーネントを作成する

# 例外が発生した場合のグローバルハンドラー
@app.errorhandler(Exception)
def handle_exception(e):
    # すべての例外をキャッチしてJSONレスポンスとして返す
    return jsonify(error=str(e)), 500
        
# ------ ホーム画面のhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/')
def home():
    # cssファイルのurlを生成
    css_url = url_for('static', filename='styles.css')
    
    return render_template('index.html', css_url=css_url)

# ------ プライバシーポリシー画面のhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/privacy_policy')
def privacy_policy():
    # cssファイルのurlを生成
    css_url = url_for('static', filename='styles.css')
    return render_template('privacy_policy.html', css_url=css_url)

# ------ クイズ実行画面のhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/quiz')
def quiz():
    # 必要に応じてセッション変数を初期化

    # 現在の質問のインデックスを初期化
    if 'current_question_index' not in session:
        # 0に初期化。
        session['current_question_index'] = 0
    # 画面に表示された未回答の質問リストを初期化
    if 'current_question' not in session:
        # None：session['current_question']
        session['current_question'] = None
    # 解答済みの質問数を初期化
    if 'answered_question_count' not in session:
        session['answered_question_count'] = 0
    # 解答済みの質問リストを初期化
    if 'answered_questions' not in session:
        # リスト型：session['answered_questions']
        session['answered_questions'] = []
    # 正答だった質問リストを初期化
    if 'correct_answers' not in session:
        # 整数型：session['correct_answers']
        session['correct_answers'] = 0
    
    if not session['current_question']:
        random_question = get_random_question()
        if not random_question:
            return redirect(url_for('result')) # url_forを使用してresultエンドポイントにリダイレクト

     # 次の質問のインデックスを増分
    # session['current_question_index'] += 1

    # cssファイルのurlを生成
    css_url = url_for('static', filename='styles.css')
    
    return render_template('quiz_execution.html', css_url=css_url, current_question_index=session['current_question_index'])


# ------ GETリクエストでランダムに選ばれた質問をフロントエンドに送信するエンドポイント ------
@app.route('/get_random_question', methods=['GET'])
def get_random_question():
    print("get_random_question called")  # デバッグ用のプリント

    # 初めて質問を取得するときは、セッション変数を初期化
    if 'current_question_index' not in session:
        # 0に初期化。
        session['current_question_index'] = 0
        session['answered_questions'] = []
        session['current_question'] = None

    
    # 現在の質問インデックスを取得
    current_index = session['current_question_index']

    # session['current_question_index'] += 1
    

    # 未回答の質問を取得
    # セッションからanswered_questionsリストを取得しそのうちのquestion_idのみ取り出してsetに変換
    # session.get('answered_questions', [])は、answered_questionsキーが存在しない場合に
    # 空リストを返すようになっている
    answered_question_ids = set(aq['question_id'] for aq in session.get('answered_questions', []))
    # questionsリストから、question_idがanswered_question_idsセットに含まれないものだけを抽出
    # して、unanswered_questionsリストを作成
    unanswered_questions = [q for q in questions if q['id'] not in answered_question_ids]
    
    # 未回答の質問がない場合、クイズ終了
    if not unanswered_questions:
        return jsonify({'error': 'No more questions'}), 404

     # 未回答の質問からランダムに選択
    random_question = random.choice(unanswered_questions)
    # 現在の質問をセッションに保存
    session['current_question'] = random_question

    # 選択肢をランダムに並び替える
    random.shuffle(random_question['choices'])

    # 現在の質問データがセッションに保存されたことをターミナルログに表示
    app.logger.info(f"Current question data saved to session: {random_question['text']}")

    return jsonify({
        # 質問のID
        'id': random_question['id'],
        # 質問の問題文
        'question': {'text': random_question['text']},
        # 質問の選択肢
        'choices': random_question['choices'],
       # 次の問題インデックスを返す
        'next_index': current_index + 1,
        # 解答済み問題数をレスポンスに含める
        'answered_questions': session.get('answered_questions', []),
        # 質問の総数
        'total_questions': TOTAL_QUESTIONS
})

# ------ POSTリクエストでユーザーの回答を処理するエンドポイント ------
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    # リクエストデータをロギング
    data = request.json
    # 整数型：question_id
    question_id = data['questionId']
    logger.debug('Received data: %s', data)
    print('question_id in submit_answer:', question_id)
    # 解答済みの質問数を増分
    session['answered_question_count'] += 1

    # questionIdの値が適切か確認するデバックプリント
    print(f"Received questionId: {question_id}, type: {type(question_id)}")

     # データ型確認
    if not isinstance(question_id, int):
        # エラー処理
        return jsonify({'error': 'Invalid data type question_id'}), 400

    # question_idを整数に変換
    # question_id = int(question_id)

    # questionIdがquestions配列のインデックス範囲内にあるか検証する
    if question_id not in [q['id'] for q in questions]:
        return jsonify({'error': 'questionId is out of range'}), 400

    # セッション内容を出力
    app.logger.debug(session)


    # jsで定義したグローバル変数を割り当てるキー名
    # 整数型：active_choice_id
    active_choice_id = data['activeChoice']
    # choiceIdの値が適切か確認するデバックプリント
    print(f"Received activeChoiceId: {active_choice_id}, type: {type(active_choice_id)}")
    if active_choice_id is None:
        logger.error('activeChoice key is missing in the request data')
        return jsonify({'error': 'activeChoice key is missing'}), 400
    
     # データ型確認
    if not isinstance(active_choice_id, int):
        # エラー処理
        return jsonify({'error': 'Invalid data type active_choice_id'}), 400

    # インデックスとして質問を取得
    question = next((q for q in questions if q['id'] == question_id), None)
    if question is None:
        return jsonify({'error': 'Invalid question ID'}), 400
    # "question = questions[question_id]"の記述はquestion_id整数に変換し
    # questionsリストから直接質問を取得しようとするものだが、リストの要素が辞書型なので
    # 整数の添字アクセスはできない。よってquestion_idは整数のまま使用し
    # questionsリストから質問を探すようにする。
    
    if 'correct_answers' not in session:
        session['correct_answers'] = 0  # セッションに正答数を初期化、変数は"correct_answersに設定"

    

    # 正誤判定
    if question is not None:
        # 整数型：result　整数型：current_choice_id
        result = 'correct' if active_choice_id == question['correct_choice_id'] else 'incorrect'
    else:
        return jsonify({'error': 'Invalid question'}), 400
    
    if result == 'correct':
        session['correct_answers'] += 1  # 正答数を増分
    
    # 現在の質問をクリア
    session['current_question'] = None

    
    # 現在の質問の解答データをリストに追加
    session['answered_questions'] = session.get('answered_questions', [])
    session['answered_questions'].append({
        'question_id': question_id,
        'result': result,
        'user_choice': active_choice_id,  # ユーザーの選択した選択肢のIDも記録することができます
        'correct_choice': question['correct_choice_id'],
        'explanation': question['explanation'],  # 解説文もここでセッションに格納
        'display_order': session['current_question_index']  # 表示順序を設定
    })

    # session['answerer_questions']の構造を確認するデバッグプリント
    print(f"Updated answered_questions: {session['answered_questions']}")  

    # クイズの終了条件を判定
    # session['answered_questions']を使うことで実際に表示された質問数
    is_quiz_finished = session['answered_question_count'] >= TOTAL_QUESTIONS

    # クイズが終了していない場合、次の質問のインデックスを保存
    if not is_quiz_finished:
        next_question = get_random_question()
        session['current_question'] = next_question
        session['current_question_index'] += 1
        session.modified = True # セッションが変更されたことをFlaskに通知
                       
    # 結果と解説の返送
    return jsonify({
        'result': result, 
        'explanation': question['explanation'], 
        'correct_answers': session['correct_answers'],
        'isQuizFinished': is_quiz_finished,
        'currrent_question_index': session['current_question_index']
    })


# ------ 結果画面のhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/result')
def result():
    # answered_questionsの構造を確認
    print(f"answered_questions in session: {session.get('answered_questions', [])}")

    # 空のリストとして初期化
    answered_questions_info = []

    # 質問画面と結果画面の問題番号が一致しているかチェック
    question_order_mismatch = False
    if len(session.get('answered_questions', [])) != session.get('answered_question_count', 0):
        question_order_mismatch = True
        app.logger.error('質問画面と結果画面の問題番号が一致しませんでした。')

    # 問題番号の不一致がある場合のエラーメッセージ
    if question_order_mismatch:
        return render_template('result.html', correct=correct_answers, total=total_questions, error_message='質問画面と結果画面の問題番号が一致しませんでした。')
    
   # questionsリストをループ処理し、それぞれの問題文に対し個別にtry-except文を適用
    # これによりエラーが発生した質問だけを特定
    for question in questions:
        try:
            # セッションからこの質問に対するユーザーの解答を取得
            user_answer = next((q for q in session.get('answered_questions', []) if q['question_id'] == question['id']), None)
            # ユーザーが選んだ選択肢の文章を格納するキーをまだ設定していなかったので新たに作成し、
            # これに文章を格納する
            # ユーザーが選んだ選択肢の文章を取得
            user_choice_text = next((c['text'] for c in question['choices'] if c['id'] == user_answer['user_choice']), 'Unknown')
            answered_question_info = {
                'text': question['text'],
                'user_choice_text': user_choice_text,
                'explanation': next((q['explanation'] for q in session.get('answered_questions', []) if q['question_id'] == question['id']), question['explanation']),
                'display_order': user_answer['display_order'] + 1  # 表示順序を1から始めるよう修正
            }
            answered_questions_info.append(answered_question_info)    
        except (TypeError, KeyError) as e:
            print(f"Error occurred: {str(e)}")
            print(f"question object: {question}")
            raise e

    # セッションから正答数を取得
    correct_answers = session.get('correct_answers', 0)
    total_questions = len(questions)

    # セッション内容を出力
    app.logger.debug(session)

    # 表示順序に基づいて answered_questions_info をソート
    answered_questions_info.sort(key=lambda q: q['display_order'])
    
    # result.htmlに正答数と総問題数を渡す
    return render_template('result.html', correct=correct_answers, total=total_questions, answered_questions=answered_questions_info)

@app.route('/reset_quiz', methods=['GET'])
def reset_quiz():
    # セッションをリセットする必要があるクイズ関連の変数のみクリア
    session.pop('current_question_index', None)
    session.pop('current_question', None)
    session.pop('correct_answers', None)
    session.pop('answered_questions', None)
    session.pop('answered_question_count', None)
    session.modified = True

    # JSONレスポンスを返す
    return jsonify({'status': 'Quiz reset successfully'}), 200

# スクリプトが直接実行された場合にアプリケーションが開始
if __name__ == '__main__':
    app.run(debug=True)