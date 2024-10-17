import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from bookmanager.db import get_db

# 第二引数:bpの定義場所, url_prefix:bpに関連するURL
bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register", methods=("GET", "POST"))
def register():
    # アカウント登録view
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None

        if not username:
            error = "ユーザー名が入力されていません。"
        elif not password:
            error = "パスワードが入力されていません。"
        
        if error is None:
            try:
                # プレースホルダーでusernameとパスワードを登録
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
            except db.IntegrityError:
                # usernameが既に登録されている場合の処理
                error = f"ユーザー名 {username} は既に使われています。"
            else:
                # usernameが登録されていなかった場合
                return redirect(url_for("auth.login"))
        
        flash(error)
    
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone() # username, はタプルにするため

        if user is None:
            error = "ユーザー名をが違います。"
        elif not check_password_hash(user["password"], password):
            error = "パスワードが違います。"
        
        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        
        flash(error)
    
    return render_template("auth/login.html")