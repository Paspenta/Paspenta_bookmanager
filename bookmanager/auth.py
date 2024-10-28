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
        UserName = request.form["UserName"]
        Password= request.form["Password"]
        db = get_db()
        error = None

        if not UserName:
            error = "ユーザー名が入力されていません。"
        elif not Password:
            error = "パスワードが入力されていません。"
        
        if error is None:
            try:
                # プレースホルダーでusernameとパスワードを登録
                print("execute sql")
                db.execute(
                    "INSERT INTO Users (UserName, Password) VALUES (?, ?)",
                    (UserName, generate_password_hash(Password))
                )
                db.commit()
            except db.IntegrityError:
                # usernameが既に登録されている場合の処理
                error = f"ユーザー名 {UserName} は既に使われています。"
            else:
                # usernameが登録されていなかった場合
                return redirect(url_for("auth.login"))
        
        flash(error)
    
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        UserName = request.form["UserName"]
        Password = request.form["Password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM Users WHERE UserName = ?", (UserName,)
        ).fetchone() # username, はタプルにするため

        if user is None:
            error = "ユーザー名をが違います。"
        elif not check_password_hash(user["Password"], Password):
            error = "パスワードが違います。"
        
        if error is None:
            session.clear()
            session["UserID"] = user["UserID"]
            return redirect(url_for("manager.index"))
        
        flash(error)
    
    return render_template("auth/login.html")

@bp.before_app_request
def load_logged_in_user():
    # アカウント確認
    UserID = session.get("UserID")

    if UserID is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT * FROM Users WHERE UserID = ?", (UserID,)
        ).fetchone()

@bp.route("/logout")
def logout():
    # ログアウト処理
    session.clear()
    return redirect(url_for("index"))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        
        return view(**kwargs)
    
    return wrapped_view