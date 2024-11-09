from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

from .manager import (
    bp
)

@bp.route("/book_del", methods=("POST",))
@login_required
def book_del():
    BookID = request.args.get("BookID", None)
    UserID = g.user["UserID"]
    db = get_db()

    if BookID is None:
        abort(400)

    SeriesID = db.execute(
        """
        SELECT SeriesID
        FROM Books
        WHERE
            BookID = ?
            AND UserID = ?;
        """, (BookID, UserID)
    ).fetchone()
    if SeriesID is not None:
        SeriesID = SeriesID["SeriesID"]
        db.execute(
            "DELETE FROM Books WHERE BookID = ?",
            (BookID,)
        )
        db.execute(
            "DELETE FROM BookAuthors WHERE BookID = ?",
            (BookID,)
        )
        db.execute(
            """
            DELETE FROM Series
            WHERE SeriesID = ?
            AND NOT EXISTS (
                SELECT 1 FROM Books WHERE SeriesID = ?
            );
            """, (SeriesID, SeriesID)
        )
        db.commit()
    else:
        abort(404)

    return redirect(url_for('manager.index'))


@bp.route("/series_del", methods=("POST",))
@login_required
def series_del():
    SeriesID = request.args.get("SeriesID", None)
    if SeriesID is None:
        abort(400)
    UserID = g.user["UserID"]
    db = get_db()
    flag = db.execute(
        """
        SELECT SeriesID
        FROM Series
        WHERE
            SeriesID = ?
            AND UserID = ?
        """, (SeriesID, UserID)
    ).fetchone()
    if flag is not None:
        db.execute(
            """
            DELETE FROM BookAuthors
            WHERE BookAuthors.BookID IN (
                SELECT Books.BookID
                FROM Books
                WHERE SeriesID = ?
            );
            """, (SeriesID,)
        )
        db.execute("DELETE FROM Books WHERE SeriesID = ?;", (SeriesID,))
        db.execute("DELETE FROM Series WHERE SeriesID = ?;", (SeriesID,))
        db.commit()
    else:
        abort(404)
    return redirect(url_for('manager.index'))