// quiz_info.js

// アプリケーションのベースURLを定義
const BASE_URL = window.location.origin;

// 意図的なページ離脱（リセットやホームに戻る）と、ブラウザを閉じるなどの意図しない離脱を区別するフラグ
// ファイルの先頭付近に追加
let isQuitting = false;

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


document.addEventListener('DOMContentLoaded', function() {
    // タグクリックイベント (quiz_info.html用)
    document.querySelectorAll('.detail-tag').forEach(tag => {
        tag.addEventListener('click', function(e) {
            e.preventDefault();
            const tagName = this.textContent.trim();
            window.location.href = `/tag_search?tag=${encodeURIComponent(tagName)}`;
        });
    });

    // スタートボタンの要素を取得
    const detailStartButton = document.getElementById('q_info_start_b');

    // スタートボタンのクリックイベントリスナー
    detailStartButton.addEventListener('click', function(e) {
        e.preventDefault();
        
        // 非表示のセレクト要素から値を取得
        var selectedRange = document.getElementById('quiz_range').value;
        
        // 既存のスタートボタンのロジックを再利用
        $.ajax({
            url: `${window.location.origin}/set_quiz_range`,
            method: 'POST',
            data: JSON.stringify({ range: selectedRange }),
            contentType: 'application/json',
            success: function(response) {
                if (response.status === 'success') {
                    window.location.href = '/quiz';
                } else {
                    alert('出題範囲の設定に失敗しました。もう一度お試しください。');
                }
            },
            error: function() {
                alert('サーバーとの通信に失敗しました。もう一度お試しください。');
            }
        });
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