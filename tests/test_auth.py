import pytest
from flask import g, session
from bookmanager import get_db

def test_register(client, app):
    # getして200が取得できるか
    assert client.get("/auth/register").status_code == 200

    # aを登録
    response = client.post(
        "/auth/register", data={"UserName": "a", "Password": "a"}
    )
    # 登録後、loginに遷移するか
    assert response.headers["Location"] == "/auth/login"

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM Users WHERE UserName = 'a'").fetchone()
        assert user is not None

# 無効なユーザー名, パスワードを渡して特定のエラーメッセージが返ってくるか
@pytest.mark.parametrize(
    ("UserName", "Password", "msg"),
    ("", "", "ユーザー名が入力されていません。"), 
    ("a", "", "パスワードが入力されていません。")
    ("a", "a", "ユーザー名 a は既に使われています。")
)
def test_register_validate_input(client, UserName, Password, msg):
    # registerに無効なユーザー名・パスワードを送る
    response = client.post(
        "/auth/register",
        data={"UserName":UserName, "Password": Password}
    )
    # 特定のエラーメッセージが含まれているか
    assert msg in response.data.decode('utf-8')


def test_login(client, auth):
    # loginにアクセスできるか
    assert client.get("/auth/login").status_code == 200
    response = auth.login()

    # ログイン後、indexにリダイレクトするか
    assert response.headers["Location"] == "/"

    with client:
        client.get('/')
        assert session["UserID"] == 1
        assert g.user["UserName"] == "test"