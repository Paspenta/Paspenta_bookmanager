PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS outer_name;
DROP TABLE IF EXISTS publisher;
DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS have_site;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    namename TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE outer_name (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outer_name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE publisher (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    publisher_name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE have_site (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    outer_id INTEGER NOT NULL,
    publisher_id INTEGER NOT NULL,
    series_id INTEGER,
    site_id INTEGER NOT NULL,
    volume INTEGER,
    publication_date TEXT,
    isbn INTEGER,
    title TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (outer_id) REFERENCES outer_name(id),
    FOREIGN KEY (publisher_id) REFERENCES publisher(id),
    FOREIGN KEY (series_id) REFERENCES series(id),
    FOREIGN KEY (site_id) REFERENCES have_site(id)
);