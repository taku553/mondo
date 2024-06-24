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
  
    // ボタン要素を取得
    var button = document.getElementById('start_b_f');

    // リセットボタンのイベントリスナー
  document.getElementById('start_b_f').addEventListener('click', function() {
    // クイズをリセットする関数を呼び出す
    resetQuiz();
  });

    // ボタンがクリックされたときのイベントリスナーを追加
    button.addEventListener('click', function() {
        // ここでページ遷移を実行
        window.location.href = '/quiz';  // 遷移先のURLを指定
    });

});



// クイズをリセットする関数
function resetQuiz() {
  fetch('http://127.0.0.1:5000/reset_quiz')
      .then(response => response.json())
      .then(data => {
          console.log(data.status); // リセットのステータスをログ出力
          // ここで必要に応じてクライアント側の状態もリセットする
          // ページをリロードするか、ホームにリダイレクトするなど
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