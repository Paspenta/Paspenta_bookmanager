from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from bookmanager.db import get_db

bp = Blueprint("manager", __name__, url_prefix="/index")

@bp.route("/")
def index():
    db = get_db()


    return render_template("index.html",
                            title="index",
                            outers=outers,
                            Publishers=Publishers,
                            have_sites=have_sites,
                            books=books)
