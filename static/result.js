// 結果画面のスクリプト result.js


// アプリケーションのベースURLを定義
const BASE_URL = window.location.origin;

// 意図的なページ離脱（リセットやホームに戻る、リロード・アンロードなど、true）と、ブラウザを閉じるなどの意図しない離脱（false）を区別するフラグ
// ファイルの先頭付近に追加
let isQuitting = false;

// リロード検出するフラグ（リロード：true、リロードではない：false）
let isReloading = false;

// ページロード時に isReloading フラグを設定
window.addEventListener('load', () => {
    const [navigationEntry] = performance.getEntriesByType('navigation');
    isReloading = navigationEntry && navigationEntry.type === 'reload';
    handlePageLoad();
});


// ------------------------- 各種関数 -------------------------

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


// ページが実際にアンロードされるときに呼び出される関数
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
    if (isReloading) {
        console.log('This page is reloaded');
        // リロード時にセッションを保持するリクエストを送信
        fetch(`${BASE_URL}/keep_session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Reload': 'true'
            },
            body: JSON.stringify({})
        }).then(response => {
            if(!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        }).then(data => {
            // ここで必要に応じて結果を再表示する処理を行う
            console.log('セッションの保持に成功しました:', data);
        }).catch(error => {
            // エラー時の処理;
            console.error('セッションの保持に失敗しました:', error);
        });
    }
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

// 問題番号をログ出力する関数
function logQuestionNumbers() {
    const questionNumberElements = document.querySelectorAll('.question-order');
    questionNumberElements.forEach(function(element) {
        const questionNumber = element.textContent.trim().replace('第', '').replace('問', '');
        console.log('結果画面の問題番号:', questionNumber);
    });
}



// DOMContentLoaded イベントリスナーを最後に配置
// 質問画面表示のタイミングでDOMコンテンツを読み込むイベントリスナー
document.addEventListener('DOMContentLoaded', () => {

    // ページロード時に実行される関数
    //handlePageLoad();

    // ページがロードされたらイベントリスナーを追加する
    // リセットボタンのイベントリスナー
    document.getElementById('restart_b').addEventListener('click', async function(event) {
        event.preventDefault(); // デフォルトの動作をキャンセル
        isQuitting = true;  // 意図的なナビゲーションを示すフラグをセット        
        try {
            // TypeScriptの型チェックにより'await'不要の提案。動作に問題はないので無視。
            window.onbeforeunload = null; // beforeunloadイベントハンドラーを解除
            const url = await resetQuiz(true);
            window.location.href = url;
        } catch (error) {
            console.error('クイズのリセットに失敗しました:', error);
            isQuitting = false;  // エラーが発生した場合、フラグをリセット
        }
    });

    // ホームに戻るボタンのイベントリスナー
    document.getElementById('home_b').addEventListener('click', async function(event) {
        event.preventDefault(); // デフォルトの動作をキャンセル
        isQuitting = true;  // 意図的なナビゲーションを示すフラグをセット        
        try {
            // TypeScriptの型チェックにより'await'不要の提案。動作に問題はないので無視。
            const url = await resetAll();
            window.onbeforeunload = null; // beforeunloadイベントハンドラーを解除
            window.location.href = url;
        } catch (error) {
            console.error('全セッションデータのリセットに失敗しました:', error);
            isQuitting = false;  // エラーが発生した場合、フラグをリセット
        }
    });
    // 問題番号をログ出力する関数の呼び出し
    logQuestionNumbers();
});