// result.js

// ページがロードされたらイベントリスナーを追加する
document.addEventListener('DOMContentLoaded', function() {
    // リセットボタンのイベントリスナー
    document.getElementById('restart_b').addEventListener('click', function() {
        // クイズをリセットする関数を呼び出す。リセットに成功したらホーム画面にリダイレクトする
        resetQuiz(() => {
            //Javascriptでクイズ画面にリダイレクト
            window.location.href = '/quiz';
        });
    });

    // ホームに戻るボタンのイベントリスナー
    document.getElementById('home_b').addEventListener('click', function() {
        // クイズデータをリセットし、ホームにリダイレクト
        resetQuiz(() => {
            // ホーム画面にリダイレクト
            window.location.href = '/';
        });

    });


    // 結果画面の問題番号を取得し、ログ出力する
    logQuestionNumbers();
});

// 問題番号をログ出力する関数
function logQuestionNumbers() {
    const questionNumberElements = document.querySelectorAll('.question-order');
    questionNumberElements.forEach(function(element) {
        const questionNumber = element.textContent.trim().replace('第', '').replace('問', '');
        console.log('結果画面の問題番号:', questionNumber);
    });
}


// クイズをリセットする関数
function resetQuiz(callback) {
    fetch('http://127.0.0.1:5000/reset_quiz')
        .then(response => response.json())
        .then(data => {
            console.log(data.status); // リセットのステータスをログ出力
            callback();
            
        })
        .catch(error => console.error('クイズのリセット中にエラー:', error));
}