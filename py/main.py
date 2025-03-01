# Flaskとその他のモジュールをインポート
from flask import Flask, request, jsonify, session, render_template, url_for, redirect, current_app, abort, send_from_directory
from flask_session import Session  # Flask-Sessionを追加、ユーザーからの解答データ（セッションデータ）を管理するflaskのパッケージ
from flask_cors import CORS  # CORSをインポート
import random
import json
# ファイルパスの指定のためosをインポート
import os
from datetime import timedelta
# 送受信されるデータの状態をコンソールから確認するためloggingをインポート
import logging
from logging.handlers import RotatingFileHandler
# redisをインポート
import redis
# dataset.pyからデータセットをインポート
from py.dataset import questions, quiz_metadata

# ロギングの設定
logging.basicConfig(level=logging.INFO)

# Flaskアプリケーションを初期化
app = Flask(__name__, template_folder=os.path.join('../templates'), static_folder='../static')
app.logger.setLevel(logging.DEBUG)  # Flaskのロガーレベルを設定

# 環境変数から設定を読み込む
app_env = os.environ.get('APP_ENV', 'production')

if app_env == 'production':
    redis_url = os.environ.get('REDIS_URL', 'redis://red-ctv7rel2ng1s73dp0na0:6379')
    if not redis_url:
        raise ValueError('REDIS_URL must be set in production')
        
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise ValueError('SECRET_KEY must be set in production')
    
    # Redis接続テストを追加
    try:
        redis_client = redis.from_url(redis_url)
        redis_client.ping()  # 接続テスト
        app.logger.info("Successfully connected to Redis")
    except redis.ConnectionError as e:
        app.logger.error(f"Redis connection failed: {str(e)}")
        # エラー発生時にフォールバック設定を使用するか、エラーを発生させる
        raise RuntimeError(f"Failed to connect to Redis: {str(e)}")
    
    app.config.update(
        DEBUG=False,
        SESSION_TYPE='redis',  # セッションデータをRedisに保存
        SESSION_REDIS = redis_client,
        SECRET_KEY=secret_key,  # 環境変数から取得
        SESSION_PERMANENT = False, # セッションが永続的でないように設定
        PERMANENT_SESSION_LIFETIME = timedelta(days=1) # セッションの有効期限を1日に設定
        # 他の本番環境用の設定
    )
        
    # App Engine環境用のログ設定
    app.logger.setLevel(logging.INFO)
    
else:
    app.config.update(
        DEBUG=True,
        SECRET_KEY='dev-secret-key',  # 開発環境用のデフォルトのシークレットキー
        SESSION_TYPE='redis',
        # SESSION_FILE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sessions')), # セッションファイルの保存先ディレクトリを指定
        SESSION_REDIS = redis.from_url('redis://localhost:6379'),  # Redisの接続情報を設定
        SESSION_PERMANENT=False,
        PERMANENT_SESSION_LIFETIME=timedelta(days=1)
        # 他の開発環境用の設定
    )
    # 開発環境用のログ設定
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

# セッションを初期化    
Session(app)

CORS(app)  # CORSをアプリケーションに適用


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
    return render_template('index.html', css_url=css_url, quizzes=quiz_metadata)

# ------ クイズの概要ページhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/quiz_info/<int:quiz_id>')
def quiz_info(quiz_id):
    # quiz_metadataから該当するクイズ情報を取得
    quiz = next((q for q in quiz_metadata if q['id'] == quiz_id), None)
    
    # クイズが見つからない場合は404エラー
    if quiz is None:
        abort(404)
    
    # cssファイルのURLを生成
    css_url = url_for('static', filename='styles.css')
    return render_template('quiz_info.html', css_url=css_url, quiz=quiz)


# ------ タグの検索結果ページhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/tag_search')
def tag_search():
    tag = request.args.get('tag', '').strip()  # 余分な空白を削除
    
    # quiz_metadataからタグに一致するクイズをフィルタリング
    filtered_quizzes = [
        quiz for quiz in quiz_metadata if tag in quiz.get('tags', [])
    ]
 
    css_url = url_for('static', filename='styles.css')
    return render_template('tag_search.html', tag=tag, quizzes=filtered_quizzes, css_url=css_url)

# ------ プライバシーポリシー画面のhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/privacy_policy')
def privacy_policy():
    # cssファイルのurlを生成
    css_url = url_for('static', filename='styles.css')
    return render_template('privacy_policy.html', css_url=css_url)


