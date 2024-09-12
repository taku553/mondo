// 結果画面のスクリプト result.js

// アプリケーションのベースURLを定義
const BASE_URL = window.location.origin;

// ページがロードされたらイベントリスナーを追加する
document.addEventListener('DOMContentLoaded', function() {
    // リセットボタンのイベントリスナー
    document.getElementById('restart_b').addEventListener('click', function() {
        // クイズをリセットする関数を呼び出す。リセットに成功したらホーム画面にリダイレクトする
        resetQuiz(true, () => {
            //Javascriptでクイズ画面にリダイレクト
            window.location.href = '/quiz';
        });
    });

    // ホームに戻るボタンのイベントリスナー
    document.getElementById('home_b').addEventListener('click', function() {
        // クイズデータをリセットし、ホームにリダイレクト
        resetAll(() => {
            // ホーム画面にリダイレクト
            window.location.href = '/';
        });

    });


    // 結果画面の問題番号を取得し、ログ出力する
    logQuestionNumbers();
});


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

// 問題番号をログ出力する関数
function logQuestionNumbers() {
    const questionNumberElements = document.querySelectorAll('.question-order');
    questionNumberElements.forEach(function(element) {
        const questionNumber = element.textContent.trim().replace('第', '').replace('問', '');
        console.log('結果画面の問題番号:', questionNumber);
    });
}