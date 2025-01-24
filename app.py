import os
from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Post, PostAnalytics, Tag, PostTag
from werkzeug.utils import secure_filename

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
    # DBから投稿を一覧表示
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

@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if request.method == "GET":
        # 入力フォームを表示
        return render_template("create_post.html")

    # POST: フォーム送信されたデータを受け取り、DBに登録
    content = request.form.get("content")  # 実際はタイトル扱い
    tweet_link = request.form.get("tweet_link")
    tags_str = request.form.get("tags", "").strip()
    file = request.files.get("thumbnail")

    # バリデーション例
    if not content or not tweet_link:
        return "タイトル(content) と URL は必須です", 400
    if len(content) > 30:
        return "タイトルは30文字以内にしてください", 400

    # サムネイル画像を保存
    image_path = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)
        image_path = f"/{app.config['UPLOAD_FOLDER']}/{filename}"

    # DB登録
    # ここでは content にタイトルをそのまま入れている
    new_post = Post(
        user_id=1,        # ログイン中のユーザーIDなどを適用
        content=content,  # 「タイトル」として入力された値を content に保存
        tweet_link=tweet_link,
        image=image_path
    )
    db.session.add(new_post)
    db.session.flush()  # post_id が確定

    # タグがあれば紐付け (Tag, PostTag)
    if tags_str:
        # スペース区切りを最大6個まで
        tag_list = tags_str.split()
        tag_list = tag_list[:6]
        for tname in tag_list:
            # 先頭に # がついてるなら除去
            if tname.startswith("#"):
                tname = tname[1:]
            tname = tname.strip()
            if not tname:
                continue
            # 既存タグがあるかチェック
            existing_tag = Tag.query.filter_by(name=tname).first()
            if not existing_tag:
                existing_tag = Tag(name=tname)
                db.session.add(existing_tag)
                db.session.flush()
            # PostTag で紐付け
            pt = PostTag(post_id=new_post.post_id, tag_id=existing_tag.tag_id)
            db.session.add(pt)

    db.session.commit()
    return redirect(url_for("index"))



# アプリ起動時にデータベースを作成
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)