# ------ obots.txtを提供するためのルートハンドラー ------
@app.route('/robots.txt')
def serve_robots():
    return send_from_directory(app.root_path, 'robots.txt')

# ------ ドロップダウンメニューで選択された項目対応したデータ列の範囲を決定するエンドポイント ------
@app.route('/set_quiz_range', methods=['POST'])
def set_quiz_range():
    print("set_quiz_range called")  # set_quiz_range()関数が呼び出されてるか確かめるプリント
    data = request.json
    selected_range = data.get('range')
    if selected_range in ['first', 'second', 'third', 'opening']: # 有効な年代のみを受け付ける
        session['quiz_range'] = selected_range
        app.logger.info(f"Quiz range set to: {session['quiz_range']}")  # session['quiz_range']にどのデータ範囲が保存されたか確認するログ
        # 選択された範囲に基づいて質問をフィルタリング
        filtered_questions = [q for q in questions if q['category'] == selected_range]
        # フィルタリングされた質問の総数をセッションに保存
        session['total_questions'] = len(filtered_questions)
        #global TOTAL_QUESTIONS
        # TOTAL_QUESTIONSを動的に設定
        #TOTAL_QUESTIONS = len(filtered_questions)
        app.logger.info(f"Total questions for selected range '{selected_range}': {len(filtered_questions)}")
        return jsonify({'status': 'success'})
    else:
        app.logger.warning(f"Invalid quiz range selected: {selected_range}")  # エラー時のログ
        return jsonify({'status': 'error', 'message': '出題範囲が選択されていません。'}), 400


# ------ クイズ実行画面のhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/quiz')
def quiz():
    print("quiz called")  # quiz()関数が呼び出されてるか確かめるプリント

    # セッションに出題範囲が設定されていない場合、ホーム画面にリダイレクト
    if 'quiz_range' not in session:
        app.logger.warning("Attempted to access /quiz without setting quiz_range")
        return redirect(url_for('/'))  # url_forを使用してホーム画面にリダイレクト
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
        

    # cssファイルのurlを生成
    css_url = url_for('static', filename='styles.css')
    return render_template('quiz.html', css_url=css_url, current_question_index=session['current_question_index'])


# ------ページをリロードした時に呼び出されるエンドポイント ------
@app.route('/keep_session', methods=['POST'])
def keep_session():
    app.logger.info("keep_session called")
    app.logger.info(f"Request headers: {request.headers}")
    app.logger.info(f"Request data: {request.json}")       
    # セッションを保持し、quiz_rangeが設定されていることを確認
    if 'quiz_range' not in session or session['quiz_range'] is None:
        # quiz_rangeが設定されていない場合、エラーを返す
        return jsonify({'error': '出題範囲が設定されていません。ホーム画面に戻ってください。'}), 400
    # セッションを保持するだけで何もしない
    return jsonify({'status': 'success'})


