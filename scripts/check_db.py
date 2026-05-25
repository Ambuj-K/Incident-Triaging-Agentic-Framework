import psycopg2
import os

try:
    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cursor.execute(
        "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    print(f"pgvector version: {result[1]}")
    print("Database ready")
except Exception as e:
    print(f"Failed: {e}")
