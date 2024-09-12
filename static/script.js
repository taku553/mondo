// ホーム画面のスクリプト script.js

// アプリケーションのベースURLを定義
const BASE_URL = window.location.origin;

// ページ遷移のスクリプト
document.addEventListener('DOMContentLoaded', function() {
  // フォントの読み込みエラーハンドリング
  document.fonts.load('12px "GenSekiGothic JP H"').then(function (fonts) {
    // フォントが正しく読み込まれたかを確認
    if (fonts.length === 0) {
      console.error('フォントが読み込めませんでした。');
      // ここでエラー処理を行う
    } else {
      console.log('フォントが正しく読み込まれました。');
    }
  }).catch(function (error) {
    console.error('フォントの読み込み中にエラーが発生しました:', error);
  });

  // ドロップダウンメニューによる通信
  //Secect2の初期化
  $('.js-example-basic-single').select2({
    width: 'calc(7em + 6vw)', // または '100%' など、任意の値を設定
    minimumResultsForSearch: Infinity, // 検索ボックスを非表示
    containerCssClass: 'custom-select2-container',
    dropdownCssClass: 'custom-select2-dropdown'      
    // 必要に応じて追加のオプションを設定
  });

  // スタートボタンのイベントリスナー
  $('#start_b_f').on('click', function(e) {
      e.preventDefault();
      var selectedRange = $('#quiz_range').val();
      if (!selectedRange) {
          alert('出題範囲を選択してください。');
          return;
      }

      //クイズをリセット
      // resetQuiz();

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



// クイズをリセットする関数
function resetQuiz() {
  fetch(`${BASE_URL}/reset_quiz`)
      .then(response => response.json())
      .then(data => {
          console.log(data.status); // リセットのステータスをログ出力
          // ここで必要に応じてクライアント側の状態もリセットする
          // ページをリロードするか、ホームにリダイレクトするなど
          // resetQuiz関数はホーム画面スタートボタンだけじゃなく結果画面の再挑戦ボタンでも使うので
          // /quizルートへ遷移する際は直前の出題範囲をそのまま使うようにしたい。そのための調整が必要。
          window.location.href = '/quiz';
      })
      .catch(error => console.error('クイズのリセット中にエラー:', error));
}


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

