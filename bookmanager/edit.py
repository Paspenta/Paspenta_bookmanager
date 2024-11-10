from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

from .manager import (
    bp, get_id, get_datalist
)


def change_book_authors(db, UserID, BookID, authors):
    if authors == "":
        authors = []
    else:
        authors = set(authors.split(","))
        authors.discard("")
    db.execute(
        """
        DELETE FROM BookAuthors
        WHERE BookID = ?;
        """, (BookID,)
    )
    for author in authors:
        AuthorID = get_id(db, "Authors", "AuthorName", "AuthorID", author, UserID)
        db.execute(
            """
            INSERT INTO BookAuthors (BookID, AuthorID)
            VALUES (?, ?)
            """, (BookID, AuthorID)
        )
    db.commit()


@bp.route("/book_edit", methods=("GET", "POST"))
@login_required
def book_edit():
    if request.method == "POST":
        BookID = request.form.get("BookID")
        Title = request.form.get("Title", "")
        SeriesName = request.form.get("SeriesName", "")
        PublisherName = request.form.get("PublisherName", "")
        Authors = request.form.get("Authors", "")
        Location = request.form.get("LocationName", "")
        PublicationDate = request.form.get("PublicationDate", None)
        ISBN10 = request.form.get("ISBN10", None)
        ISBN13 = request.form.get("ISBN13", None)
        UserID = g.user["UserID"]
        error = None
        db = get_db()

        if BookID is None:
            abort(400)
        elif Title == "":
            error = "タイトルがありません"
        elif Location == "":
            error = "本の場所が入力されていません"

        if SeriesName == "":
            SeriesName = Title

        if error is None:
            flag = db.execute(
                """
                SELECT 1
                FROM Books
                WHERE
                    BookID = ?
                    AND UserID = ?
                """, (BookID, UserID)
            ).fetchone()
            if flag is None:
                abort(404)

        if error is None:
            LocationID = get_id(db, "Locations", "LocationName", "LocationID", Location, UserID)
            SeriesID = get_id(db, "Series", "SeriesName", "SeriesID", SeriesName, UserID)
            if PublisherName != "":
                PublisherID = get_id(db, "Publishers", "PublisherName", "PublisherID", PublisherName, UserID)
            else:
                PublisherID = None

            db.execute(
                """
                UPDATE Books
                SET
                    Title = ?,
                    LocationID = ?,
                    SeriesID = ?,
                    PublisherID = ?,
                    PublicationDate = ?,
                    ISBN10 = ?,
                    ISBN13 = ?
                WHERE BookID = ?;
                """, (
                    Title,
                    LocationID,
                    SeriesID,
                    PublisherID,
                    PublicationDate,
                    ISBN10,
                    ISBN13,
                    BookID
                )
            )
            db.commit()

            change_book_authors(db, UserID, BookID, Authors)

            return redirect(url_for('manager.index'))
        else:
            flash(error, 'info')

    BookID = request.args.get("BookID", None)
    UserID = g.user["UserID"]
    if BookID is None:
        abort(400)
    db = get_db()
    Book = db.execute(
        """
        SELECT
            Books.BookID,
            Books.Title,
            Locations.LocationName AS LocationName,
            Series.SeriesName AS SeriesName,
            COALESCE(Publishers.PublisherName, '') AS PublisherName,
            COALESCE(PublicationDate, '') AS PublicationDate,
            COALESCE(GROUP_CONCAT(Authors.AuthorName, ','), '') AS Authors,
            COALESCE(ISBN13, '') AS ISBN13,
            COALESCE(ISBN10, '') AS ISBN10
        FROM Books
        JOIN Locations ON Locations.LocationID = Books.LocationID
        JOIN Series ON Series.SeriesID = Books.SeriesID
        LEFT JOIN Publishers ON Publishers.PublisherID = Books.PublisherID
        LEFT JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
        LEFT JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
        WHERE Books.BookID = ? AND Books.UserID = ?
        GROUP BY Books.BookID
        """, (BookID, UserID)
    ).fetchone()
    if Book is None:
        abort(404)
    else:
        Book = dict(Book)

    datalist = get_datalist(db, UserID)

    return render_template("book_edit.html", Book=Book, datalist=datalist)

