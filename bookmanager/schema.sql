PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS outer_name;
DROP TABLE IF EXISTS publisher;
DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS have_site;

CREATE TABLE book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outer_id INTEGER NOT NULL,
    publisher_id INTEGER NOT NULL,
    series_id INTEGER NOT NULL,
    site_id INTEGER NOT NULL,
    volume INTEGER NOT NULL,
    publication_date TEXT NOT NULL,
    isbn INTEGER,
    title TEXT NOT NULL,
    FOREIGN KEY (outer_id) REFERENCES outer_name(id),
    FOREIGN KEY (publisher_id) REFERENCES publisher(id),
    FOREIGN KEY (series_id) REFERENCES series(id),
    FOREIGN KEY (site_id) REFERENCES have_site(id)
);

CREATE TABLE outer_name (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outer_name TEXT NOT NULL
);

CREATE TABLE publisher (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    publisher_name TEXT NOT NULL
);

CREATE TABLE series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name TEXT NOT NULL
)

CREATE TABLE have_site (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_name TEXT NOT NULL
)