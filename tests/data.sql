INSERT INTO user (username, password)
VALUES
    /* passwrod: test_password */
    ("test", 'scrypt:32768:8:1$8uZscSUuCdRPqJEs$b92a17217171f9d72d9b2e9899e2b2c88d090f91e8ae7f02d937961c80090da8a24c889f8018f7c6c498dc6ba9cf526c934cb57a2974a2c26b67ead223e18186'),
    /* password: other_password */
    ("other", 'scrypt:32768:8:1$I4mIy0QdfpRfB62m$b8491a038c9984da03e51d7e109c1300ad004afc1cfd3eea0f810cefa9560633dc3b1a9025285cb628ddf621b2ee299f852a4c5b86daf21d26491e638dce551d')

INSERT INTO Publishers (PublisherName, UserID)
VALUES
    ("TestPublisher", 1);

INSERT INTO Series (SeriesName, PublisherID, UserID)
VALUES
    ("TestSeries", 1, 1),
    ("HaveTwoAuthorSeries", 1, 1),
    ("NonPublisherSeries", NULL, 1),
    ("NonAuhtorsSeries", 1, 1);

INSERT INTO Authors (AuthorName, UserID)
VALUES
    ("TestAuthor1", 1)
    ("TestAuthor2", 1);

INSERT INTO Locations (LocationName, UserID)
VALUES
    ("TestLocation", 1);

INSERT INTO Books (Title, SeriesID, LocationID, PublicationDate, ISBN13, ISBN10, UserID)
VALUES
    ("TestBook1", 1, 1, "xxxx-xx-xx", "1234567890123", "1234567890", 1),
    ("TestBook2", 2, 1, "xxxx-xx-xx", "1234567890123", "1234567890", 1),
    ("Book_NullDate", 1, 1, NULL, "1234567890123", "1234567890", 1),
    ("Book_NullISBN13", 1, 1, "2023-01-01", NULL, "1234567890", 1),                -- ISBN13のみNULL
    ("Book_NullISBN10", 1, 1, "2023-01-01", "1234567890123", NULL, 1),             -- ISBN10のみNULL
    ("Book_NullDate_ISBN13", 1, 1, NULL, NULL, "1234567890", 1),                   -- PublicationDateとISBN13がNULL
    ("Book_NullDate_ISBN10", 1, 1, NULL, "1234567890123", NULL, 1),                -- PublicationDateとISBN10がNULL
    ("Book_NullISBN13_ISBN10", 1, 1, "2023-01-01", NULL, NULL, 1),                 -- ISBN13とISBN10がNULL
    ("Book_AllNull", 1, 1, NULL, NULL, NULL, 1); 

INSERT INTO BookAuthors (SeriesID, AuthorID)
VALUES
    (1, 1),
    (2, 1),
    (2, 2),
    (3, 1);