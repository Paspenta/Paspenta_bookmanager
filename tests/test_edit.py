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