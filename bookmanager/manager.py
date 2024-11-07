from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

bp = Blueprint("manager", __name__)


def get_id(db, table_name, col_name, id_name, name, UserID):
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
    UserID: int
        挿入・取得するIDをもつユーザーID

    Returns
    -------
    ret: str
        取得したID

    Examples
    --------
    >>> get_id(db, 'Publishers', 'PublisherName', 'PublisherID', 'KADOKAWA', 1)
    2
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
    
    # 挿入用テンプレート
    select_template = """
        SELECT {get_id_name}
        FROM {table_name}
        WHERE
            {col_name}= ?
            AND UserID = ?;
        """
    
    # 挿入
    insert_parms = (name, UserID, name, UserID)
    db.execute(insert_template.format(
        table_name=table_name,
        col_name = col_name
    ), insert_parms)

    # 取得
    select_parms = (name, UserID)
    ret = db.execute(select_template.format(
        get_id_name=id_name,
        table_name=table_name,
        col_name=col_name
    ), select_parms).fetchall()
    db.commit()

    return ret[0][id_name]


def get_page(page_str):
    """Overview
    文字列として取得したページをintに変換する。

    Parameters
    ----------
    page_str: str
        ページ数(文字列)
    
    Returns
    -------
    ret: int
        intに変換したページ数
        intに変換できなければ0を返す
    
    Examples
    --------
    >>> get_page("2")
    2
    >>> get_page("a")
    0
    """
    if page_str is None:
        # Noneであれば0
        return 0
    try:
        ret = int(page_str)
        if ret < 0:
            ret = 0
    except (ValueError, TypeError):
        # 数値ではないか、変換できない型の場合0
        ret = 0
    
    return ret