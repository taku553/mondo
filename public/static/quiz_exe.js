// ページリロード後の処理を解決したjsファイルのソースコード
// クイズ画面のスクリプト quiz_exe.js

// アプリケーションのベースURLを定義
const BASE_URL = window.location.origin;

// アクティブな選択肢を保持する変数（グローバルスコープで宣言）
let choiceId = null;

/* グローバルスコープでtotalQuestionsを宣言。
totalQuestionsの値をsubmitAnswer関数の外部から取得した後にtotal_questionsを保存し、
submitAnswer関数で使用させるのが目的 */
let totalQuestions;

let currentQuestionIndex = 0;  // グローバルスコープで宣言し、初期値を0に設定
// ページロード時に一度だけ要素を取得してグローバル変数に保存
let nextButton;

// 意図的なページ離脱（リセットやホームに戻る）と、ブラウザを閉じるなどの意図しない離脱を区別するフラグ
// ファイルの先頭付近に追加
let isQuitting = false;

// リロード検出するフラグ
let isReloading = false;

// ページロード時に isReloading フラグを設定
window.addEventListener('load', () => {
    const [navigationEntry] = performance.getEntriesByType('navigation');
    isReloading = navigationEntry && navigationEntry.type === 'reload';
});

    // --------- 各種関数 ---------

// 非同期処理を開始する前にロード状態を表す
function setLoadingState(isLoading) {
    const choices = document.querySelectorAll('.choice');
    choices.forEach(choice => {
        if (isLoading) {
            choice.classList.add('loading');
        } else {
            choice.classList.remove('loading');
        }
    });
}

// 条件に基づいて特定の選択肢を無効化する
function setDisabledState(choiceElement, isDisabled) {
    if (isDisabled) {
        choiceElement.classList.add('disabled');
    } else {
        choiceElement.classList.remove('disabled');
    }
}

