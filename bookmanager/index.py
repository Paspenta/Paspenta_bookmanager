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
    """Overview
    本を一覧表示

    URL Parameters
    ----------
    SeriesName: str
        シリーズ名から検索する
    AuthorName: str
        著者名で検索
    PublisherName: str
        出版社名で検索
    LocationName: str
        本がある場所で検索
    
    Returns
    -------
    検索条件がある場合、検索条件に一致する本を表示
    検索条件がない場合、ユーザーが持つ本を表示
    """
    db = get_db()
    SeriesName = "%" + request.args.get("SeriesName", "") + "%"
    AuthorName = request.args.get("AuthorName", None)
    PublisherName = request.args.get("PublisherName", None)
    LocationName = "%" + request.args.get("LocationName", "") + "%"
    UserID = g.user["UserID"]

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
        """, (UserID, AuthorName,
            UserID, LocationName,
            UserID, SeriesName, PublisherName,
            page)
    ).fetchall()

    # series_listをsqlite.rowオブジェクトからdictに変換
    series_list = [dict(row) for row in series_list]

    for i in range(len(series_list)): # シリーズごとの情報
        series_data = series_list[i]
        add_data = dict()
        # 本がある場所を追加
        add_data["Locations"] = db.execute(
            """
            SELECT
                Locations.LocationName AS LocationName,
                COUNT(Books.LocationID) AS VolumeCount
            FROM Books
            JOIN Locations ON Books.LocationID = Locations.LocationID
            WHERE SeriesID = ?
            GROUP BY Books.LocationID
            ORDER BY `VolumeCount` DESC;
            """, (series_data["SeriesID"],)
        ).fetchall()
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
            """, (series_data["SeriesID"],)
        ).fetchall()
        add_data["Authors"] = ",".join([author["AuthorName"] for author in authors])

        add_data["volumes"] = db.execute(
            """
            SELECT
                BookID,
                Title,
                COALESCE(PublicationDate, "") AS PublicationDate,
                Locations.LocationName AS LocationName,
                COALESCE(ISBN13, ISBN10, "") AS ISBN
            FROM Books
            JOIN Locations ON Books.LocationID = Locations.LocationID
            WHERE SeriesID = ?
            ORDER BY Title;
            """, (series_list[i]["SeriesID"],)
        ).fetchall()

        parms = {
            "title":series_data["SeriesName"],
            "seriesName":series_data["SeriesName"],
            "publisher":series_data["PublisherName"],
            "author":add_data["Authors"],
            "Location":add_data["Locations"][0]["LocationName"]
        }
        add_data["add_volume_url"] = url_for('manager.register', **parms)

        series_list[i].update(add_data)
    
    return render_template("index.html",
                            series_list=series_list,
                            plus_parms=plus_parms,
                            minus_parms=minus_parms)