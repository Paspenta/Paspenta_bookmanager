from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db
from bookmanager.get_books import get_books

from .manager import (
    bp, get_page, get_id
)


@bp.route("/register", methods=("GET", "POST"))
@login_required
def register():
    if request.method == "POST":
        Title = request.form["Title"]
        Series = request.form["Series"]
        Location = request.form["Location"]
        input_authors = request.form["author"]
        Publisher = request.form["Publisher"]
        PublicationDate = request.form["PublicationDate"]
        ISBN13 = request.form["ISBN13"]
        ISBN10 = request.form["ISBN10"]
        UserID = g.user["UserID"]
        db = get_db()
        error = None

        if not Title:
            error = "タイトルが入力されていません"
        elif not Location:
            error = "本の場所が入力されていません"
        
        if error is None:
            if not Series:
                Series = Title
            if Publisher:
                PublisherID = get_id(db, "Publishers", "PublisherName", "PublisherID", Publisher, UserID)
            else:
                PublisherID = None
            authorsID = []
            if input_authors:
                for author in input_authors.split(","):
                    authorsID.append(
                        get_id(db, "Authors", "AuthorName", "AuthorID", author, UserID)
                    )
            
            db.execute(
                """
                INSERT INTO Series (SeriesName, PublisherID, UserID)
                SELECT ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM Series
                    WHERE
                        SeriesName = ?
                        AND UserID = ?
                );
                """, (Series, PublisherID, UserID, Series, UserID)
            )
            SeriesID = db.execute(
                """
                SELECT SeriesID
                FROM Series
                WHERE
                    SeriesName = ?
                    AND UserID = ?
                """, (Series, UserID)
            ).fetchone()["SeriesID"]

            LocationID = get_id(db, "Locations", "LocationName", "LocationID", Location, UserID)
            
            db.execute(
                """INSERT INTO Books (
                    Title,
                    UserID,
                    LocationID,
                    SeriesID,
                    PublicationDate,
                    ISBN13,
                    ISBN10
                ) VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                );
                """, (
                    Title,
                    UserID,
                    LocationID,
                    SeriesID,
                    PublicationDate,
                    ISBN13, ISBN10
                )
            )
            for AuthorID in authorsID:
                db.execute(
                    """
                    INSERT INTO BookAuthors (SeriesID, AuthorID)
                    SELECT ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM BookAuthors
                        WHERE
                            SeriesID = ?
                            AND AuthorID = ?
                    );
                    """, tuple([SeriesID, AuthorID]*2)
                )
            db.commit()
            previous_url = session.get('previous_url', url_for('index'))
            return redirect(previous_url)

        else:
            flash(error)
    Book = dict()
    Book["Title"] = request.args.get("title", "")
    Book["Series"] = request.args.get("series", Book["Title"])
    Book["author"] = request.args.get("author", "")
    Book["Location"] = request.args.get("Location", "")
    Book["Publisher"] = request.args.get("publisher", "")
    Book["PublicationDate"] = request.args.get("publishe_date", "")
    Book["ISBN13"] = request.args.get("ISBN13", "")
    Book["ISBN10"] = request.args.get("ISBN10", "")

    return render_template("book_register.html", Book=Book)


@bp.route("/register_search")
@login_required
def register_search():
    keyword = request.args.get("keyword", None)
    title = request.args.get("title", None)
    author = request.args.get("author", None)
    isbn = request.args.get("isbn", None)
    page = request.args.get("page", "0")

    page = get_page(page)

    plus_parms = {**request.args}
    minus_parms = {**request.args}
    plus_parms["page"] = page+1
    minus_parms["page"] = page-1 if page>0 else 0

    books = get_books(q=keyword, intitle=title, inauthor=author, isbn=isbn)

    return render_template("register_search.html", Books=books, plus_parms=plus_parms, minus_parms=minus_parms)