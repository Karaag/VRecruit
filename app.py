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
    #posts = Post.query.all()
    return render_template("index.html") #posts=posts

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
    return render_template("create_post.html")

@app.route("/create_post_check", methods=["GET","POST"])
def create_post_check():
    if request.method == "POST":

        return redirect(url_for("index"))
    return render_template("create_post_check.html")

# 検索ページ (GETのみ想定)
@app.route("/search", methods=["GET"])
def search():
    """検索窓からの入力をもとに、通常検索 or タグ検索を行う"""
    query = request.args.get("q", "").strip()  # 検索ワードを取得
    if not query:
        # 入力が空の場合、何もしないか、全件返すなどお好みで
        return render_template("search.html", results=[], query=query)

    if query.startswith("#"):
        # ===================
        # タグ検索
        # ===================
        tag_name = query[1:]  # 先頭の "#" を削除
        # Tagテーブルで一致するタグを探し、PostTag から該当するPostをJOINで取得
        results = (
            db.session.query(Post)
            .join(PostTag, Post.post_id == PostTag.post_id)
            .join(Tag, PostTag.tag_id == Tag.tag_id)
            .filter(Tag.name == tag_name)
            .filter(Post.delete_flag == False)  # もし「削除フラグ」を除外したい場合
            .all()
        )
    else:
        # ===================
        # 通常の投稿本文検索
        # ===================
        # ここでは部分一致検索 (LIKE) を想定
        results = (
            Post.query
            .filter(Post.delete_flag == False)  # 削除フラグ OFF のものだけ
            .filter(Post.content.contains(query))
            .all()
        )
    
    return render_template("search.html", results=results, query=query)

# アプリ起動時にデータベースを作成
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)