import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import DATABASE_URL


@contextmanager
def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                code BIGINT PRIMARY KEY,
                title TEXT NOT NULL,
                year TEXT,
                genre TEXT,
                duration TEXT,
                language TEXT,
                quality TEXT,
                file_id TEXT NOT NULL,
                views INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                joined_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                user_id BIGINT,
                code BIGINT,
                stars INTEGER,
                PRIMARY KEY (user_id, code)
            )
        """)


def add_user(user_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))


def get_all_user_ids():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users")
        return [r["user_id"] for r in cur.fetchall()]


def get_user_count():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        return cur.fetchone()["cnt"]


def add_movie(code, title, year, genre, duration, language, quality, file_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO movies (code, title, year, genre, duration, language, quality, file_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (code) DO UPDATE SET
                 title=EXCLUDED.title, year=EXCLUDED.year, genre=EXCLUDED.genre,
                 duration=EXCLUDED.duration, language=EXCLUDED.language,
                 quality=EXCLUDED.quality, file_id=EXCLUDED.file_id""",
            (code, title, year, genre, duration, language, quality, file_id),
        )


def delete_movie(code):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM movies WHERE code=%s", (code,))


def get_movie(code):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM movies WHERE code=%s", (code,))
        return cur.fetchone()


def code_exists(code):
    return get_movie(code) is not None


def increment_views(code):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE movies SET views = views + 1 WHERE code=%s", (code,))


def get_movie_count():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM movies")
        return cur.fetchone()["cnt"]


def get_genres():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT genre FROM movies WHERE genre IS NOT NULL ORDER BY genre")
        return [r["genre"] for r in cur.fetchall()]


def get_movies_by_genre(genre, offset=0, limit=10):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT code, title FROM movies WHERE genre=%s ORDER BY title LIMIT %s OFFSET %s",
            (genre, limit, offset),
        )
        return cur.fetchall()


def count_movies_by_genre(genre):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM movies WHERE genre=%s", (genre,))
        return cur.fetchone()["cnt"]


def search_movies(query, offset=0, limit=10):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT code, title FROM movies WHERE title ILIKE %s ORDER BY title LIMIT %s OFFSET %s",
            (f"%{query}%", limit, offset),
        )
        return cur.fetchall()


def count_search_movies(query):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM movies WHERE title ILIKE %s", (f"%{query}%",))
        return cur.fetchone()["cnt"]


def get_top_movies(limit=10):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT code, title FROM movies ORDER BY views DESC LIMIT %s", (limit,))
        return cur.fetchall()


def add_rating(user_id, code, stars):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ratings (user_id, code, stars) VALUES (%s,%s,%s)
               ON CONFLICT (user_id, code) DO UPDATE SET stars=EXCLUDED.stars""",
            (user_id, code, stars),
        )


def get_rating_info(code):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT AVG(stars) AS avg, COUNT(*) AS cnt FROM ratings WHERE code=%s", (code,))
        row = cur.fetchone()
        avg = round(float(row["avg"]), 1) if row["avg"] else 0
        return avg, row["cnt"]
