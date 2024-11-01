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


@bp.route("/")
@login_required
def index():
    db = get_db()
    SeriesName = "%" + request.args.get("SeriesName", "") + "%"
    AuthorName = request.args.get("AuthorName", None)
    PublisherName = request.args.get("PublisherName", None)
    LocationName = "%" + request.args.get("LocationName", "") + "%"

    page = request.args.get("Page", "0")
    user_id = g.user["UserID"]

    page = get_page(page)

    plus_parms = {**request.args}
    minus_parms = {**request.args}
    plus_parms["page"] = page+1
    minus_parms["page"] = page-1 if page>0 else 0

    if PublisherName is not None:
        PublisherName = "%" + PublisherName + "%"
        where_publisher = "`PublisherName` = ?"
    else:
        where_publisher = "? IS NULL"
    
    if AuthorName is not None:
        AuthorName = "%" + AuthorName + "%"
        where_authorname = "Authors.AuthorName LIKE ?"
        use_filter = "AND Series.SeriesID IN (SELECT SeriesID FROM AuthorFilter)"
    else:
        where_authorname = "? IS NULL"
        use_filter = ""
    Seriess = db.execute(
        f"""
        WITH AuthorFilter AS (
            SELECT BookAuthors.SeriesID
            FROM BookAuthors
            WHERE BookAuthors.AuthorID IN (
                SELECT Authors.AuthorID
                FROM Authors
                WHERE 
                    Authors.UserID = ?
                    AND {where_authorname}
            )
        ),
        LocationsFilter AS (
            SELECT Books.SeriesID
            FROM Books
            WHERE Books.LocationID IN (
                SELECT Locations.LocationID
                FROM Locations
                WHERE
                    Locations.UserID = ?
                    AND Locations.LocationName LIKE ?
            )
        )
        SELECT
            Series.SeriesID,
            SeriesName,
            Publishers.PublisherName AS PublisherName
        FROM Series
        LEFT JOIN Publishers ON Series.PublisherID = Publishers.PublisherID
        WHERE
            Series.UserID = ?
            AND SeriesName LIKE ?
            AND {where_publisher}
            AND Series.SeriesID IN (SELECT SeriesID FROM LocationsFilter)
            {use_filter}
        LIMIT 15 OFFSET ?;
        """, (user_id, AuthorName,
            user_id, LocationName,
            user_id, SeriesName, PublisherName,
            page)
    ).fetchall()

    Seriess = [dict(row) for row in Seriess]
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
            FROM Books
            JOIN Locations ON Books.LocationID = Locations.LocationID
            WHERE SeriesID = ?
            ORDER BY Title;
            """, (Seriess[i]["SeriesID"],)
        ).fetchall()
    
    return render_template("index.html",
                            Seriess=Seriess,
                            plus_parms=plus_parms,
                            minus_parms=minus_parms)

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
        user_id = g.user["UserID"]
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
                """, (BookID, user_id)
            ).fetchone()
            if flag is None:
                error = "Not found Book"

        if error is None:
            LocationID = get_id(db, "Locations", "LocationName", "LocationID", Location, user_id)
            SeriesID = get_id(db, "Series", "SeriesName", "SeriesID", SeriesName, user_id)

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
            flash(error)
    BookID = request.args.get("BookID", None)
    user_id = g.user["UserID"]
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
        """, (BookID, user_id)
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
        user_id = g.user["UserID"]
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
                """, (user_id, SeriesID)
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
                PublisherID = get_id(db, "Publishers", "PublisherName", "PublisherID", PublisherName, user_id)
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
                AuthorID = get_id(db, "Authors", "AuthorName", "AuthorID", author, user_id)
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
            flash(error)

    SeriesID = request.args.get("SeriesID", None)
    if SeriesID is None:
        return "Nothing Series"
    db = get_db()
    user_id = g.user["UserID"]
    SeriesData = db.execute(
        """
        SELECT
            SeriesID,
            SeriesName,
            COALESCE(Publishers.PublisherName, '') AS PublisherName
        FROM Series
        LEFT JOIN Publishers ON Series.PublisherID = Publishers.PublisherID
        WHERE SeriesID = ? AND Series.UserID = ?;
        """, (SeriesID, user_id)
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