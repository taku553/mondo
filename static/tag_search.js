// tag_search.js

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
    // URLからタグパラメータを取得
    const urlParams = new URLSearchParams(window.location.search);
    const tag = urlParams.get('tag');
    
    // 現在のタグ名を表示
    document.getElementById('current-tag').textContent = tag;
    
    // 検索結果ページ内のタグクリックイベント
    document.querySelectorAll('.tag').forEach(tag => {
        tag.addEventListener('click', function(e) {
            e.preventDefault();
            const tagName = this.textContent.trim();
            window.location.href = `/tag_search?tag=${encodeURIComponent(tagName)}`;
        });
    });    
        
    // gridContainerのセレクタを.gridに変更
    const gridContainer = document.querySelector('.grid');
    // gridContainerが存在する場合のみ処理を実行
    if (gridContainer) {
        const cards = gridContainer.querySelectorAll('.card');
        const itemsPerPage = 8;
        let currentPage = 1;
        
        function showPage(page) {
            const start = (page - 1) * itemsPerPage;
            const end = start + itemsPerPage;
            
            cards.forEach((card, index) => {
                card.style.display = (index >= start && index < end) ? '' : 'none';
            });
            
            updatePagination();
            // ページ上部にスクロール
            window.scrollTo(0, 0);        
        }
        
        function updatePagination() {
            const totalPages = Math.ceil(cards.length / itemsPerPage);
            const paginationContainer = document.getElementById('tag-pagination');
            paginationContainer.innerHTML = '';
            
            if (totalPages > 1) {  // ページが2以上ある場合のみページネーションを表示
                // 「前へ」ボタン
                if (currentPage > 1) {
                    const prevButton = document.createElement('button');
                    prevButton.textContent = '前へ';
                    prevButton.onclick = () => {
                        currentPage--;
                        showPage(currentPage);
                    };
                    paginationContainer.appendChild(prevButton);
                }
                
                // ページ番号
                for (let i = 1; i <= totalPages; i++) {
                    const button = document.createElement('button');
                    button.textContent = i;
                    button.className = i === currentPage ? 'active' : '';
                    button.onclick = () => {
                        currentPage = i;
                        showPage(i);
                    };
                    paginationContainer.appendChild(button);
                }
                
                // 「次へ」ボタン
                if (currentPage < totalPages) {
                    const nextButton = document.createElement('button');
                    nextButton.textContent = '次へ';
                    nextButton.onclick = () => {
                        currentPage++;
                        showPage(currentPage);
                    };
                    paginationContainer.appendChild(nextButton);
                }
            }
        }
        
        // 初期表示
        if(cards.length > 0) {
            showPage(1);
        }
    }

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