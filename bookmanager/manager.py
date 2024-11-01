from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db
from bookmanager.get_books import get_books

bp = Blueprint("manager", __name__)


def get_id(db, table_name, col_name, id_name, name, user_id):
    insert_template = """
        INSERT INTO {table_name} ({col_name}, UserID)
        SELECT ?, ?
        WHERE NOT EXISTS (
            SELECT 1
            FROM {table_name}
            WHERE
                {col_name} = ?
                AND UserID = ?
        );
        """
    select_template = """
        SELECT {get_id_name}
        FROM {table_name}
        WHERE
            {col_name}= ?
            AND UserID = ?;
        """
    
    insert_parms = (name, user_id, name, user_id)
    db.execute(insert_template.format(
        table_name=table_name,
        col_name = col_name
    ), insert_parms)

    select_parms = (name, user_id)
    ret = db.execute(select_template.format(
        get_id_name=id_name,
        table_name=table_name,
        col_name=col_name
    ), select_parms).fetchall()
    db.commit()

    return ret[0][id_name] if ret else None

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


@bp.route("/book_delete", methods=("POST",))
@login_required
def book_delete():
    BookID = request.args.get("BookID")
    SeriesID = request.args.get("SeriesID")


@bp.route("/volume_del",methods=("POST",))
@login_required
def volume_del():
    if request.method == "POST":
        BookID = request.args.get("BookID")
        user_id = g.user["UserID"]
        db = get_db()
        SeriesID = db.execute(
            """
            SELECT SeriesID
            FROM Books
            WHERE
                BookID = ?
                AND UserID = ?;
            """, (BookID, user_id)
        ).fetchone()
        if SeriesID is not None:
            SeriesID = SeriesID["SeriesID"]
            db.execute(
                "DELETE FROM Books WHERE BookID = ? AND UserID = ?",
                (BookID, user_id)
            )
            db.execute(
                """
                DELETE FROM Series
                WHERE 
                    SeriesID = ?
                    AND NOT EXISTS (
                        SELECT 1
                        FROM Books
                        WHERE
                            SeriesID = ?
                        )
                """, (SeriesID, SeriesID)
            )
            db.commit()
        
        return redirect(url_for('index'))

@bp.route("/series_del", methods=("POST",))
@login_required
def series_del():
    if request.method == "POST":
        SeriesID = request.args.get("SeriesID")
        user_id = g.user["UserID"]
        db = get_db()
        flag = db.execute(
            """
            SELECT SeriesID
            FROM Series
            WHERE
                SeriesID = ?
                AND UserID = ?
            """, (SeriesID, user_id)
        ).fetchone()
        if flag is not None:
            db.execute("DELETE FROM Books WHERE SeriesID = ?;", (SeriesID,))
            db.execute("DELETE FROM Series WHERE SeriesID = ?;", (SeriesID,))
            db.execute("DELETE FROM BookAuthors WHERE SeriesID = ?;", (SeriesID,))
            db.commit()
        return redirect(url_for('index'))


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
        user_id = g.user["UserID"]
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
                PublisherID = get_id(db, "Publishers", "PublisherName", "PublisherID", Publisher, user_id)
            else:
                PublisherID = None
            authorsID = []
            if input_authors:
                for author in input_authors.split(","):
                    authorsID.append(
                        get_id(db, "Authors", "AuthorName", "AuthorID", author, user_id)
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
                """, (Series, PublisherID, user_id, Series, user_id)
            )
            SeriesID = db.execute(
                """
                SELECT SeriesID
                FROM Series
                WHERE
                    SeriesName = ?
                    AND UserID = ?
                """, (Series, user_id)
            ).fetchone()["SeriesID"]

            LocationID = get_id(db, "Locations", "LocationName", "LocationID", Location, user_id)
            
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
                    user_id,
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
    Book["Series"] = Book["Title"]
    Book["author"] = request.args.get("author", "")
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