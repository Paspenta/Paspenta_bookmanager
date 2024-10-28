from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db
from bookmanager.get_books import get_books

bp = Blueprint("manager", __name__)

ins_template = """
    INSERT INTO {table_name} ({col_name}, UserID)
    SELECT ?, ?
    WHERE NOT EXISTIS (
        SELECT 1
        FROM {table_name}
        WHERE
            {col_name} = ?
            AND UserID = ?
    );
    SELECT {getIDName}
    FROM {table_name}
    WHERE
        {col_name}= ?
        AND UserID = ?;
    """

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

    plus_parms = request.args.deepcopy()
    minus_parms = request.args.deepcopy()
    plus_parms["page"] = page+1
    minus_parms["page"] = page-1 if page>0 else 0
    
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
            WITH BookAuthors AS (
                SELECT AuthorID
                FROM BookAuthors
                WHERE SeriesID = ?
            )
            SELECT AuthorName
            FROM Authors
            WHERE AuthorID IN BookAuthors;
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
    
    return render_template("index.html",
                            Seriess=Seriess,
                            plus_parms=plus_parms,
                            minus_parms=minus_parms)

@bp.route("/volume_edit", medhods=("GET", "POST"))
@login_required
def volume_edit():
    if request.method == "POST":
        BookID = request.form["BookID"]
        Title = request.form["Title"]
        Location = request.form["LocaitonName"]
        PublicationDate = request.form["PublicationDate"]
        ISBN10 = request.form["ISBN13"]
        ISBN13 = request.form["ISBN10"]
        user_id = g.user["UserID"]
        db = get_db()

        LocationID = db.execute(
            ins_template.format(
                table_name="Locations",
                col_name="LocationName",
                getIDname="LocationID"
            ), tuple([Location, user_id] * 3)
        ).fetchone()

        db.execute(
            """
            UPDATE Books
            SET
                Title = ?,
                LocationID = ?,
                PublicationDate = ?,
                ISBN10 = ?,
                ISBN13 = ?
            WHERE BookID = ?
            """, (
                Title,
                LocationID,
                PublicationDate,
                ISBN10,
                ISBN13,
                BookID
            )
        )
        db.commit()
    else:
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
                PublicationDate,
                ISBN10,
                ISBN13
            FROM Books
            JOIN Locations ON Locations.LocationID = LocationID
            WHERE BookID = ? AND UserID = ?;
            """, (BookID, user_id)
        ).fetchone()
        if Book is None:
            return 404
        if Book["PublicationDate"] is None:
            Book["PublicationDate"] = ""
        if Book["ISBN10"] is None:
            Book["ISBN10"] = ""
        if Book["ISBN13"] is None:
            Book["ISBN13"] = ""
        return render_template("volume_edit.html", Book=Book)


@bp.route("/series_edit", medhods=("GET", "POST"))
@login_required
def series_edit():
    if request.method == "POST":
        SeriesID = request.form["SeriesID"]
        PublisherName = request.form["PublisherName"]
        AuthorName = request.form["Authors"]
        new_authors = set(AuthorName.split(","))
        new_authors.discard("")
        edit_series = request.get_json()
        user_id = g.user["UserID"]
        error = None
        db = get_db()

        series_existis = db.execute(
            """
            SELECT 1
            FROM Series
            WHERE UserID = ? AND SeriesID = ?
            """, (user_id, SeriesID)
        ).fetchone()
        if series_existis is None:
            error = "Not found Series"

        if error is None:
            if PublisherName:
                PublisherID = db.execute(
                    ins_template.format(
                        table_name="Publishers",
                        col_name="PublisherName",
                        getIDname="PublisherID"
                    ), tuple([PublisherName, user_id] * 3)
                ).fetchone()
                db.execute(
                    "UPDATE Series SET PublisherID = ? WHERE SeriesID = ?",
                    (PublisherID, SeriesID)
                )
            prev_authors = db.execute(
                """
                SELECT
                    AuthorID,
                    Authors.AuthorName AS AuthorName
                FROM BookAuthors
                JOIN Authors ON AuthorID = Authors.AuthorID
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
                AuthorID = db.execute(
                    ins_template.format(
                        table_name="Authors",
                        col_name="AuthorName",
                        getIDname="AuthorID"
                    ), tuple([AuthorName, user_id] * 3)
                ).fetchall()[0]
                db.execute(
                    """
                    INSERT INTO BookAuthors (SeriesID, AuthorID)
                    SELECT ?, ?
                    WHERE NOT EXISTIS (
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
                    "DELETE FROM BookAuthors WHERE SeriesID = ? AND AuthorID = ?;"
                    (SeriesID, AuthorID)
                )
            
        else:
            flash(error)
    else:
        SeriesID = request.args.get("SeriesID", None)
        if SeriesID is None:
            return 404
        db = get_db()
        user_id = g.user["UserID"]
        SeriesDate = db.execute(
            """
            SELECT
                SeriesID,
                SeriesName,
                Publishers.PublisherName AS PublisherName,
            FROM Series
            JOIN Publishers ON Publishers.PublisherID = PublisherID
            WHERE SeriesID = ? AND UserID = ?;
            """, (SeriesID, user_id)
        ).fetchone()
        if SeriesDate is None:
            return 404
        Authors = db.execute(
            """
            SELECT Authors.AuthorName AS AuthorName
            FROM BookAuthors
            JOIN Authors ON AuthorID = BookAuthors.AuthorID
            WHERE SeriesID = ?;
            """, (SeriesID,)
        ).fetchall()
        SeriesDate["Author"] = ",".join([Author["AuthorName"] for Author in Authors])
    
        return render_template("Series_edit,html", SeriesDate=SeriesDate)




@bp.route("/volume_del",methods=("POST",))
@login_required
def book_del():
    if request.method == "POST":
        BookID = request.form["BookID"]
        db = get_db()
        db.execute("DELETE FROM Books WHERE BookID = ?", (BookID,))
        db.commit()

@bp.route("/Series_del", methods=("POST",))
@login_required
def Series_del():
    if request.method == "POST":
        SeriesID = request.form["SeriesID"]
        db = get_db()
        db.execute("DELETE FROM Books WHERE SeriesID = ?;", (SeriesID,))
        db.execute("DELETE FROM Series WHERE SeriesID = ?;", (SeriesID,))
        db.execute("DELETE FROM BookAuthors WHERE SeriesID = ?;")
        db.commit()


@bp.route("/register", medhods=("GET", "POST"))
@login_required
def book_register():
    if request.method == "POST":
        Title = request.form["Title"]
        Series = request.form["Series"]
        Location = request.form["Location"]
        input_authors = request.form["Authors"]
        Publiser = request.form["Publisher"]
        PublicationDate = request.form["PulicationDate"]
        ISBN13 = request.form["ISBN13"]
        ISBN10 = request.form["ISBN10"]
        user_id = g.user["UserID"]
        db = get_db()
        error = None
        series = request.get_json()

        if not Title:
            error = "タイトルが入力されていません"
        elif not Location:
            error = "本の場所が入力されていません"
        
        if error is None:
            if not Series:
                Series = Title
            if Publiser:
                PubliserID = db.execute(
                    ins_template.format(
                        table_name="Publishers",
                        col_name="PublisherName",
                        getIDname="PubliserID"
                    ), tuple([Publiser, user_id] * 3)
                ).fetchall()[0]
            else:
                PubliserID = None
            authorsID = []
            if input_authors:
                for author in input_authors.split(","):
                    authorsID.append(
                        db.execute(
                            ins_template.format(
                                table_name="Authors",
                                col_name="AuthorName",
                                getIDname="AuthorID"
                            ), tuple([author, user_id] * 3)
                        ).fetchone()
                    )
            SeriesID = db.execute(
                ins_template.format(
                    table_name="Series",
                    col_name="SeriesName",
                    getIDname="SeriesID"
                ), tuple([Series, user_id] * 3)
            )
            LocationID = db.execute(
                ins_template.format(
                    table_name="Locations",
                    col_name="LocationName",
                    getIDname="LocationID"
                ), tuple([Location, user_id] * 3)
            )
            
            db.execute(
                """INSERT INTO Books (
                    Title,
                    UserID,
                    LocationID,
                    SeriesID,
                    PublisherID,
                    PublicationDate,
                    ISBN13,
                    ISBN10
                ) VALUE (
                    ?,
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
                    PubliserID, 
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
                    WHERE NOT EXISTIS (
                        SELECT 1
                        FROM BookAuthors
                        WHERE
                            SeriesID = ?
                            AND AuthorID = ?
                    );
                    """, tuple([SeriesID, AuthorID]*2)
                )
            db.commit()

        else:
            flash(error)
    else:
        Book = dict()
        Book["Title"] = request.args.get("title", "")
        Book["Series"] = Book["Title"]
        Book["author"] = request.args.get("author", "")
        Book["Publisher"] = request.args.get("publisher", "")
        Book["PublicationDate"] = request.args.get("publishe_date", "")
        Book["ISBN13"] = request.args.get("IsBN13", "")
        Book["ISBN10"] = request.args.get("IsBN10", "")
    
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

    books = get_books(q=keyword, intitle=title, author=author, isbn=isbn)

    return render_template("register_search.html", books)