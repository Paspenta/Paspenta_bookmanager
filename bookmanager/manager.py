from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db
from bookmanager.get_books import get_books

bp = Blueprint("manager", __name__)

def get_page(page_str):
    if page_str is None:
        return 0
    try:
        ret = int(page_str)
        if ret < 0:
            ret = 0
    except (ValueError, TypeError):
        ret = 0
    
    return ret


@bp.route("/")
@login_required
def index():
    db = get_db()
    title = request.args.get("Title", None)
    author = request.args.get("AuthorName", None)
    publisher = request.args("PublisherName", None)
    Location = request.args("LocationName", None)
    page = request.args("Page", "0")
    user_id = g.user["UserID"]

    page = get_page(page)
    
    if publisher is None:
        publisher_where = ""
        place_holder = (author, Location, user_id, title, page)
    else:
        publisher_where = "AND `PublisherName` = ?"
        place_holder = (author, Location, user_id, title, publisher, page)
    
    Seriess = db.execute(
        """
        WITH AuthorFilter AS (
            SELECT SeriesID
            FROM BookAuthors
            WHERE AuthorID IN (
                SELECT AuthorsID
                FROM Authors
                WHERE AuthorsName = ?
            )
        )
        WITH LocationsFilter AS (
            SELECT *
            FROM Books
            WHERE LocationID = (
                SELECT LocationName
                FROM Locations
                WHERE = ?)
            )
        SELECT
            SeriesID,
            Series.SeriesName AS SeriesName
            Publishers.PublisherName AS PublisherName
        FROM LocationFilter
        JOIN Series ON SeriesID = Series.SeriesID
        WHERE
            UserID = ?
            AND `SeriesName` = ?
            {}
            AND SeriesID IN (
                SELECT SeriesID
                FROM AuthorFilter)
        GROUP BY SeriesID
        LIMIT 15 OFFSET ?
        """.format(publisher_where), place_holder
    ).fetchall()
    for i in range(len(Seriess)):
        authors = db.execute(
            """
            WITH SeriesAuthors AS (
                SELECT AuthorID
                FROM BookAuthors
                WHERE SeriesID = ?
            )
            SELECT AuthorName
            FROM Authors
            WHERE AuthorID IN SeriesAuthors;
            """, (Seriess[i]["SeriesID"],)
        ).fetchall()
        Seriess[i]["Authors"] = [author["AuthorName"] for author in authors]
        Seriess[i]["volumes"] = db.execute(
            """
            SELECT
                BookID,
                Title,
                PublicationDate,
                Locations.LocationName AS LocationName
                JOIN Locations ON LocationID = Locations.LocationID
                WHERE seriesID = ?
                ORDER BY Title;
            """, (Seriess[i]["SeriesID"],)
        ).fetchall()
    
    return render_template("index.html", Seriess)

@bp.route("/edit")
@login_required
def edit():
    pass

@bp.route("/book_del",methods=("POST",))
@login_required
def book_del():
    pass

@bp.route("/register_search")
@login_required
def register_search():
    keyword = request.args.get("keyword", None)
    title = request.args.get("title", None)
    author = request.args.get("author", None)
    isbn = request.args.get("isbn", None)
    page = request.args.get("page", "0")

    page = get_page(page)

    books = get_books(q=keyword, intitle=title, author=author, isbn=isbn)

    return render_template("register_search.html", books)