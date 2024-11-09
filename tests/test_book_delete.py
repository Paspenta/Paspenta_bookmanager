import pytest
from bookmanager.db import get_db
response = ""


def test_book_delete(client, auth, app):
    """
    本が削除できるか。また、本が一冊もなくなったシリーズを削除できるか
    """
    auth.login("delete_validate", "delete_password")

    response = client.post("/book_del?BookID=3")
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        for table in ("Books", "Series"):
            exists = db.execute(
                f"""
                SELECT 1
                FROM {table}
                WHERE UserID = 4;
                """
            ).fetchall()
            assert len(exists) == 0
        exists = db.execute("SELECT 1 FROM BookAuthors WHERE BookID = 3").fetchall()
        assert len(exists) == 0
        for table in ("Authors", "Publishers", "Locations"):
            exists = db.execute(
                f"""
                SELECT 1
                FROM {table}
                WHERE UserID = 4;
                """
            ).fetchall()
            assert len(exists) == 1


def test_book_delete_remain_series(client, auth, app):
    """
    本が削除できるか。また、本が一冊あるシリーズが削除されないか
    """
    auth.login("delete_validate", "delete_password")
    with app.app_context():
        db = get_db()
        # 2冊目の本を追加
        db.execute(
            """
            INSERT INTO Books (Title, SeriesID, LocationID, UserID)
            VALUES ('RemainBook', 3, 3, 4);
            """
        )

        # 1冊目を削除
        response = client.post("/book_del?BookID=3", follow_redirects=True)
        assert response.headers["Location"] == "/"

        # シリーズが残っているか
        exists = db.execute(
            """
            SELECT 1
            FROM Series
            WHERE SeriesID = 3;
            """
        ).fetchone()
        assert exists is not None
        # 2冊目が残っているか
        exists = db.execute(
            """
            SELECT 1
            FROM Books
            WHERE Title = 'RemainBook';
            """
        ).fetchone()
        assert exists is not None


def test_book_delete_validate(client, auth):
    """_summary_
    無効なリクエストをした時、適切な出力が得られるか
    """
    auth.login()

    # BookIDを指定しない
    assert client.post("/book_del?", follow_redirects=True).status_code == 400

    # 他ユーザーの本を指定
    assert client.post("/book_del?BookID=2", follow_redirects=True).status_code == 404

    # 存在しない本を指定
    assert client.post("/book_del?BookID=404", follow_redirects=True).status_code == 404


def test_sereis_del(client, auth, app):
    """_summary_
    シリーズごと本の削除ができるか
    """

    auth.login("delete_validate", "delete_password")

    # 削除した後、indexに遷移するか
    response = client.post("/series_del?SeriesID=3", follow_redirects=True)
    assert response.headers["Location"] == "/"

    # シリーズが削除されているか確認
    with app.app_context():
        db = get_db()
        for table in ("Books", "BookAuthors"):
            assert db.execute(f"SELECT 1 FROM {table} WHERE BookID = 3").fetchone() is None
        assert db.execute(f"SELECT 1 FROM Series WHERE SeriesID = 3").fetchone() is None


def test_series_del(client, auth):
    """_summary_
    series_delに無効なリクエストをして、適切なエラーが返ってくるか
    """
    auth.login()

    # seriesIDを指定しない
    assert client.post("/series_del?", follow_redirects=True).status_code == 400

    # 他ユーザーのシリーズを指定
    assert client.post("/series_del?SeriesID=2", follow_redirects=True).status_code == 404

    # 存在しないシリーズを指定
    assert client.post("/series_del?SeriesID=404", follow_redirects=True).status_code == 404