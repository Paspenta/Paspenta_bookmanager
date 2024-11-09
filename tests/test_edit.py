import pytest
from bookmanager.db import get_db
response = ""

@pytest.mark.parametrize(
    ("flag", "AuthorName", "PublisherName", "SeriesName"),
    (True, "AfterAuthor", "AfterPublisher", "AfterSeries"),
    (False, None, None, None)
)
def test_book_edit(client, auth, app, flag, AuthorName, PublisherName, SeriesName):
    auth.login()
    data={
        "BookID":1,
        "Title":"AfterTitle",
        "LocationName":"AfterLocation",
        "PublicationDate":"AfterDate",
        "ISBN10":"afterISBN10",
        "ISBN13":"afterISBN13"
    }
    if flag:
        data["SeriesName"] = SeriesName
        data["Authors"] = AuthorName
        data["PublisherName"] = PublisherName

    response = client.get("/book_edit?BookID=1")
    html = response.data.decode("utf-8")
    book_datas = [
        "TestBook1", "TestSeries", "TestPublisher",
        "TestAuthor1", "TestLocation",
        "xxxx-xx-xx", "1234567890123", "1234567890"
    ]
    for book_data in book_datas:
        assert book_data in html

    response = client.post("/book_edit", data=data)
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        after_book = db.execute(
            """
            SELECT
                Books.BookID AS BookID,
                Title,
                Series.SeriesName AS SeriesName,
                Publishers.PublisherName AS PublisherName,
                Locations.LocationName AS LocationName,
                Authors.AuthorName AS Authors,
                PublicationDate,
                ISBN10,
                ISBN13
            FROM Books
            JOIN Series ON Books.SeriesID = Series.SeriesID
            JOIN Locations ON Books.LocationID = Locations.LocationID
            LEFT JOIN BookAuthors.BookID = Books.BookID
            LEFT JOIN Authors ON Authors.AuthorID, BookAuthors.AuthorID
            LEFT JOIN Publishers ON Publishers.PublisherID, Publishers.PublisherID
            WHERE Books.BookID = 1;
            """
        ).fetchone()
        assert after_book is not None
        for key, v in data.items():
            assert after_book[key] == v
        if not flag:
            assert after_book["SeriesName"] == "AfterTitle"
            assert after_book["PublisherName"] is None
            assert after_book["Authors"] is None


@pytest.mark.parametrize(
    ("BookID", "status_code"),
    (2, 404),
    (404, 404)
)
def test_book_edit_validate(client, auth, BookID, status_code):
    auth.login()

    data = {"BookID":1}

    assert client.post("/book_edit").status_code == 400
    assert client.get("/book_edit").status_code == 400

    response = client.post("/book_edit", data=data)
    html = response.data.decode("utf-8")
    assert "タイトルがありません" in html

    data["Title"] = "validate_title"
    response = client.post("/book_edit", data=data)
    html = response.data.decode("utf-8")
    assert "本の場所が入力されていません" in html

    data["BookID"] = BookID
    assert client.post("/book_edit", data=data).status_code == status_code
    assert client.get(f"/book_edit?BookID={BookID}").status_code == status_code
