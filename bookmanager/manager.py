from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

bp = Blueprint("manager", __name__)

@bp.route("/")
@login_required
def index():

    db = get_db()
    title = request.args.get("book_title", "%")
    author = request.args.get("author", "%")
    have_site = request.args.get("have_site", "%")
    publisher = request.args.get("publisher", "%")
    page = request.args.get("page", 0)
    user_id = g.user["id"]

    try:
        page = int(page)
    except:
        page = 0
    
    books = db.execute(
        """
        SELECT
            title.id AS id
            title.title AS title
            author_name.author_name AS author,
            MAX(volume) AS volume,
            publisher.publisher_name AS publisher,
            have_site.site_name AS have_site,
            COALESCE(publication_date, "") AS publication_date
        FROM book
        JOIN title ON title_id = title.id
        JOIN publisher ON publisher_id = publisher.id
        JOIN have_site ON site_id = have_site.id
        WHERE
            user_id = ?
            AND `title` = ?
            AND `author` = ?
            AND `publisher` = ?
            AND `have_site` = ?
        GROUP BY title_id
        LIMIT 15 OFFSET ?;
        """, (user_id, title, author, publisher, have_site, page*15)
    ).fetchall()

    parms = request.args
    minus_parms = parms
    minus_parms["page"] = page-1
    plus_parms = parms
    plus_parms["page"] = page+1

    return render_template("index.html",
                           minus_parms=minus_parms,
                           plus_parms=plus_parms,
                           books=books)

@bp.route("/edit")
@login_required
def edit():
    title_id = request.args.get("id", False)
    if title_id:
        db = get_db()
        user_id = g.user["id"]
        series = db.execute(
            """
            SELECT
                title.title AS title
                author_id,
                author_name.author_name AS author_name,
                publisher_id,
                publisher.publisher_name AS publisher_name
                FROM book
                JOIN author_name ON author_id = author_name.id
                JOIN publisher ON publisher_id = publisher.publisher_name
                WHERE
                    title_id = ?
                    AND user_id = ?
                LIMIT 1
                """, (title_id, user_id)
        ).fetchone()
        if series:
            books = db.execute(
                """
                SELECT
                    id,
                    volume,
                    publication_date,
                    isbn
                FROM book
                WHERE title_id = ?
                """
            ).fetchall()
        else:
            books = []
    else:
        series = []
        books = []

    return render_template("edit.html", series, books)