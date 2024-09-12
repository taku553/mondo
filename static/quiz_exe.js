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


// 1. 問題データの取得と表示：
// 非同期リクエストで問題をサーバーから取得し、結果を関数"displayQuestion"に渡す関数
// 非同期関数として修正
async function getAndDisplayQuestion() {
    console.log('getAndDisplayQuestion called'); // 呼び出しの確認用ログ
    setLoadingState(true);  // ローディング状態をonにする
    try {
        // サーバー（Flaskを使用）から問題データを取得するための非同期リクエスト
        // Flaskサーバーから問題データを取得。'/get_question'エンドポイントにHTTP GETリクエストを非同期で送信
        const response  = await fetch(`${BASE_URL}/get_random_question`);
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
    const questionElement = document.getElementById('question');
    const choicesContainer = document.getElementById('choices_container');
    const questionNumberElement = document.getElementById('current-question-number');

    if (!questionElement || !choicesContainer) {
        console.error('必要な要素がDOMに見つかりません');
        return;
    }

    // 問題文の表示
    questionElement.textContent = questionData.question.text;
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
            const error = await response.text(); // サーバーからのエラーテキストを取得
            throw new Error(`Server responded with ${response.status}: ${error}`);
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

// クイズをリセットする関数
function resetQuiz(keepQuizRange, callback) {
    fetch(`${BASE_URL}/reset_quiz`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keep_quiz_range: keepQuizRange })
    }).then(response => {
        if (response.ok) {
            callback();
        }
    }).catch(error => console.error('クイズのリセット中にエラー:', error));
}

// 全てのセッションデータをリセットする関数
function resetAll(callback) {
    fetch(`${BASE_URL}/reset_all`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => {
        if (response.ok) {
            callback();
        }
    }).catch(error => console.error('全てのセッションデータのリセット中にエラー:', error));
}

// DOMContentLoaded イベントリスナーを最後に配置
/*質問画面表示のタイミングでDOMコンテンツを読み込むイベントリスナー
質問idを取得する関数"getAndDisplayQuestion()"と、「次へ」ボタン要素の取得、および
ボタンクリック時に解答データを送信する関数"setupNextButtonListener();"をそれぞれ呼び出す役目を担う
*/
document.addEventListener('DOMContentLoaded', () => {
    nextButton = document.getElementById('next-button');  // ボタン要素を取得
    // '次へ'ボタンを有効化
    nextButton.disabled = false;
    if (!nextButton) {
        console.error('Next button not found');
        return;
    }
    
    // 次へボタンに直接イベントリスナーを設定
    nextButton.addEventListener('click', handleNextButtonClick);

    // ページのロード時に画面に表示される質問を取得・表示関数
    getAndDisplayQuestion();

    // ページがロードされたらイベントリスナーを追加する
    // リセットボタンのイベントリスナー
    document.getElementById('q_window_restart_b').addEventListener('click', function() {
        // クイズをリセットする関数を呼び出す。リセットに成功したらホーム画面にリダイレクトする
        resetQuiz(true, () => {
            //Javascriptでクイズ画面にリダイレクト
            window.location.href = '/quiz';
        });
    });
    // ホームに戻るボタンのイベントリスナー
    document.getElementById('q_window_home_b').addEventListener('click', function() {
        // クイズデータをリセットし、ホームにリダイレクト
        resetAll(() => {
            // ホーム画面にリダイレクト
            window.location.href = '/';
        });

    });
});

/* ページリロードした時にブラウザからのデフォルトメッセージを表示させるイベントリスナー*/

// リロードボタンクリックおよびページ閉じる際に起動させるイベントリスナー
// リロードボタンクリック関数を起動させるイベントリスナー
window.onbeforeunload = function(event) {
    // メッセージを設定
    event.returnValue = 'ページをリロードすると、解答途中の質問から表示されます。'
    return event.returnValue;
};