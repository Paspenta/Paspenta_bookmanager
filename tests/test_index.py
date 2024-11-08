import pytest
from bookmanager.db import get_db
response = ""

def test_index(client, auth):
    auth.login()

    response = client.get("/")
    url = b"/book_edit?BookID=1"
    assert "TestBook1" in response.data
    assert url in response.data
    assert b"CONCAT1,CONCAT2" in response.data or "CONCAT2,CONCAT1" in response.data
    assert b"OtherBook" in response.data

@pytest.mark.parametrize(
    ("parm", "value", "HitBook"),
    ("Title", "NeoVim", b"SearchNeoVim9"),
    ("SeriesName", "Golang", b"S_GL_Book5"),
    ("AuthorName", "JavaScript", b"S_JS_Book7"),
    ("PublisherName", "Python", b"S_P_Book5"),
    ("LocationName", "Flutter", b"S_FL_Book8"),
)
def test_index_search(client, auth, parm, value, HitBook):
    auth.login()

    response = client.get("/", query_string={parm:value})
    assert b"TestBook" not in response.data
    assert HitBook in response.data

def test_index_series(client, auth):
    auth.login()

    response = client.get("/index_series")
    url = "/book?Title"
    url = b"/register?title=TestSeries1&seriesName=TestSeries1&publisher=TestPublisher&author=TestAuthor1&Location=TestLocation"
    assert b"TestSeries1" in response.data
    assert url in response.data

@pytest.mark.parametrize(
    ("parm", "value", "HitBook"),
    ("Title", "NeoVim", b"SearchNeoVim9"),
    ("SeriesName", "Golang", b"S_GL_Book5"),
    ("AuthorName", "JavaScript", b"S_JS_Book7"),
    ("PublisherName", "Python", b"S_P_Book5"),
    ("LocationName", "Flutter", b"S_FL_Book8"),
)
def test_index_Series(client, auth, parm, value, HitBook):
    auth.login()

    response = client.get("/", query_string={parm:value})
    assert b"TestBook" not in response.data
    assert HitBook in response.data


def test_index_pagenation(client, auth, app):
    with app.app_context():
        auth.login()
        db = get_db()

        for i in range(1, 62):
            db.execute(
                """
                INSERT INTO Books (Title, SeriesID, LocationID, UserID)
                VALUES (?, 1, 1, 1):
                """, (f"Pagenation{i}",)
            )
        db.commit()

        response = client.get("/", query_string={"Title":"Pagenation"})
        data = response.data.decode("utf-8")
        for i in range(1, 31):
            assert f"Pagenation{i}" in data
        for i in range(31, 62):
            assert f"Pagenation{i}" not in data

        response = client.get("/"), query_string=({"Title":"Pagenation", "page":"2"})
        data = response.data.decode("utf-8")
        for i in range(1, 31):
            assert f"Pagenation{i}" not in data
        for i in range(31, 61):
            assert f"Pagenation{i}" in data
        assert f"Pagenation61" not in data

        response = client.get("/"), query_string=({"Title":"Pagenation", "page":"3"})
        data = response.data.decode("utf-8")
        for i in range(1, 61):
            assert f"Pagenation{i}" not in data
        assert f"Pagenation{i}" in data
