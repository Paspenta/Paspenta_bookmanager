PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Publishers;
DROP TABLE IF EXISTS Series;
DROP TABLE IF EXISTS Authors;
DROP TABLE IF EXISTS Locations;
DROP TABLE IF EXISTS Books;
DROP TABLE IF EXISTS BookAuthors;

CREATE TABLE Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserName TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL
);

CREATE TABLE Publishers (
    PublisherID INTEGER PRIMARY KEY AUTOINCREMENT,
    PublisherName TEXT NOT NULL,
    UserID INTEGER NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

CREATE TABLE Series (
    SeriesID INTEGER PRIMARY KEY AUTOINCREMENT,
    SeriesName TEXT NOT NULL,
    UserID INTEGER NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

CREATE TABLE Authors (
    AuthorID INTEGER PRIMARY KEY AUTOINCREMENT,
    AuthorName TEXT NOT NULL,
    UserID INTEGER NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

CREATE TABLE Locations (
    LocationID INTEGER PRIMARY KEY AUTOINCREMENT,
    LocationName TEXT NOT NULL,
    UserID INTEGER NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

CREATE TABLE Books (
    BookID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL,
    LocationID INTEGER NOT NULL,
    PublisherID INTEGER,
    SeriesID INTEGER,
    Title TEXT NOT NULL,
    PublicationDate TEXT,
    ISBN13 TEXT,
    ISBN10 TEXT,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (LocationID) REFERENCES Locations(LocationID),
    FOREIGN KEY (PublisherID) REFERENCES Publishers(PublisherID),
    FOREIGN KEY (SeriesID) REFERENCES Series(SeriesID)
);

CREATE TABLE BookAuthors (
    BookID INTEGER NOT NULL,
    AuthorID INTEGER NOT NULL,
    PRIMARY KEY (BookID, AuthorID),
    FOREIGN KEY (BookID) REFERENCES Books(BookID),
    FOREIGN KEY (AuthorID) REFERENCES Authors(AuthorID)
);