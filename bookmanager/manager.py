from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bookmanager.auth import login_required
from bookmanager.db import get_db

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