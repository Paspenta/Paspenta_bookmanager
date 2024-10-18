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