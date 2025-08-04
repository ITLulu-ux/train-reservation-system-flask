import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "new_train_data.db")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS train_info (
            train_number TEXT PRIMARY KEY,
            departure_station TEXT NOT NULL,
            arrival_station TEXT NOT NULL,
            departure_time TEXT,
            arrival_time TEXT,
            total_seats INTEGER
        );
    ''')
    conn.commit()
    conn.close()

info_data = [
    ("KTX301", "서울", "광주송정", "10:30", "12:00", 50),
    ("무궁화2680", "대천", "용산", "15:00", "17:00", 50),
]

def generate_seats_for_schedule(train_number, total_seats):
    return [
        (train_number, f"S{i:02d}", True)
        for i in range(1, total_seats + 1)
    ]

all_seats_data = []
for train_num, dep_s, arr_s, dep_t, arr_t, total_s in info_data:
    seats = generate_seats_for_schedule(train_num, total_s)
    all_seats_data.extend(seats)

def insert_dummy_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("Inserting train_routes...")
        cursor.executemany("""
            INSERT INTO train_info (train_number, departure_station, arrival_station, departure_time, arrival_time, total_seats)
            VALUES (?, ?, ?, ?, ?, ?)
        """, info_data)


        conn.commit()
        print("모든 더미 데이터 삽입 완료!")

    except sqlite3.IntegrityError as e:
        print(f"무결성 오류: {e}")
        conn.rollback()
    except Exception as e:
        print(f"기타 오류: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_tables()
    insert_dummy_data()
