import pytest
from bookmanager.db import get_db
response = ""


get_no_change_book_sql = """
    SELECT 1
    FROM Books
    JOIN Series ON Series.SeriesID = Books.SeriesID
    LEFT JOIN Publishers ON Publishers.PublisherID = Books.PublisherID
    LEFT JOIN BookAuthors ON BookAuthors.BookID = Books.BookID
    LEFT JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
    WHERE
        BookID = 1
        AND Series.SeriesName = "TestSeries1"
        AND Publishers.PublisherName = "TestPublisher"
        AND Authors.AuthorName = "TestAuthor1";
    """

@pytest.mark.parametrize(
    ("flag", "AuthorName", "PublisherName", "SeriesName"), [
        (True, "AfterAuthor", "AfterPublisher", "AfterSeries"),
        (False, None, None, None)
    ]
)
def test_book_edit(client, auth, app, flag, AuthorName, PublisherName, SeriesName):
    """
    書籍情報を正常に編集できるかをテスト
    """
    auth.login()

    data={
        "BookID":1,
        "Title":"AfterTitle",
        "LocationName":"AfterLocation",
        "PublicationDate":"AfterDate",
        "ISBN10":"afterISBN10",
        "ISBN13":"afterISBN13"
    }
    if flag:
        data["SeriesName"] = SeriesName
        data["Authors"] = AuthorName
        data["PublisherName"] = PublisherName

    # getした時、formに初期値が入力されているか
    response = client.get("/book_edit?BookID=1")
    html = response.data.decode("utf-8")
    book_datas = [
        "TestBook1", "TestSeries", "TestPublisher",
        "TestAuthor1", "TestLocation",
        "xxxx-xx-xx", "1234567890123", "1234567890"
    ]
    for book_data in book_datas:
        assert book_data in html

    # 編集完了した後indexに遷移するか
    response = client.post("/book_edit", data=data)
    assert response.headers["Location"] == "/"

    # 編集されているか確認
    with app.app_context():
        db = get_db()
        after_book = db.execute(
            """
            SELECT
                Books.BookID AS BookID,
                Title,
                Series.SeriesName AS SeriesName,
                Publishers.PublisherName AS PublisherName,
                Locations.LocationName AS LocationName,
                Authors.AuthorName AS Authors,
                PublicationDate,
                ISBN10,
                ISBN13
            FROM Books
            JOIN Series ON Books.SeriesID = Series.SeriesID
            JOIN Locations ON Books.LocationID = Locations.LocationID
            LEFT JOIN BookAuthors.BookID = Books.BookID
            LEFT JOIN Authors ON Authors.AuthorID, BookAuthors.AuthorID
            LEFT JOIN Publishers ON Publishers.PublisherID, Publishers.PublisherID
            WHERE Books.BookID = 1;
            """
        ).fetchone()
        assert after_book is not None
        # 正常に更新されているならばformのデータと同じになるはず
        for key, v in data.items():
            assert after_book[key] == v
        # 空文字列を許可するform項目の検証
        if not flag:
            # SeriesNameが空ならタイトルが代入されているはず
            assert after_book["SeriesName"] == "AfterTitle"
            # PublisherName, Authorsが空ならばNULL値がINSERTされているはず
            assert after_book["PublisherName"] is None
            assert after_book["Authors"] is None


@pytest.mark.parametrize(
    ("BookID", "status_code"), [
        (2, 404),
        (404, 404)
    ]
)
def test_book_edit_validate(client, auth, app, BookID, status_code):
    """
    book_editに無効な入力をして適切なエラーが表示されるか
    """
    auth.login()

    data = {"BookID":1}

    # BookIDなしでpost, get
    assert client.post("/book_edit", follow_redirects=True).status_code == 400
    assert client.get("/book_edit").status_code == 400

    # bookIDあり、タイトルなしでpost
    response = client.post("/book_edit", data=data, follow_redirects=True)
    html = response.data.decode("utf-8")
    assert "タイトルがありません" in html

    # BookID・TitleありLocationなしでPOST
    data["Title"] = "validate_title"
    response = client.post("/book_edit", data=data, follow_redirects=True)
    html = response.data.decode("utf-8")
    assert "本の場所が入力されていません" in html

    # 他ユーザーの所有するBookIDと存在しないBookIDでget, post
    data["BookID"] = BookID
    assert client.post("/book_edit", data=data, follow_redirects=True).status_code == status_code
    assert client.get(f"/book_edit?BookID={BookID}").status_code == status_code

    # 変更されていないか
    with app.app_context():
        db = get_db()
        exists = db.execute(get_no_change_book_sql).fetchone
        assert exists is not None


