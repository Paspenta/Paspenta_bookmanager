from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

from .manager import (
    bp, get_page
)


@bp.route("/")
@login_required
def index():
    db = get_db()
    SeriesName = "%" + request.args.get("SeriesName", "") + "%"
    AuthorName = request.args.get("AuthorName", None)
    PublisherName = request.args.get("PublisherName", None)
    LocationName = "%" + request.args.get("LocationName", "") + "%"
    user_id = g.user["UserID"]

    page = request.args.get("Page", "0")
    page = get_page(page)

    plus_parms = {**request.args}
    minus_parms = {**request.args}
    plus_parms["Page"] = page+1
    minus_parms["Page"] = page-1 if page>0 else 0

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
    series_list = db.execute(
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

    series_list = [dict(row) for row in series_list]
    for i in range(len(series_list)):
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
            """, (series_list[i]["SeriesID"],)
        ).fetchall()
        series_list[i]["Authors"] = [author["AuthorName"] for author in authors]
        series_list[i]["volumes"] = db.execute(
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
            """, (series_list[i]["SeriesID"],)
        ).fetchall()
    
    return render_template("index.html",
                            series_list=series_list,
                            plus_parms=plus_parms,
                            minus_parms=minus_parms)