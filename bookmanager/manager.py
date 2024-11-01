from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

bp = Blueprint("manager", __name__)


def get_id(db, table_name, col_name, id_name, name, user_id):
    """Overview

    指定の名前とユーザーIDの組み合わせが、存在しなければIDをINSERTする。
    作成したか、既存のIDを返す。

    Parameters
    ----------
    db: sqlite3.Connection
        データベース接続オブジェクト
    table_name: str
        挿入先及び取得先テーブル名
    col_name: str
        挿入・取得する基準となる名前の列名
    id_name: str
        挿入・取得するIDの列名
    name: str
        挿入・取得する基準となる名前
    user_id: str
        挿入・取得するIDをもつユーザーID
    
    Returns
    -------
    ret: str
        取得したID
    
    Examples
    --------
    >>> get_id(db, 'Publishers', 'PublisherName', 'PublisherID', 'KADOKAWA', 1)
    "2"
    """
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