-- Active: 1720577098991@@postgres.wolfeydev.com@5432@thermostatter
CREATE SCHEMA auth;

DROP TABLE auth.users;

CREATE TABLE auth.users (
    username VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(60) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);