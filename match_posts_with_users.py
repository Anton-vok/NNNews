import sqlite3

INSERT_DELIVERIES = """
INSERT OR IGNORE INTO deliveries (post_id, user_id, sent)
SELECT :post_id, u.id, 0
FROM users AS u
WHERE
    (
        EXISTS (
            SELECT 1 FROM post_campuses pc
            WHERE pc.post_id = :post_id AND pc.campus_id = u.campus_id
        )
    )
    AND (
        EXISTS (
            SELECT 1 FROM post_faculties pf
            WHERE pf.post_id = :post_id AND pf.faculty_id = u.faculty_id
        )
    )
    AND (
        EXISTS (
            SELECT 1 FROM post_programs pp
            WHERE pp.post_id = :post_id AND pp.program_id = u.program_id
        )
    )
    AND (
        EXISTS (
            SELECT 1 FROM post_years py
            WHERE py.post_id = :post_id AND py.admission_year = u.admission_year
        )
    )
    AND (
        EXISTS (
            SELECT 1 FROM post_tags pt
            JOIN user_tags ut ON ut.tag_id = pt.tag_id
            WHERE pt.post_id = :post_id AND ut.user_id = u.id
        )
    )
"""

def match_posts_with_users(db_path):
    print("hi")
    connection = sqlite3.connect(str(db_path))
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("BEGIN IMMEDIATE")

    post_ids = [row[0] for row in connection.execute(
        """SELECT id FROM posts
           WHERE moderation_status = 'approved' AND is_processed = 0
           ORDER BY id"""
    )]

    for post_id in post_ids:
        print("1")
        connection.execute(INSERT_DELIVERIES, {"post_id": post_id})
        connection.execute(
            "UPDATE posts SET is_processed = 1 WHERE id = ?", (post_id,)
        )

    connection.commit()
    connection.close()