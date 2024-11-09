import pytest
from flask import g, session
from bookmanager.db import get_db
from bookmanager.auth import password_check
from werkzeug.security import check_password_hash

# Intelligence
response = ""

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
    ("UserName", "Password", "msg"), [
        ("", "", "ユーザー名が入力されていません。"),
        ("a", "", "パスワードが入力されていません。"),
        ("a", "a", "ユーザー名 a は既に使われています。")
    ]
)
def test_register_validate_input(client, UserName, Password, msg):
    # registerに無効なユーザー名・パスワードを送る
    response = client.post(
        "/auth/register",
        data={"UserName":UserName, "Password": Password}
    )
    # 特定のエラーメッセージが含まれているか
    assert msg in response.data.decode("utf-8")


def test_password_check(app):
    with app.app_context():
        db = get_db()

        error, user = password_check(db, "test", "test_password")
        assert error is None
        assert user is not None

        error, user = password_check(db, "NoneUser", "None_password")
        assert error == "ユーザー名が違います"
        assert error is None

        error, user = password_check(db, "test", "diff_password")
        assert error == "パスワードが違います。"


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


# loginで無効な入力をしたとき適切なメッセージが表示されるか
@pytest.mark.parametrize(
    ("UserName", "Password", "msg"), [
        ("a", "test", "ユーザー名が違います。"),
        ("test", "a", "パスワードが違います。")
    ]
)
def test_login_validate_input(auth, UserName, Password, msg):
    response = auth.login(UserName, Password)
    assert msg in response.data.decode("utf-8")


# logoutできるか
def test_logout(client, auth):
    auth.login()

    # ログアウト後、sessionがclearされているか
    with client:
        auth.logout()
        assert "UserID" not in session

def test_user_edit(client, auth, app):
    auth.login("change_before", "before")

    response = client.post(
        "/auth/edit",
        data={"category":"UserName", "NewUserName":"change_after"}
    )
    assert "ユーザー名を変更しました" in response.data.decode("utf-8")

    response = client.post(
        "/auth/edit",
        data={"category":"Password", "OldPassword":"before", "NewPassword":"after"}
    )
    assert "パスワードを変更しました" in response.data.decode("utf-8")

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM Users WHERE UserName = 'change_after'").fetchone()
        assert user is not None
        assert check_password_hash(user["Password"], "after")

def test_user_edit_category(client, auth):
    auth.login()
    response = client.post("/auth/edit")
    assert "カテゴリーが存在しません" in response.data.decode("utf-8")

    response = client.post("/auth/edit", data={"category":"diff"})
    assert "カテゴリーが存在しません" in response.data.decode("utf-8")


@pytest.mark.parametrize(
    ("UserName", "msg"), [
        ("", "ユーザー名が入力されていません"),
        ("other", "ユーザー名 other は既に使われています")
    ]
)
def test_username_edit_validate(client, auth, app, UserName, msg):
    """
    NewUserNameが無効な入力の場合、適切なメッセージを表示するか。また、UserNameが変更されていないか
    """
    auth.login()

    response = client.post(
        "/auth/edit",
        data={"category":"UserName", "NewUserName":UserName}
    )
    assert msg in response.data.decode("utf-8")

    with app.app_context():
        # UserNameが変更されていないか
        db = get_db()
        user = db.execute("SELECT * FROM Users WHERE UserName = 'test'").fetchone()
        assert user is not None


@pytest.mark.parametrize(
    ("OldPassword", "NewPassword", "msg"), [
        ("", "", "パスワードが入力されていません"),
        ("test", "", "パスワードが入力されていません"),
        ("", "test", "パスワードが入力されていません"),
        ("different", "after", "パスワードが違います")
    ]
)
def test_password_edit_validate(client, auth, app, NewPassword, OldPassword, msg):
    # 無効なパスワードを入力して、適切なメッセージが表示されるか
    auth.login()

    response = client.post(
        "/auth/edit",
        data={"category":"Password", "OldPassword":OldPassword, "NewPassword":NewPassword}
    )
    assert msg in response.data.decode("utf-8")

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM Users WHERE UserName = 'test'").fetchone()
        assert not check_password_hash(user["Password"], NewPassword)


def test_account_delete(client, auth, app):
    # アカウントが削除できるか、また、データが残っていないか
    username = "delete_validate"
    password = "delete_password"
    auth.login(username, password)

    # ログアウトされているか
    with client:
        client.post("/auth/delete", data={"Password":password})
        assert "UserID" not in session

    tables = ["Users", "Series", "Authors", "Locations", "Books"]

    with app.app_context():
        db = get_db()
        for table_name in tables:
            data_existis = db.execute(f"SELECT 1 FROM {table_name} WHERE UserID = 4").fetchone()
            assert data_existis is None
        data_existis = db.execute("SELECT 1 FROM BookAuthors WHERE SeriesID = 5").fetchone()
        assert data_existis is None

@pytest.mark.parametrize(
    ("Password", "msg"), [
        ("", "パスワードが入力されていません"),
        ("diff", "パスワードが違います")
    ]
)
def test_account_delete_validate(client, auth, app, Password, msg):
    auth.login()

    response = client.post("/auth/delete", data={"Password":Password})
    assert msg in response.data.decode("utf-8")

    tables = ["Users", "Series", "Authors", "Locations", "Books"]

    with app.app_context():
        db = get_db()
        for table_name in tables:
            data_existis = db.execute(f"SELECT 1 FROM {table_name} WHERE UserID = 1").fetchall()
            assert len(data_existis) > 0
        data_existis = db.execute("SELECT 1 FROM BookAuthors WHERE SeriesID = 1").fetchone()
        assert data_existis is not None