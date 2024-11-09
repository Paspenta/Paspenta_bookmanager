import os
import tempfile

import pytest
from bookmanager import create_app
from bookmanager.db import get_db, init_db

# テストDB初期値をINSERTするSQLファイルをutf8でデコードして_data_sqlに格納
with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    # appをテストモード, dbにtempfileを指定
    app = create_app({
        "TESTING": True,
        "DATABASE": db_path
    })

    # テスト用DBを初期化し、テスト用データを挿入
    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)
    
    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    # テスト用クライアントを作成
    return app.test_client()

@pytest.fixture
def runner(app):
    # clickの実行者を作成
    return app.test_cli_runner()

class AuthActions(object):
    # clientにloginとlogout処理を付加
    def __init__(self, client):
        self.client = client
    
    def login(self, username="test", password="test_password"):
        return self.client.post(
            "/auth/login",
            data={"UserName": username, "Password": password}
        )
    
    def logout(self):
        return self._client.get("/auth/logout")

@pytest.fixture
def auth(client):
    return AuthActions(client)