@pytest.mark.parametrize(
    ("category", "formkey", "name", "msg"), [
        ("SeriesName", "NewSeriesName", "AfterSeries", "シリーズ名を変更しました"),
        ("Authors", "AuthorsName", "AfterAuthor", "著者を変更しました"),
        ("Publisher", "PublisherName", "AfterPublisher", "出版社名を変更しました")
    ]
)
def test_series_edit(client, auth, app, category, formkey, name, msg):
    """_summary_
    シリーズを正常に編集できるかテスト
    """
    auth.login()

    # getした時にシリーズの情報がform初期値として入力されているか
    response = client.get("/series_edit?SeriesID=1")
    html = response.data.decode("utf-8")
    series_datas = ["TestSeries1", "TestPublisher", "TestAuthor1"]
    for series_data in series_datas:
        assert series_data in html

    # 各項目を変更
    response = client.post("/series_edit", data={
        "SeriesID":1,
        "category":category,
        formkey:name
    })
    html = response.data.decode("utf-8")
    assert msg in html

    # データが編集されているか確認
    with app.app_context():
        db = get_db()
        after_books = db.execute(
            """
            SELECT
                SeriesName AS NewSeriesName,
                Publishers.PublisherName AS PublisherName,
                Authors.AuthorName AS AuthorsName
            FROM Books
            JOIN Series ON Series.SeriesID = Books.SeriesID
            LEFT JOIN Publishers ON Publishers.PublisherID = Books.PublisherID
            LEFT JOIN BookAuthors ON BookAuthors.BookID = Books.BookID
            LEFT JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
            WHERE Books.SeriesID = 1;
            """
        ).fetchall()
        assert len(after_books) == 2
        for book in after_books:
            assert book[formkey] == name


@pytest.mark.parametrize(
    ("category", "formkey", "error"), [
        ("SeriesName", "NewSeriesName", "シリーズ名が入力されていません"),
        ("Authors", "AuthorsName", "著者名が入力されていません"),
        ("Publisher", "PublisherName", "出版社名が入力されていません")
    ]
)
def test_series_edit_validate(client, auth, app, category, formkey, error):
    """_summary_
    series_editに無効なリクエストをした時適切なエラーが出力されるか
    """
    auth.login()

    # SeriesIDなし
    assert client.get("/series_edit").status_code == 400
    assert client.post("/series_edit", follow_redirects=True).status_code == 400

    # 他ユーザーのシリーズを指定
    assert client.post("/series_edit?SeriesID=2", follow_redirects=True).status_code == 404
    assert client.post("/series_edit?", data={"SeriesID":2}, follow_redirects=True).status_code == 404

    # 存在しないシリーズID
    assert client.post("/series_edit?SeriesID=404", follow_redirects=True).status_code == 404
    assert client.post("/series_edit", data={"SeriesID":404}, follow_redirects=True).status_code == 404

    # 無効なカテゴリ
    assert client.post("/series_edit", data={
        "SeriesID":1,
        "category":"invalid"
    }).status_code == 400

    # 各項目を検証, 空文字列
    response = client.post("/series_edit", data={
        "SeriesID":1,
        "category":category,
        formkey:""
    })
    html = response.data.decode("utf-8")
    assert error in html
    # 各項目を検証, formkeyなし
    response = client.post("/series_edit", data={
        "SeriesID":1,
        "category":category
    })
    html = response.data.decode("utf-8")
    assert error in html

    # 変更されていないか
    with app.app_context():
        db = get_db()
        exists = db.execute(get_no_change_book_sql).fetchone
        assert exists is not None