from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

from .manager import (
    bp, get_page
)

GET_BOOK_AMOUNT = 30
GET_SERIES_AMOUNT = 15

def get_url_parameters():
    """_summary_

    URL Parameters
    --------------
    SeriesName: str
        シリーズ名から検索する
    AuthorName: str
        著者名で検索
    PublisherName: str
        出版社名で検索
    LocationName: str
        本がある場所で検索

    Returns
    -------
    parms: dict
        URLパラメタ
    """
    def f(name):
        if name == "":
            return "%"
        else:
            return "%" + name + "%"

    parms = {
        "Title": f(request.args.get("Title", "")),
        "SeriesName": f(request.args.get("SeriesName", "")),
        "AuthorName": f(request.args.get("AuthorName", "")),
        "PublisherName": f(request.args.get("PublisherName", "")),
        "LocationName": f(request.args.get("LocationName", "")),
        "page": get_page(request.args.get("Page", "0"))
    }


    return parms


def get_have_books(db, UserID, parms):
    books = db.execute(
        """
        SELECT
            Books.BookID AS BookID,
            Title,
            Series.SeriesName AS SeriesName,
            Locations.LocationName AS LocationName,
            COALESCE(Publishers.PublisherName, '') AS PublisherName,
            COALESCE(GROUP_CONCAT(Authors.AuthorName, ','), '') AS Authors,
            COALESCE(PublicationDate, '') AS PublicationDate,
            COALESCE(ISBN13, ISBN10, '') AS ISBN
        FROM Books
        JOIN Series ON Series.SeriesID = Books.SeriesID
        JOIN Locations ON Locations.LocationID = Books.LocationID
        LEFT JOIN Publishers ON Publishers.PublisherID = Books.PublisherID
        LEFT JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
        LEFT JOIN Authors ON Authors.AuthorID = BookAuthors.AuthorID
        WHERE
            Books.UserID = ?
            AND Title LIKE ?
            AND Locations.LocationName LIKE ?
            AND (Authors.AuthorName LIKE ? OR (Authors.AuthorName IS NULL AND ? = '%'))
            AND (Publishers.PublisherName LIKE ? OR (Publishers.PublisherName IS NULL AND ? = '%'))
        GROUP BY Books.BookID
        LIMIT ? OFFSET ?;
        """, (
            UserID,
            parms["Title"],
            parms["LocationName"],
            parms["AuthorName"], parms["AuthorName"],
            parms["PublisherName"], parms["PublisherName"],
            GET_BOOK_AMOUNT, GET_BOOK_AMOUNT * parms["page"]
        )
    ).fetchall()

    return books

def get_series_data(row, db, parms):
    series_data = dict(row)
    # 本がある場所を追加
    series_data["Locations"] = db.execute(
        """
        SELECT
            Locations.LocationName AS LocationName,
            COUNT(Books.LocationID) AS VolumeCount
        FROM Books
        JOIN Locations ON Books.LocationID = Locations.LocationID
        WHERE SeriesID = ?
        GROUP BY Books.LocationID
        ORDER BY `VolumeCount` DESC;
        """, (series_data["SeriesID"],)
    ).fetchall()
    series_data["PublisherName"] = db.execute(
        """
        SELECT
            COALESCE(MAX(Publishers.PublisherName), '') AS PublisherName,
            COUNT(Books.PublisherID) AS PublisherCount
        FROM Books
        LEFT JOIN Publishers ON Books.PublisherID = Publishers.PublisherID
        WHERE Books.SeriesID = ?
        GROUP BY Books.SeriesID
        ORDER BY PublisherCount DESC
        LIMIT 1;
        """, (series_data["SeriesID"],)
    ).fetchone()["PublisherName"]

    series_data["volumes"] = db.execute(
        """
        SELECT
            Books.BookID AS BookID,
            Title,
            Locations.LocationName AS LocationName,
            COALESCE(Publishers.PublisherName, '') AS PublisherName,
            COALESCE(GROUP_CONCAT(Authors.AuthorName, ','), '') AS Authors,
            COALESCE(PublicationDate, '') AS PublicationDate,
            COALESCE(ISBN13, ISBN10, '') AS ISBN
        FROM Books
        JOIN Locations ON Locations.LocationID = Books.LocationID
        LEFT JOIN Publishers ON Publishers.PublisherID = Books.PublisherID
        LEFT JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
        LEFT JOIN Authors ON Authors.AuthorID = BookAuthors.AuthorID
        WHERE
            Title LIKE ?
            AND SeriesID = ?
            AND Locations.LocationName LIKE ?
            AND (Authors.AuthorName LIKE ? OR (Authors.AuthorName IS NULL AND ? = '%'))
            AND (Publishers.PublisherName LIKE ? OR (Publishers.PublisherName IS NULL AND ? = '%'))
        GROUP BY Books.BookID
        LIMIT ? OFFSET ?;
        """, (
            parms["Title"],
            series_data["SeriesID"],
            parms["LocationName"],
            parms["AuthorName"], parms["AuthorName"],
            parms["PublisherName"], parms["PublisherName"],
            GET_BOOK_AMOUNT, GET_BOOK_AMOUNT * parms["page"]
        )
    ).fetchall()

    register_parms = {
        "title":series_data["SeriesName"],
        "seriesName":series_data["SeriesName"],
        "publisher":series_data["PublisherName"],
        "author":series_data["Authors"],
        "Location":series_data["Locations"][0]["LocationName"]
    }
    series_data["add_volume_url"] = url_for('manager.register', **register_parms)

    return series_data


