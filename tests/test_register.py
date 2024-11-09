import pytest
from bookmanager.db import get_db
from flask import session, url_for


def test_register(client, auth, app):
    """_summary_
    正常に登録できるか
    """
    auth.login()
    data={
        "Title":"NewTitle",
        "Series":"NewSeries",
        "Location":"NewLocation",
        "author":"NewAuthor",
        "Publisher":"NewPublisher",
        "ISBN13":"New13",
        "ISBN10":"New10"
    }
    parms = {
        "Title":"TestTitle",
        "Series":"TestSeries",
        "author":"TestAuthor",
        "Location":"TestLocation",
        "Publisher":"TestPublisher",
        "PublicationData":"TestData",
        "ISBN13":"Test13",
        "ISBN10":"Test10"
    }
    # urlを生成
    url = "/register?"
    flag = True
    for key, v in parms.items():
        if flag:
            url = url + key + "=" + v
            flag = False
        else:
            url = url + "&" + key + "=" + v

    # URLパラメタがform valueに反映されるか
    response = client.get(url)
    html = response.data.decode("utf-8")
    for v in parms.values():
        assert v in html

    client.get("/register_search")
    response = client.post("/register", data=data)
    assert response.headers["Location"] == url
    with app.app_context():
        db = get_db()
        register_book = db.execute(
            """
            SELECT 1
            FROM Books
            JOIN Series ON Series.SeriesID = Books.SeriesID
            JOIN LOcations ON Locations.LocationID = Books.LocationID
            LEFT JOIN Publishers ON Publishers.PUblisherID = Books.PublisherID
            LEFT JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
            LEFT JOIN Authors ON Authors.AuthorID = BookAuthors.AuthorID
            WHERE
                Books.Title = 'NewTitle'
                AND Series.SeriesName = 'NewSeries'
                AND Locations.LocationName = 'NewLocation'
                AND Authors.AuthorName = 'NewAuthor'
                AND Publishers.PublisherName = 'NewPublisher'
                AND ISBN13 = 'New13'
                AND ISBN10 = 'New10'
            """
        ).fetchone()
        assert register_book is not None


@pytest.mark.parametrize(
    ("Title", "Location", "error"),
    ("", "", "タイトルが入力されていません"),
    ("NewTitle", "", "本の場所が入力されていません"),
    ("TestBook1", "NewLocation", "「TestBook1」は既に登録されています")
)
def test_register_validate(client, auth, app, Title, Location, error):
    auth.login()

    response = client.post("/register", data={"Title":Title, "Location":Location})
    html = response.data.decode("utf-8")
    assert error in html