import sqlite3

import pytest
from bookmanager.db import get_db

def test_get_close_db(app):
    # get_dbはdbが閉じられるまで同じ接続を返す
    with app.app_context():
        db = get_db()
        assert db is get_db
    
    # 既に閉じられているはずのdbからSELECTを実行
    # ProgrammingErrorが出なければテスト失敗
    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute("SELECT 1")
    
    # エラーメッセージにclosedが含まれるか
    assert "closed" in str(e.value)

def test_init_db_command(runner, monkeypatch):
    # 実行されたかを記録する
    class Recorder(object):
        called = False
    
    # init_dbが呼び出されたことを記録
    def fake_init_db():
        Recorder.called = True
    
    # init_dbが呼び出された時、fake_init_dbも実行する
    monkeypatch.setattr("flask.db.init_db", fake_init_db)
    result = runner.invoke(args=["init-db"]) # ターミナルでinit-dbを実行

    # init_db_cmdはinit_dbが終わった後、初期化成功メッセージを返すはず
    assert "DB初期化" in result.output
    # init_dbが呼び出されたならcalledがTrueになっているはず
    assert Recorder.called