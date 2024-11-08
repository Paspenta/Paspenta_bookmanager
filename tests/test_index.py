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