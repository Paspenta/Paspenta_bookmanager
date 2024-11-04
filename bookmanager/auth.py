import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from bookmanager.db import get_db

# 第二引数:bpの定義場所, url_prefix:bpに関連するURL
bp = Blueprint("auth", __name__, url_prefix="/auth")

def password_check(db, UserName, Password):
    """Overview
    パスワードを照合, 
    ユーザー名が存在しない、または、パスワードが異なる場合errorに文字列を格納

    Parameters
    ----------
    db: sqlite3.Connection
        データベース接続オブジェクト
    UserName: str
        formで入力されたUserName
    Password: str
        formで入力されたパスワード
    UserID: str
        既にログインしている場合のUserID

    Returns
    -------
    error: str or None
        エラー内容を格納する
    user: sqlite3.Row
        ユーザー情報
    """
    error = None

    user = db.execute(
        "SELECT * FROM Users WHERE UserName = ?", (UserName,)
    ).fetchone() # username, はタプルにするため

    if user is None:
        error = "ユーザー名が違います。"
    elif not check_password_hash(user["Password"], Password):
        error = "パスワードが違います。"
    
    return error, user



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

        error, user = password_check(db, UserName, Password)
        
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
    return redirect(url_for("manager.index"))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        
        return view(**kwargs)
    
    return wrapped_view

@bp.route("/edit", methods=("GET", "POST"))
@login_required
def edit():
    """Overview
    アカウント編集画面

    feature
    ----------
    UserNameを変更
    パスワードを変更
    アカウントを削除するボタンを設置
    """
    if request.method == "POST":
        category = request.form.get("category", None)
        NewUserName = request.form.get("NewUserName", None)
        OldPassword = request.form.get("OldPassword", None)
        NewPassword = request.form.get("NewPassword", None)
        db = get_db()
        UserID = g.user["UserID"]
        error = None
        msg = None

        UserName = db.execute(
            "SELECT UserName FROM Users WHERE UserID = ?", (UserID,)
        ).fetchone()["UserName"]

        if category == "UserName":
            if NewUserName is not None:
                # UserNameを変更
                try:
                    db.execute(
                        """
                        UPDATE Users 
                        SET UserName = ?
                        WHERE UserID = ?
                        """, (NewUserName, UserID))
                    db.commit()
                    msg = "ユーザー名を変更しました"
                except db.IntegrityError:
                    # usernameが既に登録されている場合の処理
                    error = f"ユーザー名 {NewUserName} は既に使われています。"
            else:
                error = "ユーザー名が入力されていません"
        elif category == "Password":
            # Passwordを変更
            if NewPassword is not None and OldPassword is not None:
                error, _ = password_check(db=db, UserName=UserName, Password=OldPassword)
                if error is None:
                    db.execute(
                        """
                        UPDATE Users
                        SET Password = ?
                        WHERE UserID = ?
                        """, (generate_password_hash(NewPassword), UserID)
                    )
                    db.commit()
                    msg = "Passwordを変更しました"
            else:
                error = "パスワードが入力されていません"
        
        if error is not None:
            flash(error)
        if msg is not None:
            flash(msg)
    
    return render_template("auth/edit.html")