# ------ GETリクエストでランダムに選ばれた質問をフロントエンドに送信するエンドポイント ------
@app.route('/get_random_question', methods=['GET'])
def get_random_question():
    print("get_random_question called")  # get_ramdom_question()関数が呼び出されてるか確かめるプリント

    is_reload = request.headers.get('X-Reload') == 'true'

    # quiz_rangeが設定されていない場合、エラーを返す
    if 'quiz_range' not in session or session['quiz_range'] is None:
        return jsonify({'error': '出題範囲が設定されていません。ホーム画面に戻ってください。'}), 400    

    # セッションに保存された現在の質問をチェック
    current_question = session.get('current_question')

    # if current_question:
    #     # セッションに保存された質問がある場合、JSONとしてパースしてから返す
    #     return jsonify(json.loads(current_question))
    
    
    if is_reload and current_question:
        # リロード時は現在の質問を再利用
        return jsonify(json.loads(session['current_question']))    
    
    # セッションに保存された出題範囲を取得
    quiz_range = session.get('quiz_range')
    app.logger.info(f"Current quiz range: {quiz_range}") # 現在設定されているクイズ範囲を出力
    if not quiz_range:
        return jsonify({'error': '出題範囲が設定されていません。'}), 400

     # quiz_rangeに基づいて質問をフィルタリング
    filtered_questions = [q for q in questions if q['category'] == quiz_range]

    if not filtered_questions:
        return jsonify({'error': '選択された範囲の問題が見つかりません。'}), 404


    # 未回答の質問を取得
    # セッションからanswered_questionsリストを取得しそのうちのquestion_idのみ取り出してsetに変換
    # session.get('answered_questions', [])は、answered_questionsキーが存在しない場合に
    # 空リストを返すようになっている
    answered_question_ids = set(aq['question_id'] for aq in session.get('answered_questions', []))
    # questionsリストから、question_idがanswered_question_idsセットに含まれないものだけを抽出
    # して、unanswered_questionsリストを作成
    unanswered_questions = [q for q in filtered_questions if q['id'] not in answered_question_ids]
    
    # 未回答の質問がない場合クイズ終了。問題数がデータ数を上回った場合に出力される
    if not unanswered_questions:
        return jsonify({'error': 'No more questions'}), 404

     # 未回答の質問からランダムに選択
    random_question = random.choice(unanswered_questions)

    # 選択肢をランダムに並び替える
    random.shuffle(random_question['choices'])

    # 現在の質問インデックスを更新
    current_index = session.get('current_question_index', 0)
    next_index = current_index + 1

    # 現在の質問をセッションに保存
    session['current_question'] = json.dumps({
        'id': random_question['id'],
        'question': {'text': random_question['text']},
        'image': random_question['image'],
        'choices': random_question['choices'],
        'next_index': next_index,
        'answered_questions': session.get('answered_questions', []),
        'total_questions': len(filtered_questions)
    }, ensure_ascii=False)
    session['current_question_index'] = current_index  # 現在のインデックスを保存
    session.modified = True

    # 現在の質問データがセッションに保存されたことをターミナルログに表示
    app.logger.info(f"Current question data saved to session: {random_question['id']}")
    app.logger.info(f"Current question data saved to session: {random_question['text']}")

    # セッションに保存したデータをJSONとしてパースしてから返す
    return jsonify(json.loads(session['current_question']))

