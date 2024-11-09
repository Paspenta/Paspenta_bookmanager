import pytest
from bookmanager.db import get_db
from bookmanager.manager import get_id, get_page

def test_get_id(app):
    with app.app_context():
        db = get_db()
        ret_id = get_id(db, "Publisers", "PublisherName", "PublisherID", "TestPublisher", 1)
        assert ret_id == 1

        ret_id = db.execute(
            "SELECT SeriesID FROM Series WHERE SeriesName = 'TestSeries';"
        ).fetchall()
        assert len(ret_id) == 1

        ret_id = get_id(db, "Publisers", "PublisherName", "PublisherID", "NewPublisher", 1)
        assert ret_id == 3

        existis = db.execute(
            """
            SELECT 1
            FROM Publishers
            WHERE
                PublisherID = 3
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
    "/volume_del", "/series_del"
    ]
)
def test_login_required(client, path):
    response = client.get(path)
    assert response.headers["Location"] == "/auth/login"