def change_seriesname(SeriesName, UserID, SeriesID):
    db = get_db()
    error = None
    exists = db.execute(
        "SELECT 1 FROM Series WHERE SeriesName = ? AND UserID = ?",
        (SeriesName, UserID)
    ).fetchone()
    if exists is not None:
        return None, f"シリーズ名 {SeriesName} は既に登録されています。"
    db.execute(
        "UPDATE Series SET SeriesName = ? WHERE SeriesID = ?",
        (SeriesName, SeriesID)
    )
    db.commit()
    return "シリーズ名を変更しました", None


def change_series_authors(db, Authors, SeriesID, UserID):
    if Authors == "":
        return None, "著者名が入力されていません"
    Authors = set(Authors.split(","))
    Authors.discard("")
    db.execute(
        """
        DELETE FROM BookAuthors
        WHERE
            BookAuthors.BookID IN (
                SELECT Books.BookID
                FROM Books
                WHERE SeriesID = ?
            );
        """, (SeriesID,)
    )
    for author in Authors:
        AuthorID = get_id(db, "Authors", "AuthorName", "AuthorID", author, UserID)
        db.execute(
            """
            INSERT INTO BookAuthors (BookID, AuthorID)
            SELECT Books.BookID, ?
            FROM Books
            WHERE Books.SeriesID = ?;
            """, (AuthorID, SeriesID)
        )
    db.commit()
    return "著者を変更しました", None


def change_publisher(db, PublisherName, SeriesID, UserID):
    PublisherID = get_id(db, "Publishers", "PublisherName", "PublisherID", PublisherName, UserID)
    db.execute(
        """
        UPDATE Books
        SET PublisherID = ?
        WHERE SeriesID = ?
        """, (PublisherID, SeriesID)
    )
    db.commit()
    return "出版社名を変更しました", None

def get_series_edit_forms():
    """_summary_

    Category
    --------
    SeriesName
        シリーズ名変更
    Authors
        著者をまとめて変更
    Publishers
        出版社をまとめて変更

    Returns
    -------
    (str or None), (str or None)
        成功メッセージか、エラーメッセージか
    """
    SeriesID = request.form.get("SeriesID", None)
    msg = error = None

    if SeriesID is None:
        abort(400)
    db = get_db()
    UserID = g.user["UserID"]
    exists = db.execute(
        "SELECT 1 FROM Series WHERE SeriesID = ? AND UserID = ?",
        (SeriesID, UserID)
    ).fetchone()
    if exists is None:
        abort(404)

    category = request.form.get("category", None)

    if category == "SeriesName":
        # シリーズ名変更
        name = request.form.get("NewSeriesName", "")
        if name == "":
            error = "シリーズ名が入力されていません。"
        else:
            msg, error = change_seriesname(name, UserID, SeriesID)
    elif category == "Authors":
        # 著者変更
        names = request.form.get("AuthorsName", "")
        msg, error = change_series_authors(db, names, SeriesID, UserID)
    elif category == "Publisher":
        # 出版社名変更
        name = request.form.get("PublisherName", "")
        if name == "":
            error = "出版社名が入力されていません"
        else:
            msg, error = change_publisher(db, name, SeriesID, UserID)
    else:
        abort(400)

    return msg, error


@bp.route("/series_edit", methods=("GET", "POST"))
@login_required
def series_edit():
    if request.method == "POST":
        msg, error = get_series_edit_forms()

        if error is not None:
            flash(error, 'info')
        else:
            flash(msg, 'success')

    SeriesID = request.args.get("SeriesID", None)
    if SeriesID is None:
        abort(400)
    db = get_db()
    UserID = g.user["UserID"]
    SeriesData = db.execute(
        """
        SELECT
            Series.SeriesID AS SeriesID,
            Series.SeriesName AS SeriesName,
            (
                SELECT COALESCE(Publishers.PublisherName, '')
                FROM Books
                LEFT JOIN Publishers ON Books.PublisherID = Publishers.PublisherID
                WHERE
                    Books.SeriesID = ?
                GROUP BY Publishers.PublisherID
                ORDER BY COUNT(*) DESC
                LIMIT 1
            ) AS PublisherName,
            COALESCE(GROUP_CONCAT(Authors.AuthorName, ','), '') AS Authors
        FROM Series
        JOIN Books ON Books.SeriesID = Series.SeriesID
        LEFT JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
        LEFT JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
        WHERE
            Series.SeriesID = ?
            AND Series.UserID = ?
        GROUP BY Series.SeriesID;
        """, (SeriesID, SeriesID, UserID)
    ).fetchone()
    if SeriesData is None:
        abort(404)

    datalist = get_datalist(db, UserID)

    return render_template("series_edit.html", SeriesData=SeriesData, datalist=datalist)