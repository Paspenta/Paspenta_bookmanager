import pytest
from bookmanager.db import get_db
response = ""

def test_index(client, auth):
    auth.login()

    response = client.get("/")
    url = b"/book_edit?BookID=1"
    assert b"TestBook1" in response.data
    assert url in response.data
    assert b"CONCAT1,CONCAT2" in response.data or "CONCAT2,CONCAT1" in response.data
    assert b"OtherBook" not in response.data

@pytest.mark.parametrize(
    ("parm", "value", "HitBook"), [
        ("Title", "NeoVim", b"SearchNeoVim"),
        ("SeriesName", "Golang", b"S_GL_Book"),
        ("AuthorName", "JavaScript", b"S_JS_Book"),
        ("PublisherName", "Python", b"S_P_Book"),
        ("LocationName", "Flutter", b"S_FL_Book"),
    ]
)
def test_index_search(client, auth, parm, value, HitBook):
    auth.login()

    response = client.get("/", query_string={parm:value})
    assert b"TestBook" not in response.data
    assert HitBook in response.data

def test_index_series(client, auth):
    auth.login()

    response = client.get("/index_series")
    url = b"/register?title="
    assert b"TestSeries1" in response.data
    assert url in response.data

@pytest.mark.parametrize(
    ("parm", "value", "HitBook"), [
        ("Title", "NeoVim", b"SearchNeoVim"),
        ("SeriesName", "Golang", b"S_GL_Book"),
        ("AuthorName", "JavaScript", b"S_JS_Book"),
        ("PublisherName", "Python", b"S_P_Book"),
        ("LocationName", "Flutter", b"S_FL_Book"),
    ]
)
def test_index_Series(client, auth, parm, value, HitBook):
    auth.login()

    response = client.get("/", query_string={parm:value})
    assert b"TestBook" not in response.data
    assert HitBook in response.data


def test_index_pagenation(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()

        for i in range(1, 62):
            db.execute(
                """
                INSERT INTO Books (Title, SeriesID, LocationID, UserID)
                VALUES (?, 1, 1, 1);
                """, (f"Pagenation{i:02}",)
            )
        db.commit()

        response = client.get("/", query_string={"Title":"Pagenation"})
        data = response.data.decode("utf-8")
        for i in range(1, 31):
            assert f"Pagenation{i:02}" in data
        for i in range(31, 62):
            assert f"Pagenation{i:02}" not in data

        response = client.get("/", query_string={"Title":"Pagenation", "Page":"1"})
        data = response.data.decode("utf-8")
        for i in range(1, 31):
            assert f"Pagenation{i:02}" not in data
        for i in range(31, 61):
            assert f"Pagenation{i:02}" in data
        assert f"Pagenation61" not in data

        response = client.get("/", query_string={"Title":"Pagenation", "Page":"2"})
        data = response.data.decode("utf-8")
        for i in range(1, 61):
            assert f"Pagenation{i:02}" not in data
        assert "Pagenation61" in data

def test_index_series_pagenation(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()

        for i in range(1, 32):
            db.execute(
                """
                INSERT INTO Series (SeriesName, UserID)
                VALUES (?, 1);
                """, (f"PagenationSeries{i:02}",)
            )
            SeriesID = db.execute(
                """
                SELECT SeriesID
                FROM Series
                WHERE SeriesName = ?;
                """, (f"PagenationSeries{i:02}",)
            ).fetchone()["SeriesID"]
            db.execute(
                """
                INSERT INTO Books (Title, SeriesID, LocationID, UserID)
                VALUES (?, ?, 1, 1);
                """, (f"PagenationBook{i:02}", SeriesID)
            )
        db.commit()

        response = client.get("/index_series", query_string={"SeriesName":"Pagenation"})
        data = response.data.decode("utf-8")
        for i in range(1, 16):
            assert f"PagenationSeries{i:02}" in data
        for i in range(16, 32):
            assert f"PagenationSeries{i:02}" not in data

        response = client.get("/index_series", query_string={"SeriesName":"Pagenation", "Page":"1"})
        data = response.data.decode("utf-8")
        for i in range(1, 16):
            assert f"PagenationSeries{i:02}" not in data
        for i in range(16, 31):
            assert f"PagenationSeries{i:02}" in data
        assert f"PagenationSeries31" not in data

        response = client.get("/index_series", query_string={"SeriesName":"Pagenation", "Page":"2"})
        data = response.data.decode("utf-8")
        for i in range(1, 31):
            assert f"PagenationSeries{i:02}" not in data
        assert f"PagenationSeries31" in data