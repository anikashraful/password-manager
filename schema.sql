DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS passwords;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    salt TEXT NOT NULL
);

CREATE TABLE passwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    site_name TEXT NOT NULL,
    site_url TEXT,
    username TEXT NOT NULL,
    encrypted_password TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);