from datetime import datetime
import pytz
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ユーザーテーブル
class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    mailaddress = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    twitter_account = db.Column(db.String(50), nullable=True)

# 投稿テーブル
class Post(db.Model):
    __tablename__ = "posts"
    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tweet_link = db.Column(db.String(255), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone("Asia/Tokyo")))
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.now(pytz.timezone("Asia/Tokyo")))
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", backref="posts")

# 投稿アナリティクス
class PostAnalytics(db.Model):
    __tablename__ = "post_analytics"
    analytics_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.post_id"), nullable=False)
    click_count = db.Column(db.Integer, nullable=False, default=0)
    redirect_count = db.Column(db.Integer, nullable=False, default=0)
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone("Asia/Tokyo")))

    post = db.relationship("Post", backref="analytics")

# タグテーブル
class Tag(db.Model):
    __tablename__ = "tags"
    tag_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

# 投稿タグリレーション
class PostTag(db.Model):
    __tablename__ = "post_tags"
    post_id = db.Column(db.Integer, db.ForeignKey("posts.post_id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.tag_id"), primary_key=True)

    post = db.relationship("Post", backref="post_tags")
    tag = db.relationship("Tag", backref="post_tags")