# ------ POSTリクエストでユーザーの回答を処理するエンドポイント ------
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    try:
        # リクエストデータをロギング
        data = request.json
        # 整数型：question_id
        question_id = data['questionId']
        app.logger.debug('Received data: %s', data)
        # print('question_id in submit_answer:', question_id)
        # 解答済みの質問数を増分
        # session['answered_question_count'] += 1
        
            # 既存のコード
        session['answered_question_count'] = session.get('answered_question_count', 0) + 1
            # 残りのコード

        # questionIdの値が適切か確認するデバックプリント
        # print(f"Received questionId: {question_id}, type: {type(question_id)}")

        # データ型確認
        if not isinstance(question_id, int):
            # エラー処理
            return jsonify({'error': 'Invalid data type question_id'}), 400


        # questionIdがquestions配列のインデックス範囲内にあるか検証する
        if question_id not in [q['id'] for q in questions]:
            return jsonify({'error': 'questionId is out of range'}), 400

        # セッション内容を出力
        app.logger.debug(session)


        # jsで定義したグローバル変数を割り当てるキー名
        # 整数型：active_choice_id
        active_choice_id = data.get('activeChoice', None)
        # choiceIdの値が適切か確認するデバックプリント
        # print(f"Received activeChoiceId: {active_choice_id}, type: {type(active_choice_id)}")
        if active_choice_id is None:
            current_app.logger.error('activeChoice key is missing in the request data')
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
        # print(f"Updated answered_questions: {session['answered_questions']}")  

        quiz_range = session.get('quiz_range')
        filtered_questions = [q for q in questions if q['category'] == quiz_range]
        # クイズの終了条件を判定
        # session['answered_questions']を使うことで実際に表示された質問数
        is_quiz_finished = session['answered_question_count'] >= len(filtered_questions)

        # 現在の質問インデックスを更新
        session['current_question_index'] = session.get('current_question_index', 0) + 1

        # クイズが終了していない場合、次の質問のインデックスを保存
        if not is_quiz_finished:
            next_question = get_random_question()
            session['current_question'] = next_question.get_data(as_text=True)
            session.modified = True # セッションが変更されたことをFlaskに通知

        # 解説文をUTF-8でエンコード
        encoded_explanation = json.dumps(question['explanation'], ensure_ascii=False)
                        
        # 結果と解説の返送
        response_data = {
            'result': result, 
            'explanation': encoded_explanation, 
            'correct_answers': session['correct_answers'],
            'isQuizFinished': is_quiz_finished,
            'currrent_question_index': session['current_question_index'],
            'success': True
        }

        # レスポンスデータをデバッグログに出力
        app.logger.debug(f"response_data: {response_data}")
        for key, value in response_data.items():
            app.logger.debug(f"{key}: {type(value)}")

        # JSONレスポンスを返す
        return jsonify(response_data), 200            

        # レスポンスデータ全体をJSONエンコード
        # encoded_response = json.dumps(response_data, ensure_ascii=False), 200

        # エンコードされたデータをレスポンスとして返す
        # return Response(encoded_response, content_type='application/json; charset=utf-8')
    
    except KeyError as e:
        app.logger.error(f"KeyError in submit_answer: {str(e)}")
        return jsonify({'error': str(e), 'success':False}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error in submit_answer: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    



# ------ 結果画面のhtmlファイルをレンダリングするためのルートハンドラー ------
@app.route('/result')
def result():
    # answered_questionsの構造を確認
    #print(f"answered_questions in session: {session.get('answered_questions', [])}")

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
            if user_answer is None:
                continue  # user_answerがNoneの場合はスキップ
            # ユーザーが選んだ選択肢の文章を格納するキーをまだ設定していなかったので新たに作成し、
            # これに文章を格納する
            # ユーザーが選んだ選択肢の文章を取得
            user_choice_text = next((c['text'] for c in question['choices'] if c['id'] == user_answer['user_choice']), 'Unknown')
            # 画像の情報を取得
            image_url = question.get('image', '')
            # 画像パスから /static/ を削除。これにより、結果画面に画像を表示させる際にパスが正しく設定され画像表示される
            if image_url.startswith('static/'):
                image_url = image_url[len('static/'):]
            answered_question_info = {
                'text': question['text'],
                'image': image_url,
                'user_choice_text': user_choice_text,
                'explanation': next((q['explanation'] for q in session.get('answered_questions', []) if q['question_id'] == question['id']), question['explanation']),
                'display_order': user_answer['display_order'] + 1  # 表示順序を1から始めるよう修正
            }
            answered_questions_info.append(answered_question_info)

            # answered_questions_infoが存在しない場合のエラーハンドリング
            if not answered_questions_info:
                return "No questions have been answered.", 400

        except (TypeError, KeyError) as e:
            print(f"Error occurred: {str(e)}")
            print(f"question object: {question}")
            raise e

    # セッションから正答数を取得
    correct_answers = session.get('correct_answers', 0)
    # セッションからフィルタリングされた質問の総数を取得
    total_questions = session.get('total_questions', 0)

    # セッション内容を出力
    app.logger.debug(session)

    # 表示順序に基づいて answered_questions_info をソート
    answered_questions_info.sort(key=lambda q: q['display_order'])
    
    # result.htmlに正答数と総問題数を渡す
    return render_template('result.html', correct=correct_answers, total=total_questions, answered_questions=answered_questions_info)



# ------ クイズをリセットするエンドポイント ------

# リスタートボタンとホームに戻るボタンが共通で使用する、引数と条件分岐付きの関数
def reset_quiz(keep_quiz_range=False):
    keys_to_keep = ['quiz_range', 'total_questions'] if keep_quiz_range else []
    for key in list(session.keys()):
        if key not in keys_to_keep:
            session.pop(key, None)
    session.modified = True

# リスタートボタンが呼び出すエンドポイント、ここでは変数"keep__quiz_range"に保存された値を使う前提でreset_quiz()関数を呼び出す
@app.route('/reset_quiz', methods=['POST'])
def reset_quiz_route():
    try:
        keep_quiz_range = request.json.get('keep_quiz_range', False)
        reset_quiz(keep_quiz_range)
        return jsonify({'status': 'success', 'message': 'Quiz reset successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error in reset_quiz: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500        

# リセットボタンが呼び出すエンドポイント、ここでは変数"keep__quiz_range"に保存された値を使わない前提でreset_quiz()関数を呼び出す
@app.route('/reset_all', methods=['POST'])
def reset_all_route():
    # reset_all()関数が呼び出されてるか確かめるプリント
    # print("reset_all called", request.headers.get('X-Reload'))
    try:
        print('reload was executed. X-Reload:', request.headers.get('X-Reload'))
        is_reload = request.headers.get('X-Reload') == 'true'
        if not is_reload:
            # リロードでない場合のみセッションをリセット
            print("session all clear was executed")
            reset_quiz(keep_quiz_range=False)
        return jsonify({'status': 'success', 'message': 'All session data reset successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error in reset_all: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# スクリプトが直接実行された場合にアプリケーションが開始
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
# 開発中は引数に"debug=True"を指定しておくと、
# アプリの再起動なしでコードの変更を即座に反映できる。