import os
from flask import Flask, request, render_template, redirect, url_for, session
from models import db, User, Post, PostAnalytics, Tag, PostTag
from werkzeug.utils import secure_filename
from PIL import Image
from sqlalchemy import func


def make_square_center_crop(in_path, out_path, size=300):
    """アスペクト比を保ちつつ、正方形(size x size)に収まるよう中央トリミングする。"""
    with Image.open(in_path) as img:
        # 元のサイズ取得
        w, h = img.size

        # まず「短い辺を size にあわせる」形でリサイズ
        #   ratio = size / 短い辺
        ratio = size / min(w, h)
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        # PillowのANTIALIAS(=Resampling.LANCZOS)は高画質変換用
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 余分な部分を中央基準でトリミング → size x sizeを切り出す
        left = (new_w - size) / 2
        top = (new_h - size) / 2
        right = left + size
        bottom = top + size
        cropped = resized.crop((left, top, right, bottom))

        # 保存
        cropped.save(out_path)


app = Flask(__name__)

# データベースディレクトリとファイル名を設定
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
db_path = os.path.join(db_dir, "main.db")

# ディレクトリが存在しない場合は作成
os.makedirs(db_dir, exist_ok=True)

# データベースURIの設定
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


app.secret_key = "some_secret_key"
app.config["TMP_FOLDER"] = "static/tmp"      # 一時ファイル
app.config["UPLOAD_FOLDER"] = "static/uploads"  # 本登録保存先


# DBの初期化
db.init_app(app)


@app.route("/")
def index():
    # 削除フラグOFFの投稿だけを対象に
    base_query = Post.query.filter_by(delete_flag=False)

    # ★人気: ここでは単純に post_id の降順(新しい順)で6件
    popular_posts = base_query.order_by(Post.post_id.desc()).limit(6).all()

    # ★新着: created_at の新しい順で6件
    new_posts = base_query.order_by(Post.created_at.desc()).limit(6).all()

    # ★特集: ランダムで6件
    featured_posts = base_query.order_by(func.random()).limit(6).all()

    return render_template(
        "index.html",
        popular_posts=popular_posts,
        new_posts=new_posts,
        featured_posts=featured_posts
    )

# アカウントページ
@app.route("/account")
def account():
    # とりあえず簡単にテンプレートを返す例
    return render_template("account.html")

# アカウント編集ページ
@app.route("/account-edit")
def account_edit():
    # とりあえず簡単にテンプレートを返す例
    return render_template("account_edit.html")

# アカウントページ
@app.route("/analytics")
def analytics():
    # とりあえず簡単にテンプレートを返す例
    return render_template("user_analytics.html")

# 人気ページ
@app.route("/popular")
def popular_post():
    # とりあえず簡単にテンプレートを返す例
    return render_template("popular_post.html")

# 投稿作成ページ
@app.route("/post", methods=["GET", "POST"])
def post_page():
    if request.method == "POST":
        # ここでフォーム処理やDBへの書き込みなどを行う
        # title = request.form.get("title")
        # ...
        return redirect(url_for("index"))
    return render_template("create_post.html")


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

    # POST の場合
    action = request.form.get("action")
    if action == "confirm":
        # 1) フォーム入力を受け取り、一時的にセッション保存
        content = request.form.get("content")
        tweet_link = request.form.get("tweet_link")
        tags_str = request.form.get("tags", "").strip()

        # ▼ x.com → twitter.com に自動書き換え
        if tweet_link and "x.com" in tweet_link:
            tweet_link = tweet_link.replace("x.com", "twitter.com")
        
        # ファイルアップロード（サムネイル）
        thumbnail = request.files.get("thumbnail")
        thumbnail_filename = None
        if thumbnail and thumbnail.filename:
            safe_name = secure_filename(thumbnail.filename)
            # 一時フォルダに保存
            os.makedirs(app.config["TMP_FOLDER"], exist_ok=True)
            tmp_path = os.path.join(app.config["TMP_FOLDER"], safe_name)
            thumbnail.save(tmp_path)
            
            # ▼ ここで 300x300 にアスペクト比維持でトリミング
            out_path = tmp_path  # 上書きする場合は同じパスでもOK
            make_square_center_crop(tmp_path, out_path, size=300)

            thumbnail_filename = safe_name

        # セッションに保存
        session["post_data"] = {
            "content": content,
            "tweet_link": tweet_link,
            "tags": tags_str,
            "thumbnail_filename": thumbnail_filename
        }

        # 2) 確認画面へリダイレクト
        return redirect(url_for("create_post_confirm"))

    elif action == "register":
        # 3) 確認画面から「登録」を押した場合
        post_data = session.get("post_data", {})
        if not post_data:
            return redirect(url_for("create_post"))  # データがなければフォームへ

        # DB登録
        new_post = Post(
            user_id=1,  # ログインユーザーID想定
            content=post_data.get("content"),
            tweet_link=post_data.get("tweet_link")
            # imageは後ほど
        )
        db.session.add(new_post)
        db.session.flush()  # post_idを確定

        # サムネイルを本保存場所へ移動
        thumbnail_filename = post_data.get("thumbnail_filename")
        image_path = None
        if thumbnail_filename:
            tmp_path = os.path.join(app.config["TMP_FOLDER"], thumbnail_filename)
            final_path = os.path.join(app.config["UPLOAD_FOLDER"], thumbnail_filename)
            os.rename(tmp_path, final_path)  # tmp -> static/uploads
            image_path = f"/{app.config['UPLOAD_FOLDER']}/{thumbnail_filename}"
            new_post.image = image_path

        # タグ処理（最大6つ）
        tags_str = post_data.get("tags", "")
        if tags_str:
            tag_list = tags_str.split()
            tag_list = tag_list[:6]  # 6個に制限
            for t in tag_list:
                # 先頭#除去
                if t.startswith("#"):
                    t = t[1:]
                t = t.strip()
                if not t:
                    continue
                # Tagテーブルに存在チェック
                existing_tag = Tag.query.filter_by(name=t).first()
                if not existing_tag:
                    existing_tag = Tag(name=t)
                    db.session.add(existing_tag)
                    db.session.flush()
                # PostTag
                pt = PostTag(post_id=new_post.post_id, tag_id=existing_tag.tag_id)
                db.session.add(pt)

        db.session.commit()

        # セッション削除
        session.pop("post_data", None)

        return redirect(url_for("index"))

    else:
        # 何らかのイレギュラー
        return redirect(url_for("create_post"))


@app.route("/create_post/confirm", methods=["GET"])
def create_post_confirm():
    # セッションから入力データを取得
    post_data = session.get("post_data")
    if not post_data:
        return redirect(url_for("create_post"))  # データがなければフォームへ
    return render_template("create_post_check.html", post_data=post_data)


# アプリ起動時にデータベースを作成
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)