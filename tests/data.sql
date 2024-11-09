INSERT INTO Users (UserName, Password)
VALUES
    /* passwrod: test_password */
    ("test", "scrypt:32768:8:1$8uZscSUuCdRPqJEs$b92a17217171f9d72d9b2e9899e2b2c88d090f91e8ae7f02d937961c80090da8a24c889f8018f7c6c498dc6ba9cf526c934cb57a2974a2c26b67ead223e18186"),
    /* password: other_password */
    ("other", "scrypt:32768:8:1$I4mIy0QdfpRfB62m$b8491a038c9984da03e51d7e109c1300ad004afc1cfd3eea0f810cefa9560633dc3b1a9025285cb628ddf621b2ee299f852a4c5b86daf21d26491e638dce551d"),
    /* password: before */
    ("change_before", "scrypt:32768:8:1$LIixhld2dFVxpATJ$5d8f12d451b391ea4049f97c84b45d2d1235a01bc1211f1d57d42eaa7c89a1a69963c9df0a48b81793cca494a5bc0218aeee8352eb073f61f3abb6ef996fe626"),
    /* password: delete_password */
    ("delete_validate", "scrypt:32768:8:1$AfJ0Rihey4ZzS3hB$a1138aaa881500fdad5b432f75d61b57252db8241e6a6272f663737455afac1ada89cba0a813588c678d5645e165fc2e120d4c0ad43b7f692ba729ccd486ce4c");

INSERT INTO Publishers (PublisherName, UserID)
VALUES
    ("TestPublisher", 1),
    ("OtherPublisher", 2),
    ("DeletePublisher", 4),
    ("SearchPythonPublisher4", 1);

INSERT INTO Series (SeriesName, UserID)
VALUES
    ("TestSeries1", 1),
    ("OtherSeries", 2),
    ("DeleteSeries", 4),
    ("TestSeries2", 1),
    ("SearchGolangSeries5", 1),
    ("S_P_Series6", 1),
    ("S_JS_Series7", 1),
    ("S_GL_Series8", 1),
    ("S_FL_Series9", 1),
    ("S_NV_Series10", 1),
    ("CONCAT_Series11", 1);

INSERT INTO Authors (AuthorName, UserID)
VALUES
    ("TestAuthor1", 1),
    ("OtherAuthors", 2),
    ("DeleteAuthors1", 4),
    ("CONCAT1", 1),
    ("CONCAT2", 1),
    ("SearchJavaScriptAuthors6", 1);

INSERT INTO Locations (LocationName, UserID)
VALUES
    ("TestLocation", 1),
    ("OtherLocation", 2),
    ("DeleteLocation", 4),
    ("SearchFlutterLocation4", 1),
    ("S_P_Locaiton5", 1),
    ("S_JS_Locaiton6", 1),
    ("S_GL_Locaiton7", 1),
    ("S_FL_Location8", 1),
    ("S_NV_Location9", 1);

INSERT INTO Books (Title, SeriesID, LocationID, PublisherID, PublicationDate, ISBN13, ISBN10, UserID)
VALUES
    ("TestBook1", 1, 1, 1, "xxxx-xx-xx", "1234567890123", "1234567890", 1),
    ("OtherBook", 2, 2, 2, "xxxx-xx-xx", "1111111111111", "1111111111", 2),
    ("DeleteBook", 3, 3, 3, "xxxx-xx-xx", "1111111111111", "1111111111", 4),
    ("CONCATAuthor", 11, 1, 1, "xxxx-xx-xx", "1234567890123", "1234567890", 1),
    ("S_P_Book5", 6, 5, 4, NULL, NULL, NULL, 1),
    ("S_GL_Book6", 5, 7, NULL, NULL, NULL, NULL, 1),
    ("S_JS_Book7", 7, 6, NULL, NULL, NULL, NULL, 1),
    ("S_FL_Book8", 9, 8, NULL, NULL, NULL, NULL, 1),
    ("SearchNeoVim9", 10, 9, NULL, NULL, NULL, NULL, 1),
    ("TestBook10", 1, 1, 1, "xxxx-xx-xx", "1234567890123", "1234567890", 1);


INSERT INTO BookAuthors (BookID, AuthorID)
VALUES
    (1, 1), /* test */
    (2, 2), /* other */
    (3, 3), /* delete */
    (4, 4), /* CONCAT1 */
    (4, 5), /* CONCAT2 */
    (7, 6); /* AuthroSearch */