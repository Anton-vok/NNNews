import sqlite3
from contextlib import closing

INSERT_DELIVERIES_FOR_USER = """
INSERT OR IGNORE INTO deliveries (post_id, user_id, sent)
SELECT p.id, :user_id, 0
FROM posts p
WHERE 
  p.moderation_status = 'approved'
  AND NOT EXISTS (
        SELECT 1 FROM deliveries d WHERE d.post_id = p.id AND d.user_id = :user_id
  )
  AND (
        NOT EXISTS (SELECT 1 FROM post_campuses WHERE post_id = p.id)
     OR EXISTS (
            SELECT 1 FROM post_campuses pc WHERE pc.post_id = p.id AND pc.campus_id = :campus_id
        )
  )
  AND (
        NOT EXISTS (SELECT 1 FROM post_tags WHERE post_id = p.id)
     OR NOT EXISTS (SELECT 1 FROM user_tags WHERE user_id = :user_id)
     OR EXISTS (
            SELECT 1 FROM post_tags pt WHERE pt.post_id = p.id
              AND pt.tag_id IN (SELECT tag_id FROM user_tags WHERE user_id = :user_id)
        )
  )
ORDER BY p.created_at DESC, p.id DESC
"""

def match_users_with_posts(db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        users = conn.execute(
            "SELECT id, campus_id, is_processed FROM users WHERE is_processed IN (0, -1)"
        ).fetchall()

        for user_id, campus_id, is_processed in users:
            query = INSERT_DELIVERIES_FOR_USER
            if is_processed == -1:
                query += " LIMIT 5"
            added = conn.execute(query, {"user_id": user_id, "campus_id": campus_id}).rowcount
            conn.execute("UPDATE users SET is_processed = 1 WHERE id = ?",(user_id,),)
            print(f"пользователь {user_id}: в рассылку добавлено {added} постов")

        conn.commit()