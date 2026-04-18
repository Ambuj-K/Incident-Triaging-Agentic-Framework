import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="incident_triage",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    conn.commit()
    conn.close()
    print(f"Success: {version[0]}")
    print("pgvector ready")
except Exception as e:
    print(f"Failed: {e}")