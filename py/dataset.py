from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flaskアプリケーションとデータベースの設定
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
db = SQLAlchemy(app)

# Questionモデルの定義
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True) #主キー
    question_text = db.Column(db.String, nullable=False) #問題文を保存するカラム
    explanation = db.Column(db.String, nullable=True) #解説文を保存するカラム
    choices = db.relationship('Choice', backref='question', lazy=True) #Choiceモデルと関連付け

# Choiceモデルの定義
class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True) #　主キー
    choice_text = db.Column(db.String, nullable=False) #選択肢内の文章を保存するカラム
    is_correct = db.Column(db.Boolean, default=False, nullable=False) #選択肢が正しいかどうかを示すブール型カラム。
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False) #モデルのIDにリンクする外部キー。
    # sqlalchemyではモデルクラス名に大文字が使われていても外部キーとして参照する自動的に小文字に変換される
    order = db.Column(db.Integer, nullable=False)  # 選択肢の順序を保存する整数カラム

# クイズデータを追加する関数
def add_quiz_data():
    # ここにクイズデータを追加するためのロジックを記述
    new_question = Question(
        question_text='Pythonの創設者は誰ですか？',
        explanation='Pythonの創設者はギド・ヴァン・ロッサムです。'
    )
    db.session.add(new_question)
    db.session.commit()

    """question=new_questionの部分は、Choiceインスタンス作成において、その選択肢が
    関連する質問（new_question）を指定。具体的には、Choiceモデルの
    questionフィールド（実際にはquestion_id）に、新しく作成された質問のIDを設定。
    これにより、各選択肢が特定の質問に関連付けられることになる。よってquestionの記述は
    そのままでよい。"""
    new_choices = [
        Choice(choice_text='リンクス・トーバルズ', is_correct=False, question=new_question, order=1),
        Choice(choice_text='ギド・ヴァン・ロッサム', is_correct=True, question=new_question, order=2),
        Choice(choice_text='マーク・ザッカーバーグ', is_correct=False, question=new_question, order=3),
        Choice(choice_text='スティーブ・ジョブズ', is_correct=False, question=new_question, order=4)
    ]
    db.session.add_all(new_choices)
    db.session.commit()

# メイン処理
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_quiz_data()
