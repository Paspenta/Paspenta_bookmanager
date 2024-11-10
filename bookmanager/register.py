from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db
from bookmanager.get_books import get_books

from .manager import (
    bp, get_page, get_id, get_datalist
)
MAX_RESULT = 30


@bp.route("/register", methods=("GET", "POST"))
@login_required
def register():
    if request.method == "POST":
        Title = request.form.get("Title", "")
        Series = request.form.get("Series", "")
        Location = request.form.get("Location", "")
        input_authors = request.form.get("author", "")
        Publisher = request.form.get("Publisher", "")
        PublicationDate = request.form.get("PublicationDate", None)
        ISBN13 = request.form.get("ISBN13", None)
        ISBN10 = request.form.get("ISBN10", None)
        UserID = g.user["UserID"]
        db = get_db()
        error = None

        if Title == "":
            error = "タイトルが入力されていません"
        elif Location == "":
            error = "本の場所が入力されていません"
        exists = db.execute(
            """
            SELECT 1
            FROM Books
            WHERE
                Title = ?
                AND UserID = ?
            """, (Title, UserID)
        ).fetchall()
        if exists:
            error = f"「{Title}」は既に登録されています。"

        if error is None:
            if Publisher != "":
                PublisherID = get_id(db, "Publishers", "PublisherName", "PublisherID", Publisher, UserID)
            else:
                PublisherID = None

            Series = Series if Series != "" else Title
            SeriesID = get_id(db, "Series", "SeriesName", "SeriesID", Series, UserID)
            LocationID = get_id(db, "Locations", "LocationName", "LocationID", Location, UserID)

            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO Books (
                    Title,
                    UserID,
                    LocationID,
                    SeriesID,
                    PublisherID,
                    PublicationDate,
                    ISBN13,
                    ISBN10
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?
                );
                """, (
                    Title,
                    UserID,
                    LocationID,
                    SeriesID,
                    PublisherID,
                    PublicationDate,
                    ISBN13, ISBN10
                )
            )
            BookID = cursor.lastrowid
            db.commit()
            cursor.close()

            if input_authors != "":
                Authors = set(input_authors.split(","))
                Authors.discard("")
                for Author in Authors:
                    AuthorID = get_id(db, "Authors", "AuthorName", "AuthorID", Author, UserID)
                    db.execute(
                        """
                        INSERT INTO BookAuthors (BookID, AuthorID)
                        VALUES (?, ?)
                        """, (BookID, AuthorID)
                    )
            db.commit()
            return redirect(url_for('manager.index'))

        else:
            flash(error, 'info')
    Book = dict()
    Book["Title"] = request.args.get("title", "")
    Book["Series"] = request.args.get("series", Book["Title"])
    Book["author"] = request.args.get("author", "")
    Book["Location"] = request.args.get("Location", "")
    Book["Publisher"] = request.args.get("publisher", "")
    Book["PublicationDate"] = request.args.get("publishe_date", "")
    Book["ISBN13"] = request.args.get("ISBN13", "")
    Book["ISBN10"] = request.args.get("ISBN10", "")

    UserID = g.user["UserID"]
    datalist = get_datalist(get_db(), UserID)

    return render_template("book_register.html", Book=Book, datalist=datalist)


@bp.route("/register_search")
@login_required
def register_search():
    keyword = request.args.get("keyword", None)
    title = request.args.get("title", None)
    author = request.args.get("author", None)
    isbn = request.args.get("isbn", None)
    page = request.args.get("Page", "0")
    parms = request.args

    page = get_page(page)

    plus_page = {**request.args}
    minus_page = {**request.args}
    plus_page["Page"] = page+1
    minus_page["Page"] = page - 1 if page > 0 else -1


    books = get_books(q=keyword, intitle=title, inauthor=author, isbn=isbn)
    next_flag = len(books) == MAX_RESULT

    return render_template("register_search.html",
                            Books=books,
                            plus_parms=plus_page,
                            minus_parms=minus_page,
                            parms=parms,
                            next_flag=next_flag)