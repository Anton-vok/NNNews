PRAGMA foreign_keys = ON;


CREATE TABLE campuses      (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL );
CREATE TABLE faculties     (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, campus_id INTEGER REFERENCES campuses(id));
CREATE TABLE tage          (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL );
CREATE TABLE programs      (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, faculty_id INTEGER REFERENCES faculties(id), degree TEXT CHECK ( degree IN ('BAK','MAG')));
CREATE TABLE organizations (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL );

CREATE TABLE users (
    id             INTEGER PRIMARY KEY,
    tg_id          INTEGER UNIQUE NOT NULL,
    admission_year INTEGER,
    program_id     INTEGER REFERENCES programs(id),
    degree         TEXT CHECK ( degree IN ('BAK','MAG')),
    faculty_id     INTEGER REFERENCES faculties(id),
    campus_id      INTEGER REFERENCES campuses(id),
    is_processed   INTEGER
);

CREATE TABLE user_tags (
    user_id INTEGER REFERENCES users(id),
    tag_id  INTEGER REFERENCES tage(id),
    PRIMARY KEY (user_id, tag_id)
);

CREATE TABLE user_orgs (
    user_id INTEGER REFERENCES users(id),
    org_id  INTEGER REFERENCES organizations(id),
    PRIMARY KEY (user_id, org_id)
);

CREATE TABLE posts (
    id                 INTEGER PRIMARY KEY,
    title              TEXT NOT NULL,
    image              TEXT,
    description        TEXT,
    button_text        TEXT,
    button_url         TEXT,
    location           TEXT,
    starts_at          TEXT,
    organizer_id       INTEGER REFERENCES organizations(id),
    author_tg_id       INTEGER,
    created_at         TEXT DEFAULT CURRENT_TIMESTAMP,
    moderation_status  TEXT NOT NULL DEFAULT 'pending' CHECK ( moderation_status IN ('pending', 'approved', 'rejected', 'moderation')),
    reason             TEXT,
    source             INTEGER,
    publication_id     TEXT,
    is_processed       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE post_tags (
    post_id INTEGER REFERENCES posts(id),
    tag_id INTEGER REFERENCES tage(id),
    PRIMARY KEY (post_id, tag_id)
);
CREATE TABLE post_campuses (
    post_id   INTEGER REFERENCES posts(id),
    campus_id INTEGER REFERENCES campuses(id),
    PRIMARY KEY (post_id, campus_id)
);
CREATE TABLE post_faculties (
    post_id    INTEGER REFERENCES posts(id),
    faculty_id INTEGER REFERENCES faculties(id),
    PRIMARY KEY (post_id, faculty_id)
);
CREATE TABLE post_programs (
    post_id    INTEGER REFERENCES posts(id),
    program_id INTEGER REFERENCES programs(id),
    PRIMARY KEY (post_id, program_id)
);
CREATE TABLE post_years (
    post_id  INTEGER REFERENCES posts(id),
    admission_year INTEGER,
    PRIMARY KEY (post_id, admission_year)
);

CREATE TABLE deliveries (
    id        INTEGER PRIMARY KEY,
    post_id   INTEGER NOT NULL REFERENCES posts(id),
    user_id   INTEGER NOT NULL REFERENCES users(id),
    sent      INTEGER NOT NULL DEFAULT 0,
    liked     INTEGER CHECK ( liked in (-1, 0, 1)),
    mail_date TEXT DEFAULT '2000-01-01 00:00:00' CHECK (datetime(mail_date) IS NOT NULL),
    UNIQUE (post_id, user_id)
);