import pytest
from bookmanager.db import get_db
response = ""

def test_book_edit(client, auth, app):
    auth.login()
    data={
        "BookID":1,
        "Title":"afterTitle",
        "SeriesName":"afterSeries",
        "PublisherName":"afterPublisher",
        "Authors":"AfterAuthor",
        "LocationName":"afterLocation",
        "PublicationDate":"after-date",
        "ISBN10":"afterISBN10",
        "ISBN13":"afterISBN13"
    }

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