import pytest
from bookmanager.get_books import get_books, parse_book

@pytest.mark.parametrize(
    ("q", "intitle", "inauthor", "isbn", "page", "flag"),[
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
    ]
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
    def fake_get(URL, params):
        Recorder.called = True
        return fake_json()

    def fake_parse(book):
        Recorder.called_parse = True
        return True

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("bookmanager.get_books.parse_book", fake_parse)
    get_books(q, intitle, inauthor, isbn, page)
    assert Recorder.called == flag == Recorder.called_parse


@pytest.mark.parametrize("book, expected", [
    (
        {
            "volumeInfo": {
                "title": "Example Book",
                "authors": ["Author One", "Author Two"],
                "publisher": "Example Publisher",
                "publishedDate": "2023-01-01",
                "industryIdentifiers": [
                    {"type": "ISBN_10", "identifier": "1234567890"},
                    {"type": "ISBN_13", "identifier": "123-4567890123"}
                ]
            }
        },
        {
            "title": "Example Book",
            "author": "Author One,Author Two",
            "publisher": "Example Publisher",
            "publishe_date": "2023-01-01",
            "isbn_10": "1234567890",
            "isbn_13": "123-4567890123"
        }
    ),
    (
        {
            "volumeInfo": {
                "title": "Another Book",
                "authors": ["Single Author"],
                "publisher": "Another Publisher",
                "publishedDate": "2022-12-31",
                "industryIdentifiers": [
                    {"type": "ISBN_13", "identifier": "987-6543210987"}
                ]
            }
        },
        {
            "title": "Another Book",
            "author": "Single Author",
            "publisher": "Another Publisher",
            "publishe_date": "2022-12-31",
            "isbn_10": "",
            "isbn_13": "987-6543210987"
        }
    )
])
def test_parse_book(book, expected):
    assert parse_book(book) == expected