import os
from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Post, PostAnalytics, Tag, PostTag

app = Flask(__name__)

# データベースディレクトリとファイル名を設定
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
db_path = os.path.join(db_dir, "main.db")

# ディレクトリが存在しない場合は作成
os.makedirs(db_dir, exist_ok=True)

# データベースURIの設定
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# DBの初期化
db.init_app(app)

@app.route("/")
def index():
    posts = Post.query.all()
    return render_template("index.html", posts=posts)

# アカウントページ
@app.route("/account")
def account():
    # とりあえず簡単にテンプレートを返す例
    return render_template("account.html")

# 投稿作成ページ
@app.route("/post", methods=["GET", "POST"])
def post_page():
    if request.method == "POST":
        # ここでフォーム処理やDBへの書き込みなどを行う
        # title = request.form.get("title")
        # ...
        return redirect(url_for("index"))
    return render_template("post.html")

# 検索ページ (GETのみ想定)
@app.route("/search")
def search():
    keyword = request.args.get("q", "")  # クエリパラメータ ?q=... を取得
    # ここでDB検索などを行って結果を変数に入れる
    search_results = []
    # 例: search_results = Post.query.filter(Post.title.contains(keyword)).all()
    return render_template("search.html", keyword=keyword, results=search_results)

# アプリ起動時にデータベースを作成
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)