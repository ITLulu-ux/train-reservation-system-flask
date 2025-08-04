import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'reserve.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# 1) 테이블 생성
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reserve (
            seat_id TEXT,
            train_id TEXT,
            is_reserved INTEGER DEFAULT 0,
            reserved_by TEXT,
            reserved_at TIMESTAMP,
            PRIMARY KEY (seat_id, train_id)
        )
    """)
    conn.commit()
    conn.close()

# 2) 좌석 데이터 채우기
def seed_seats():
    trains = {
        "KTX301": ['A', 'B', 'C', 'D', 'E'],  # 5열
        "무궁화2680": ['A', 'B', 'C', 'D']    # 4열
    }

    conn = get_db_connection()
    cur = conn.cursor()

    for train_id, cols in trains.items():
        for row in range(1, 11):
            for col in cols:
                seat_id = f"{row}{col}"
                cur.execute("""
                    INSERT OR IGNORE INTO reserve (seat_id, train_id)
                    VALUES (?, ?)
                """, (seat_id, train_id))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_seats()
    print("DB 초기화 및 좌석 등록 완료.")
