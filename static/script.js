// ホーム画面のスクリプト script.js

// 意図的なページ離脱（リセットやホームに戻る）と、ブラウザを閉じるなどの意図しない離脱を区別するフラグ
// ファイルの先頭付近に追加
let isQuitting = false;

// アプリケーションのベースURLを定義
const BASE_URL = window.location.origin;


// ページがアンロードされる直前に呼び出される関数
//function handleBeforeUnload(event) {
//  if (!isQuitting) {
//      const message = 'ページを離れると、現在のセッションデータが失われます。よろしいですか？';
//      event.preventDefault(); // 標準の動作をキャンセル
//      event.returnValue = message; // Chrome用
//      return message; // 他のブラウザ用
//  }
//}

// ページが実際にアンロードされるときに呼び出される関数
function handleUnload() {
  console.log('handleUnload called');
  if (!isQuitting) {
      navigator.sendBeacon(`${BASE_URL}/reset_all`, JSON.stringify({}));
  }
}

// イベントリスナーを設定
//window.addEventListener('beforeunload', handleBeforeUnload);
window.addEventListener('unload', handleUnload);


// ページが実際にアンロードされるときに呼び出される関数
function resetAll() {
  console.log('handleUnload called');
  if (!isQuitting) {
      navigator.sendBeacon(`${BASE_URL}/reset_all`, JSON.stringify({}));
  }
}

// ページ遷移のスクリプト
document.addEventListener('DOMContentLoaded', function() {
  //ホーム画面ロード時にリセット処理を行う。
  resetAll();

  // ドロップダウンメニューによる通信
  //Secect2の初期化
  $('.js-example-basic-single').select2({
    width: 'calc(7em + 6vw)', // または '100%' など、任意の値を設定
    minimumResultsForSearch: Infinity, // 検索ボックスを非表示
    containerCssClass: 'custom-select2-container',
    dropdownCssClass: 'custom-select2-dropdown'      
    // 必要に応じて追加のオプションを設定
  });

  // タグクリックイベント (index.html用)
  document.querySelectorAll('.tag').forEach(tag => {
    tag.addEventListener('click', function(e) {
        e.preventDefault();
        const tagName = this.textContent.trim();
        window.location.href = `/tag_search?tag=${encodeURIComponent(tagName)}`;
    });
  });  

  // スタートボタンのイベントリスナー
  $('#start_b_f').on('click', function(e) {
      e.preventDefault();
      isQuitting = true;  // 意図的なナビゲーションを示すフラグをセット
      var selectedRange = $('#quiz_range').val();
      if (!selectedRange) {
          alert('出題範囲を選択してください。');
          return;
      }
      // 選択された範囲をサーバーに送信
      $.ajax({
          url: `${BASE_URL}/set_quiz_range`,
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
});



//ポップアップを切り替えるためのスクリプト
// モーダルを取得
var popup = document.getElementById("popup");

// モーダルを開くボタンを取得
var btn = document.getElementById("howto_button");

// モーダルを閉じるspan要素を取得
var span = document.getElementsByClassName("close")[0];

// ユーザーがボタンをクリックすると、モーダルが開く
btn.onclick = function() {
    popup.style.display = "block";
}

// ユーザーが <span> (x) をクリックすると、モーダルが閉じる
span.onclick = function() {
    popup.style.display = "none";
}

// ユーザーがモーダルの外側をクリックするとモーダルを閉じる
window.onclick = function(event) {
    if (event.target == popup) {
        popup.style.display = "none";
    }
}

// スライド
$(document).ready(function(){
    var currentSlide = 0;
    var slides = $('.slide');
    var dots = $('.dot');
  
    function changeSlide(newSlide){
      var slideWidth = slides.width();
      slides.eq(currentSlide).animate({left: -slideWidth}, 200, 'easeOutQuad', function() {
        $(this).removeClass('active').css('left', '');
        dots.eq(currentSlide).removeClass('active');
        slides.eq(newSlide).css('left', slideWidth).addClass('active').animate({left: 0}, 500, 'easeOutQuad');
        dots.eq(newSlide).addClass('active');
        currentSlide = newSlide;
      });
    }
  
    $('.next').click(function(){
      var newSlide = (currentSlide + 1) % slides.length;
      changeSlide(newSlide);
    });
  
    $('.prev').click(function(){
      var newSlide = (currentSlide - 1 + slides.length) % slides.length;
      changeSlide(newSlide);
    });
  
    $('.dot').click(function(){
      var index = $(this).index();
      changeSlide(index);
    });
  });

// タグ検索の実装
const searchBox = document.querySelector('.search-box');
const cards = document.querySelectorAll('.card');

if (searchBox) {
  searchBox.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase().trim();
    
    cards.forEach(card => {
      const tags = Array.from(card.querySelectorAll('.tag'))
        .map(tag => tag.textContent.toLowerCase().trim());
      
      if (searchTerm === '' || tags.some(tag => tag.includes(searchTerm))) {
        card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });
  });
}

// ページネーション機能
const paginationButtons = document.querySelectorAll('.pagination button');

paginationButtons.forEach(button => {
    button.addEventListener('click', () => {
        paginationButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        // ここにページ切り替えのロジックを追加
    });
});