def get_pagenation(parms):
    plus_page = {**request.args}
    minus_page = {**request.args}
    plus_page["Page"] = parms["page"]+1
    minus_page["Page"] = parms["page"]-1 if parms["page"]>0 else 0
    return plus_page, minus_page


def get_series(db, UserID, parms):
    series_list = db.execute(
        """
        SELECT
            Series.SeriesID AS SeriesID,
            SeriesName,
            COALESCE(GROUP_CONCAT(Authors.AuthorName, ','), '') AS Authors
        FROM Series
        JOIN Books ON Series.SeriesID = Books.SeriesID
        JOIN Locations ON Books.LocationID = Locations.LocationID
        LEFT JOIN Publishers ON Books.PublisherID = Publishers.PublisherID
        LEFT JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
        LEFT JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
        WHERE
            Series.UserID = ?
            AND SeriesName LIKE ?
            AND Books.Title LIKE ?
            AND Locations.LocationName LIKE ?
            AND (Authors.AuthorName LIKE ? OR (Authors.AuthorName IS NULL AND ? = '%'))
            AND (Publishers.PublisherName LIKE ? OR (Publishers.PublisherName IS NULL AND ? = '%'))
        GROUP BY Series.SeriesID
        ORDER BY SeriesName
        LIMIT ? OFFSET ?;
        """, (
            UserID,
            parms["SeriesName"],
            parms["Title"],
            parms["LocationName"],
            parms["AuthorName"], parms["AuthorName"],
            parms["PublisherName"], parms["PublisherName"],
            GET_SERIES_AMOUNT, parms["page"] * GET_SERIES_AMOUNT
        )
    ).fetchall()

    # 各シリーズに情報を追加
    series_list = [get_series_data(row, db, parms) for row in series_list]
    return series_list


@bp.route("/")
@login_required
def index():
    """_summary_
    登録書籍を一覧表示するview

    Returns
    -------
    検索条件がなければ全ての書籍を表示
    検索条件があれば検索条件にあった書籍のみを表示
    """

    db = get_db()
    UserID = g.user["UserID"]

    parms = get_url_parameters()

    Books = get_have_books(db, UserID, parms)
    plus_page, minus_page = get_pagenation(parms)

    return render_template("index.html",
                            Books=Books,
                            plus_page=plus_page,
                            minus_page=minus_page)

@bp.route("/index_series")
@login_required
def index_series():
    """Overview
    本をシリーズごとに表示

    Returns
    -------
    検索条件がある場合、検索条件に一致する本を表示
    検索条件がない場合、ユーザーが持つ本を表示
    """
    db = get_db()
    UserID = g.user["UserID"]

    parms = get_url_parameters()

    plus_page, minus_page = get_pagenation(parms)


    series_list = get_series(db, UserID, parms)

    return render_template("index_series.html",
                            series_list=series_list,
                            plus_parms=plus_page,
                            minus_parms=minus_page)