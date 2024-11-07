from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

from .manager import (
    bp, get_page
)

def get_url_parameters():
    """_summary_
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
    ret: dict
        URLパラメタ
    """
    ret = {
        "Title": "%" + request.args.get("Title", "") + "%",
        "SeriesName": "%" + request.args.get("SeriesName", "") + "%",
        "AuthorName": "%" + request.args.get("AuthorName", "") + "%",
        "PublisherName": "%" + request.args.get("PublisherName", "") + "%",
        "LocationName": "%" + request.args.get("LocationName", "") + "%"
    }
    return ret


@bp.route("/")
@login_required
def index():
    """Overview
    本をシリーズごとに表示

    Returns
    -------
    検索条件がある場合、検索条件に一致する本を表示
    検索条件がない場合、ユーザーが持つ本を表示
    """
    db = get_db()
    UserID = g.user["UserID"]

    page = request.args.get("Page", "0")
    page = get_page(page)

    plus_parms = {**request.args}
    minus_parms = {**request.args}
    plus_parms["Page"] = page+1
    minus_parms["Page"] = page-1 if page>0 else 0

    series_list = db.execute(
        """
        SELECT
            Series.SeriesID AS SeriesID,
            SeriesName,
            COALESCE(GROUP_CONCAT(Publishers.PublisherName, ','), '') AS PublisherName,
            COALESCE(GROUP_CONCAT(Authors.AuthorName, ','), '') AS Authors
        FROM Series
        JOIN Books ON Series.SeriesID = Books.SeriesID
        LEFT JOIN Publishers ON Series.PublisherID = Publishers.PublisherID
        LEFT JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
        LEFT JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
        WHERE
            Series.UserID = ?
            AND SeriesName LIKE ?
            AND Books.Title LIKE ?
        GROUP BY SeriesID
        HAVING
            `PublisherName` LIKE ?
            AND `Authors` LIKE ?
        LIMIT 15 OFFSET ?;
        """, (
        UserID, SeriesName, Title, PublisherName, AuthorName, page)
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