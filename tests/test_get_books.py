import pytest
from bookmanager.get_books import get_books, parse_book

@pytest.mark.parametrize(
    ("q", "intitle", "inauthor", "isbn", "page", "flag"),
    ("Python", None, None, None, 0, True),
    (None, "Python", None, None, 0, True),
    (None, None, "Python", None, 0, True),
    (None, None, None, "Python", 0, True),
    (None, None, None, None, 0, False),
    ("Python", "", "", "", 0, True),
    ("", "Python", "", "", 0, True),
    ("", "", "Python", "", 0, True),
    ("", "", "", "Python", 0, True),
    ("", "", "", "", 0, False),
)
def test_get_books(monkeypatch, q, intitle, inauthor, isbn, page, flag):
    class Recorder(object):
        called = False
        called_parse = False

    class fake_json:
        def __init__(self):
            pass

        def json(self):
            return {"items":"test"}

    # init_dbが呼び出されたことを記録
    def fake_get(parms):
        Recorder.called = True
        return fake_json()

    def fake_parse(book):
        return True

    monkeypatch.setattr("request.get", fake_get)
    monkeypatch.setattr("bookmanager.get_books.parse_book", fake_parse)
    get_books(q, intitle, inauthor, isbn, page)
    assert Recorder.called == flag == Recorder.called_parse