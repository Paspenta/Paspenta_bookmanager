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
            VALUES ('RemainBook', 3, 3, 3, 4);
            """
        )

        # 1冊目を削除
        response = client.post("/book_del?BookID=3")
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


def test_sereis_del(client, auth, app):
    """_summary_
    シリーズごと本の削除ができるか
    """

    auth.login("delete_validate", "delete_password")

    # 削除した後、indexに遷移するか
    response = client.post("/series_del?SeriesID=3")
    assert response.headers["Location"] == "/"

    # シリーズが削除されているか確認
    with app.app_context():
        db = get_db()
        for table in ("Books", "BookAuthors"):
            assert db.execute(f"SELECT 1 FROM {table} WHERE BookID = 3").fetchone() is None
        assert db.execute(f"SELECT 1 FROM Series WHERE SeriesID = 3").fetchone() is None