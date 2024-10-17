from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from bookmanager.db import get_db

bp = Blueprint("manager", __name__, url_prefix="/index")

@bp.route("/")
def index():
    db = get_db()
    db.execute(
        """
        SELECT id, outer_name AS name
        FROM outer_name;
        """
    )
    outers = db.fetchall()
    db.execute(
        """
        SELECT id, publisher_name AS name
        FROM publisher;
        """
    )
    Publishers = db.fetchall()
    db.execute(
        """
        SELECT id, site_name AS name
        FROM have_site;
        """
    )
    have_sites = db.fetchall()
    db.execute(
        f"""
        SELECT
            id,
            COALESCE(series.name, title) AS title,
            COALESCE(MAX(volume), -1) AS volume,
            outer_name.outer_name AS outer_name
            publisher.publisher_name AS publisher_name,
            have_site.site_name AS site_name
        FROM
            book
        GROUP BY COALESCE(series_id)
        LEFT JOIN series ON series_id = series.id
        JOIN outer_name ON outer_id = outer_name.id
        JOIN publisher ON publisher_id = publisher.id
        JOIN have_site ON site_id = have_site.id
        LIMIT 15 OFFSET { page * 15 }
        ORDER BY id;
        """
    )
    books = db.fetchall()

    return render_template("index.html",
                            title="index",
                            outers=outers,
                            Publishers=Publishers,
                            have_sites=have_sites,
                            books=books)
