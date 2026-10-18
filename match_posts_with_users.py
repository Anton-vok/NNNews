import sqlite3
from contextlib import closing

# Пустой фильтр у поста = подходит всем.
# Между фильтрами И, внутри фильтра ИЛИ.
INSERT_DELIVERIES = """
INSERT OR IGNORE INTO deliveries (post_id, user_id, sent)
SELECT :post_id, u.id, 0
FROM users u
WHERE (
        NOT EXISTS (SELECT 1 FROM post_campuses WHERE post_id = :post_id)
     OR u.campus_id IN (SELECT campus_id FROM post_campuses WHERE post_id = :post_id)
)
AND (
        NOT EXISTS (SELECT 1 FROM post_tags WHERE post_id = :post_id)
     OR NOT EXISTS (SELECT 1 FROM user_tags WHERE user_id = u.id)
     OR EXISTS (
            SELECT 1 FROM user_tags ut
            WHERE ut.user_id = u.id
              AND ut.tag_id IN (SELECT tag_id FROM post_tags WHERE post_id = :post_id)
     )
)
"""

def match_posts_with_users(db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        post_ids = [r[0] for r in conn.execute(
            "SELECT id FROM posts WHERE moderation_status = 'approved' AND is_processed = 0"
        )]
        for post_id in post_ids:
            added = conn.execute(INSERT_DELIVERIES, {"post_id": post_id}).rowcount
            conn.execute("UPDATE posts SET is_processed = 1 WHERE id = ?", (post_id,))
            print(f"пост {post_id}: в рассылку добавлено {added}")
        conn.commit()
