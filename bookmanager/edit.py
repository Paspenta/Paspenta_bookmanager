from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

from .manager import (
    bp, get_id
)

@bp.route("/volume_edit", methods=("GET", "POST"))
@login_required
def volume_edit():
    if request.method == "POST":
        BookID = request.form.get("BookID")
        Title = request.form.get("Title")
        SeriesName = request.form.get("SeriesName")
        Location = request.form.get("LocationName")
        PublicationDate = request.form.get("PublicationDate")
        ISBN10 = request.form.get("ISBN13")
        ISBN13 = request.form.get("ISBN10")
        UserID = g.user["UserID"]
        error = None
        db = get_db()

        if BookID is None:
            error = "Nothing BookID"
        elif Title is None:
            error = "Nothing Title"
        elif SeriesName is None:
            error = "Nothing SeriesName"
        elif Location is None:
            error = "Nothing Location"
        
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
                error = "Not found Book"

        if error is None:
            LocationID = get_id(db, "Locations", "LocationName", "LocationID", Location, UserID)
            SeriesID = get_id(db, "Series", "SeriesName", "SeriesID", SeriesName, UserID)

            db.execute(
                """
                UPDATE Books
                SET
                    Title = ?,
                    LocationID = ?,
                    SeriesID = ?,
                    PublicationDate = ?,
                    ISBN10 = ?,
                    ISBN13 = ?
                WHERE BookID = ?;
                """, (
                    Title,
                    LocationID,
                    SeriesID,
                    PublicationDate,
                    ISBN10,
                    ISBN13,
                    BookID
                )
            )
            db.commit()

            return redirect(url_for('index'))
        else:
            flash(error, 'info')
    BookID = request.args.get("BookID", None)
    UserID = g.user["UserID"]
    if BookID is None:
        return 404
    db = get_db()
    Book = db.execute(
        """
        SELECT
            BookID,
            Title,
            Locations.LocationName AS LocationName,
            Series.SeriesName AS SeriesName,
            PublicationDate,
            ISBN10,
            ISBN13
        FROM Books
        JOIN Locations ON Locations.LocationID = Books.LocationID
        JOIN Series ON Series.SeriesID = Books.SeriesID
        WHERE BookID = ? AND Books.UserID = ?;
        """, (BookID, UserID)
    ).fetchone()
    if Book is None:
        return 404
    else:
        Book = {**Book}
    if Book["PublicationDate"] is None:
        Book["PublicationDate"] = ""
    if Book["ISBN10"] is None:
        Book["ISBN10"] = ""
    if Book["ISBN13"] is None:
        Book["ISBN13"] = ""
    return render_template("volume_edit.html", Book=Book)


@bp.route("/series_edit", methods=("GET", "POST"))
@login_required
def series_edit():
    if request.method == "POST":
        SeriesID = request.form.get("SeriesID", None)
        newSeriesName = request.form.get("SeriesName", "")
        PublisherName = request.form.get("PublisherName", None)
        AuthorName = request.form.get("Authors", "")
        new_authors = set(AuthorName.split(","))
        new_authors.discard("")
        UserID = g.user["UserID"]
        error = None
        db = get_db()

        if SeriesID is None and newSeriesName == "":
            error = "Nothing Series"
        else:
            PrevSeriesName = db.execute(
                """
                SELECT SeriesName
                FROM Series
                WHERE UserID = ? AND SeriesID = ?
                """, (UserID, SeriesID)
            ).fetchone()
            if PrevSeriesName is None:
                error = "Not found Series"
            else:
                PrevSeriesName = PrevSeriesName["SeriesName"]

        if error is None:
            if PrevSeriesName != newSeriesName:
                db.execute(
                    "UPDATE Series SET SeriesName = ? WHERE SeriesID = ?",
                    (newSeriesName, PrevSeriesName)
                )
            if PublisherName:
                PublisherID = get_id(db, "Publishers", "PublisherName", "PublisherID", PublisherName, UserID)
                db.execute(
                    "UPDATE Series SET PublisherID = ? WHERE SeriesID = ?",
                    (PublisherID, SeriesID)
                )
            prev_authors = db.execute(
                """
                SELECT
                    BookAuthors.AuthorID,
                    Authors.AuthorName AS AuthorName
                FROM BookAuthors
                JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
                WHERE SeriesID = ?
                """, (SeriesID,)
            ).fetchall()
            del_authors = set()
            for author in prev_authors:
                if author["AuthorName"] in new_authors:
                    new_authors.discard(author["AuthorName"])
                else:
                    del_authors.add(author["AuthorID"])
            for author in new_authors:
                AuthorID = get_id(db, "Authors", "AuthorName", "AuthorID", author, UserID)
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
            for AuthorID in del_authors:
                db.execute(
                    "DELETE FROM BookAuthors WHERE SeriesID = ? AND AuthorID = ?;",
                    (SeriesID, AuthorID)
                )
            db.commit()
            
            return redirect(url_for('index'))
            
        else:
            flash(error, 'info')

    SeriesID = request.args.get("SeriesID", None)
    if SeriesID is None:
        return "Nothing Series"
    db = get_db()
    UserID = g.user["UserID"]
    SeriesData = db.execute(
        """
        SELECT
            SeriesID,
            SeriesName,
            COALESCE(Publishers.PublisherName, '') AS PublisherName
        FROM Series
        LEFT JOIN Publishers ON Series.PublisherID = Publishers.PublisherID
        WHERE SeriesID = ? AND Series.UserID = ?;
        """, (SeriesID, UserID)
    ).fetchone()
    if SeriesData is None:
        return "Not found Series"
    Authors = db.execute(
        """
        SELECT Authors.AuthorName AS AuthorName
        FROM BookAuthors
        JOIN Authors ON Authors.AuthorID = BookAuthors.AuthorID
        WHERE SeriesID = ?;
        """, (SeriesID,)
    ).fetchall()
    Authors = ",".join([Author["AuthorName"] for Author in Authors])
    
    return render_template("series_edit.html", SeriesData=SeriesData, Authors=Authors)