// セッション有効性をチェックする関数
async function checkSessionValidity() {
    try {
        const response = await fetch(`${BASE_URL}/check_session`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (!data.valid) {
            // セッションが無効な場合の処理
            showSessionExpiredMessage();
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('セッション確認中にエラーが発生しました:', error);
        return false;
    }
}

// セッション切れメッセージを表示する関数
function showSessionExpiredMessage() {
    // バックドロップとポップアップを作成
    const backdrop = document.createElement('div');
    backdrop.classList.add('session-expired-backdrop');
    document.body.appendChild(backdrop);

    const popup = document.createElement('div');
    popup.classList.add('session-expired-popup');

    const messageElement = document.createElement('p');
    messageElement.innerHTML = 'セッションの有効期限が切れました。<br>再度クイズを開始するにはホームに戻ってください。';
    messageElement.className = 'error-message';
    popup.appendChild(messageElement);

    // ホームに戻るボタン
    const homeButton = document.createElement('button');
    homeButton.id = 'session-expired-home-button';
    homeButton.addEventListener('click', () => {
        isQuitting = true;  // 意図的なナビゲーションを示すフラグをセット
        window.onbeforeunload = null; // beforeunloadイベントハンドラーを解除
        window.location.href = '/'; // ホームページにリダイレクト
    });
    
    const homeTextElement = document.createElement('span');
    homeTextElement.textContent = 'ホームに戻る';
    homeTextElement.className = 'session-confirm-b-f';
    homeButton.appendChild(homeTextElement);

    popup.appendChild(homeButton);
    document.body.appendChild(popup);

    // デバッグ用ログ
    console.log('セッション切れメッセージを表示しました');    
}



// 1. 問題データの取得と表示：
// 非同期リクエストで問題をサーバーから取得し、結果を関数"displayQuestion"に渡す関数
// 非同期関数として修正
async function getAndDisplayQuestion() {
    console.log('getAndDisplayQuestion called'); // 呼び出しの確認用ログ

    // セッション有効性チェックを追加
    if (!await checkSessionValidity()) {
        return; // セッションが無効な場合は処理を終了
    }

    setLoadingState(true);  // ローディング状態をonにする
    try {
        // サーバー（Flaskを使用）から問題データを取得するための非同期リクエスト
        // Flaskサーバーから問題データを取得。'/get_question'エンドポイントにHTTP GETリクエストを非同期で送信
        const response  = await fetch(`${BASE_URL}/get_random_question`, {
            method: 'GET',
            headers: {
                'X-Reload': isReloading ? 'true' : 'false'
            }
        });
        const data = await handleResponse(response);
        
        if(data.error) {
            throw new Error(data.error);
        }

        // question_idの値が正しく取得されてるか確認するデバッグプリントを追加
        console.log(`question_id: ${data.id}`);
        // クイズ開始時に問題総数を保存
        totalQuestions = data.total_questions_index;
        // 問題を画面に表示、セッションに保存された質問があればそれを使用する
        if (data.current_question) {
            displayQuestion(data.current_question);
        } else {
            displayQuestion(data);
        }
    // エラーが発生した場合にコンソールにエラーメッセージを表示
    } catch (error) {
        console.error('問題を取得中にエラーが発生しました:', error);
        // "No more questions"エラーの場合は結果ページにリダイレクト
        if (error.message.includes("No more questions")) {
            window.location.href = '/result';
        }
    } finally {
        setLoadingState(false); // ローディング状態をoffにする
    }   
}

// HTTPレスポンスの処理を担当する関数
function handleResponse(response) {
    if (!response.ok) throw new Error('ネットワークレスポンスは正常ではありませんでした');
    return response.json();
}

// 2. 問題文と選択肢を表示する関数
function displayQuestion(questionData) {
    // デバッグ用のログ
    console.log("Received question data:", questionData);
    // サーバーからの現在の問題インデックスを取得して更新
    if (questionData.next_index !== undefined) {
        currentQuestionIndex = parseInt(questionData.next_index, 10);
    }
    console.log(`currentQuestionIndex: ${currentQuestionIndex}`);

    setLoadingState(false); // ローディング状態をoffにする
    // データ形式と必要なフィールドの検証
    if (!questionData.question || !questionData.choices) {
        console.error('不正なデータ形式:', questionData);
        return;
    }

    // 問題データの要素、選択肢のコンテナ要素、問題数の要素を取得
    const imageContainer = document.getElementById('image_container'); // 画像コンテナ要素を取得
    const questionElement = document.getElementById('question');
    const choicesContainer = document.getElementById('choices_container');
    const questionNumberElement = document.getElementById('current-question-number');

    if (!questionElement || !choicesContainer) {
        console.error('必要な要素がDOMに見つかりません');
        return;
    }

    // 問題文の表示
    questionElement.textContent = questionData.question.text;
    // 画像の表示
    if (questionData.image) {
        const imgElement = document.createElement('img');
        imgElement.className = 'question-image';
        imgElement.src = questionData.image;
        imgElement.alt = 'Question Image';
        imageContainer.innerHTML = ''; // 既存の画像をクリア
        imageContainer.appendChild(imgElement);
    } else {
        imageContainer.innerHTML = ''; // 画像がない場合はクリア
    }
    // 質問IDの設定
    questionElement.setAttribute('data-question-id', questionData.id);
    // 既存の選択肢をクリア
    choicesContainer.innerHTML = ''; 
    // 現在の問題数を表示
    questionNumberElement.textContent = `第${currentQuestionIndex}問`;


    // displayQuestion で forEach ループを使用して選択肢要素を作成
    questionData.choices.forEach((choice, index) => {
        if ( choice.id === null || choice.text === 'undefined') {
            console.error('不完全な選択肢データ:', choice);
            return;
        }

        const choiceElement = createChoiceElement(choice, index);
        choicesContainer.appendChild(choiceElement);
    });

    // choiceId をリセット
    choiceId = null;

    // データが全て適用されたら、bodyのhidden属性を削除して表示
    document.body.hidden = false;
}

// 各選択肢をコンテナに追加し、イベントリスナーを設定
// 四つの選択肢それぞれに直接イベントリスナーを追加するためのスクリプト
function createChoiceElement(choice, index) {  // 取得した選択肢データを繰り返し処理
    const choiceElement = document.createElement('div');  // 選択肢を表示するための新しいdiv要素を作成
    choiceElement.id = `choice-${index}`; // 一意のIDを設定
    choiceElement.classList.add('choice');  // 作成したdiv要素に'choice'というクラスを追加（スタイリングのため）

    // 選択肢テキストの文字数制限を適用する
    const maxTextLength = 5;
    let displayText = choice.text;
    if (displayText.length > maxTextLength) {
        displayText = displayText.substring(0, maxTextLength) + '...';
    }

    choiceElement.textContent = `${index + 1}. ${displayText}`;  // 選択肢のテキストを設定
    choiceElement.setAttribute('data-choice-id', choice.id);  // 順序番号を設定
    // クリックされたときのイベントリスナーを追加
    choiceElement.addEventListener('click', function() {
        // クリックが可能な状態かを判断する
        if (this.classList.contains('loading') || this.classList.contains('disabled')) {
            console.error('選択肢は現在クリック不可能です');
            return; // クリック不可能な場合は処理を中断する
        }

        // ここではアクティブ状態の変更を行わず、ポップアップを表示する
        showChoicePopup(choice.text, choice.id);  // ポップアップ表示関数を呼び出し
    });

    return choiceElement;
}



// ユーザーが選択肢をクリックしたときにポップアップを表示する関数
function showChoicePopup(choiceText, choiceId) {

    // ページの他の部分とのインタラクションを無効にするための背景を作成
    const backdrop = document.createElement('div');
    backdrop.classList.add('backdrop');
    backdrop.addEventListener('click', () => {
        document.body.removeChild(backdrop); // 背景がクリックされたら削除
        document.body.removeChild(popup); // ポップアップも削除
    });
    document.body.appendChild(backdrop);

    // ポップアップウィンドウの作成
    const popup = document.createElement('div');
    popup.classList.add('popup_window_q');
    // 選択肢のテキストを表示
    const choiceTextElement = document.createElement('p');
    choiceTextElement.textContent = choiceText;
    choiceTextElement.className = 'popup-choice-text'; // 選択肢内テキストのクラス名
    popup.appendChild(choiceTextElement);

    // ポップアップが正しく作成されたかチェック
    if (!popup) {
        console.error('ポップアップを作成できませんでした');
        return;
    }

    // ポップアップウィンドウを表示
    popup.style.display = 'block';

    // ポップアップウィンドウをDOMに追加
    document.body.appendChild(popup);

    // ポップアップがDOMに正しく追加されたかチェック
    if (!document.body.contains(popup)) {
        console.error('ポップアップをDOMに追加できませんでした');
        return;
    }


    // 「決定」ボタンのイベントリスナー
    const confirmButton = document.createElement('button');
    confirmButton.id = 'confirm-button'
    confirmButton.addEventListener('click', () => {
        // 選択した選択肢の色を変更してアクティブにする
        setActiveChoice(choiceId)
        backdrop.click(); // ポップアップを閉じる

        // ポップアップを閉じる
        popup.remove();
    });
    const confirmTextElement = document.createElement('span')
    confirmTextElement.textContent = '決定';
    confirmTextElement.className = 'confirm-b-f';
    confirmButton.appendChild(confirmTextElement);

    // ボタンをポップアップウィンドウに追加
    popup.appendChild(confirmButton);


    // ポップアップを適切な位置に配置
    popup.style.top = '30%';
    popup.style.left = '50%';
    popup.style.transform = 'translate(-50%, -50%)'; 
}


// 選択肢のアクティブ化
function setActiveChoice(selectedChoiceId) {
    const selectedChoiceElement = document.querySelector(`[data-choice-id="${selectedChoiceId}"]`);
    
    // 選択された選択肢がDOMに存在するかチェック
    if (!selectedChoiceElement) {
        console.error('選択された選択肢がDOMに存在しません。choiceId', selectedChoiceId);
        return;
    }
    // 選択された選択肢にactiveクラスが既にあるかどうかチェック
    if (selectedChoiceElement.classList.contains('active')) {
        console.error('この選択肢はすでにアクティブです。');
        return;
    }

    // 以前にアクティブだった選択肢のアクティブ状態を解除
    const previouslyActiveElement = document.querySelector('.choice.active');
    if (previouslyActiveElement) {
        previouslyActiveElement.classList.remove('active');
    }

    // 選択した選択肢の色を変更してアクティブにする
    selectedChoiceElement.classList.add('active');
    
    // 選択された選択肢のIDをグローバル変数に保存
    choiceId = selectedChoiceId;
}


// 「次へ」ボタンに解答データを送信するイベントリスナーを設定
async function handleNextButtonClick(event) {
    // 関数の呼び出しとchoiceIdの状態を確認するログ
    console.log('handleNextButtonClick called');
    console.log('choiceId:', choiceId);

    // デフォルトの動作（フォーム送信など）を防ぐ
    event.preventDefault();

    if (choiceId === null) {
        alert('選択肢が選ばれていません');
        return;
    }
    // 質問要素からquestionIdを取得
    const questionElement = document.getElementById('question');
    const questionId = questionElement.getAttribute('data-question-id');

    try {
        await submitAnswer(choiceId, nextButton, questionId);
    } catch (error) {
        console.error('解答の送信中にエラーが発生しました:', error);
        alert('解答の送信に失敗しました。ネットワークの接続を確認して、再度試してください。');
    }
}

// 解答データを送信するsubmitAnswer関数の定義、目的は解説文を正しく表示するため
async function submitAnswer(choiceId, nextButton, questionId) {
    // セッション有効性チェックを追加
    if (!await checkSessionValidity()) {
        return; // セッションが無効な場合は処理を終了
    }
    
    // questionIdを整数に変換
    const questionIdInt = parseInt(questionId, 10);

    console.log('questionId in submitAnswer:', questionIdInt, 'Type:', typeof questionIdInt);
    console.log('activeChoice in submitAnswer:', choiceId, 'Type:', typeof choiceId);
    try {
        const response = await fetch(`${BASE_URL}/submit_answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                questionId: questionIdInt,
                activeChoice: parseInt(choiceId),
            }),
        });

        if (!response.ok) {
            // response.okがfalseの場合、エラーメッセージを生成してthrow
            const errorText = await response.text(); // サーバーからのエラーテキストを取得
            console.error('Server error response:', errorText);
            throw new Error(`Server responded with ${response.status}: ${errorText}`);
        }

        // レスポンスの生データをログ出力
        const rawData = await response.text();
        console.log('Raw server response:', rawData);

        let data;
        try {
            data = JSON.parse(rawData);
        } catch (error) {
            console.error('Failed to parse server response:', error);
            throw new Error('Invalid JSON in server response');
        }

        console.log('Parsed server response:', data);


        // 次の問題へ移動、または結果画面へリダイレクト
        if (data.result) {
            // サーバーからのレスポンスでクイズの終了を確認
            if (data.isQuizFinished) {
                isQuitting = true;  // クイズ終了時にフラグを設定
                // beforeunloadイベント（ページリロード時の動作に関するイベントリスナー）を解除
                window.onbeforeunload = null;
                // 結果画面へリダイレクト
                window.location.href = '/result';
            } else {
                // 次の問題を表示する前に、選択状態をリセット
                choiceId = null;
                // awaitを使って次の問題が完全に読み込まれてから処理が続行されることを保証
                // 次の問題を表示する前に、次の問題インデックスを反映
                await getAndDisplayQuestion();
            }
        } else {
            console.error('Unexpected response from server:', data);
            alert('解答の処理中にエラーが発生しました。再度試してください。');
        }
    } catch (error) {
            console.error('解答の送信中にエラーが発生しました:', error);
            alert('解答の送信に失敗しました。再度試してください。'); // ユーザーに通知
            // ここで '次へ' ボタンの無効化を解除
            nextButton.disabled = false;
    }
}


// ページがアンロードされる直前に呼び出される関数
function handleBeforeUnload(event) {
    console.log('handleBeforeUnload called');
    if (!isQuitting) {
        const message = 'ページを離れると、現在のセッションデータが失われます。よろしいですか？';
        event.preventDefault(); // 標準の動作をキャンセル
        event.returnValue = message; // Chrome用
        return message; // 他のブラウザ用
    }
}


// ページアンロード時に実行される関数
function handleUnload() {
    isQuitting = true;
    console.log('handleUnload called');
    fetch(`${BASE_URL}/reset_all`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Reload': 'false'
        },
        body: JSON.stringify({})
    });

}



// イベントリスナーを設定
window.addEventListener('beforeunload', handleBeforeUnload);
window.addEventListener('unload', handleUnload);

// ページロード時に実行される関数
function handlePageLoad() {
    console.log('handlePageLoad called');

    // ページロード時にもセッション確認
    checkSessionValidity().then(isValid => {
        if (isValid) {    
            const [navigationEntry] = performance.getEntriesByType('navigation');
            if (navigationEntry && navigationEntry.type === 'reload') {
                isReloading = true;
                console.log('This page is reloaded');
                // リロード時にセッションを保持するリクエストを送信
                fetch(`${BASE_URL}/keep_session`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Reload': 'true'
                    },
                    body: JSON.stringify({})
                }).then(() => {
                    // セッションの保持が成功したら、質問を取得
                    getAndDisplayQuestion();
                }).catch(error => {
                    console.error('セッションの保持に失敗しました:', error);
                    // エラー時の処理（例：ホーム画面へリダイレクト）
                    window.location.href = '/';            
                }).finally(() => {
                    // 処理が完了したらフラグをリセット
                    isReloading = false;
                });
            } else {
                // 通常のページロード時は直接質問を取得
                getAndDisplayQuestion();
            }
        }
    });
}


// --------- リセット関数 ---------

// 出題範囲以外のセッションをリセットする関数。リスタートボタン用。
async function resetQuiz(keepQuizRange) {
    isQuitting = true;
    try {
        const response = await fetch(`${BASE_URL}/reset_quiz`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keep_quiz_range: keepQuizRange })
        });

        if (!response.ok) {
            throw new Error('サーバーエラー：' + response.status);
        }

        const data = await response.json();

        if (data.status === 'success') {
            // クイズ画面へのリダイレクト用のパスを返す
            return '/quiz';
        } else {
            throw new Error(data.message || 'クイズのリセットに失敗しました。');
        }
    } catch (error) {
        console.error('クイズのリセット中にエラー:', error);
        alert('クイズのリセット中にエラーが発生しました。ページをリロードして再度お試しください。');
        throw error;
    }
}

// 全てのセッションデータをリセットする関数。リセットボタン用。
async function resetAll() {
    console.log('resetAll called');
    isQuitting = true;
    try {
        const response  = await fetch(`${BASE_URL}/reset_all`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('サーバーエラー：' + response.status);
        }

        const data = await response.json();

        if (data.status === 'success') {
            // ホーム画面へのリダイレクト用のパスを返す
            return '/';
        } else {
            throw new Error(data.message || '全セッションデータのリセットに失敗しました。');
        }
    } catch (error) {
        console.error('全セッションデータのリセット中にエラー:', error);
        alert('全セッションデータのリセット中にエラーが発生しました。ページをリロードして再度お試しください。');
        throw error;
    }
}



// DOMContentLoaded イベントリスナーを最後に配置
/*質問画面表示のタイミングでDOMコンテンツを読み込むイベントリスナー
質問idを取得する関数"getAndDisplayQuestion()"と、「次へ」ボタン要素の取得、および
ボタンクリック時に解答データを送信する関数"handleNextButtonClick"をそれぞれ呼び出す役目を担う
*/
document.addEventListener('DOMContentLoaded', () => {
    nextButton = document.getElementById('next-button');  // ボタン要素を取得
    if (!nextButton) {
        console.error('Next button not found');
        return;
    }
    // '次へ'ボタンを有効化
    nextButton.disabled = false;
    
    // 次へボタンに直接イベントリスナーを設定
    nextButton.addEventListener('click', handleNextButtonClick);

    // ページのロード時に画面に表示される質問を取得・表示関数
    //getAndDisplayQuestion();

    // ページロード時に実行される関数
    handlePageLoad();

    // ページがロードされたらイベントリスナーを追加する
    // リセットボタンのイベントリスナー
    document.getElementById('q_window_restart_b').addEventListener('click', async function(event) {
        event.preventDefault(); // デフォルトの動作をキャンセル
        isQuitting = true;  // 意図的なナビゲーションを示すフラグをセット
        try {
            const url = await resetQuiz(true);
            window.onbeforeunload = null; // beforeunloadイベントハンドラーを解除
            window.location.href = url;
        } catch (error) {
            console.error('クイズのリセットに失敗しました:', error);
            isQuitting = false;  // エラーが発生した場合、フラグをリセット
        }
    });

    // ホームに戻るボタンのイベントリスナー
    document.getElementById('q_window_home_b').addEventListener('click', async function(event) {
        event.preventDefault(); // デフォルトの動作をキャンセル
        isQuitting = true;  // 意図的なナビゲーションを示すフラグをセット
        try {
            const url = await resetAll();
            window.onbeforeunload = null; // beforeunloadイベントハンドラーを解除
            window.location.href = url;
        } catch (error) {
            console.error('全セッションデータのリセットに失敗しました:', error);
            isQuitting = false;  // エラーが発生した場合、フラグをリセット
        }
    });

});