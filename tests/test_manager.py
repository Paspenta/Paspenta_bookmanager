import pytest
from bookmanager.db import get_db
from bookmanager.manager import get_id, get_page, get_datalist

def test_get_id(app):
    with app.app_context():
        db = get_db()
        ret_id = get_id(db, "Publishers", "PublisherName", "PublisherID", "TestPublisher", 1)
        assert ret_id == 1

        ret_id = db.execute(
            "SELECT SeriesID FROM Series WHERE SeriesName = 'TestSeries1';"
        ).fetchall()
        assert len(ret_id) == 1

        ret_id = get_id(db, "Publishers", "PublisherName", "PublisherID", "NewPublisher", 1)
        assert ret_id == 5

        existis = db.execute(
            """
            SELECT 1
            FROM Publishers
            WHERE
                PublisherID = 5
                AND PublisherName = 'NewPublisher'
                AND UserID = 1;
            """
        ).fetchone()
        assert existis is not None


@pytest.mark.parametrize(
    ("page", "ret"), [
        ("1", 1),
        ("-1", 0),
        ("0", 0),
        ("a", 0),
        (dict(), 0),
        (None, 0)
    ]
)
def test_get_page(page, ret):
    assert get_page(page) == ret


@pytest.mark.parametrize('path', [
    "/", "/index_series",
    "/book_edit", "/series_edit",
    "/register", "/register_search",
    ]
)
def test_login_required(client, path):
    response = client.get(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize('path', [
    "/book_del", "/series_del"
    ]
)
def test_login_required_post(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"

def test_get_id(app):
    with app.app_context():
        db = get_db()
        UserID = 1
        assert get_datalist(db, UserID)
        assert not get_datalist(db, UserID, False, False, False, False)