from __future__ import annotations

import os
import sqlite3
import hashlib
from typing import Any, Dict, List, Mapping

from flask import (Blueprint, flash, redirect, render_template,
                   request, session, url_for
)

# ────────────────────────────────────────────────────────────
# Blueprint 설정
# ────────────────────────────────────────────────────────────
# URL 프리픽스를 두지 않으면 기존 경로를 그대로 유지할 수 있다.
booking_bp: Blueprint = Blueprint("routes", __name__)

# ────────────────────────────────────────────────────────────
# DB 연결 유틸 – 함수명/경로명 의미화
# ────────────────────────────────────────────────────────────
BASE_DIR: str = os.path.dirname(__file__)
USER_DB_PATH: str = os.path.join(BASE_DIR, "member.db")
TRAIN_DB_PATH: str = os.path.join(BASE_DIR, "new_train_data.db")
RESERVE_DB_PATH: str = os.path.join(BASE_DIR, "reserve.db")

def _connect(db_path: str) -> sqlite3.Connection:
    """공통 DB 커넥터. row_factory 적용 후 반환."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# 명확한 함수명으로 교체
get_user_conn = lambda: _connect(USER_DB_PATH)
get_train_conn = lambda: _connect(TRAIN_DB_PATH)
get_reserve_conn = lambda: _connect(RESERVE_DB_PATH)

# ────────────────────────────────────────────────────────────
# 0. 로그인 관련 헬퍼 & 라우트
# ────────────────────────────────────────────────────────────

def try_login(username: str, password: str) -> bool:
    """아이디/비밀번호 조합이 존재하는지 확인."""
    with get_user_conn() as conn:
        cursor = conn.execute(
            """
            SELECT 1
              FROM users
             WHERE username = ? --사용자 입력
               AND password = ? --사용자 입력
            """,
            (username, password),
        )
        return cursor.fetchone() is not None

@booking_bp.route("/", methods=["GET", "POST"])
def login_page():
    """로그인 폼 & 제출 처리."""
    if request.method == "POST":
        username: str = request.form["username"]
        password: str = request.form["password"]

        if try_login(username, password):
            session["user_id"] = username
            return redirect(url_for("routes.dashboard_page"))

    #flash("ID/PW 오류")
    return render_template("login.html", show_header=False)

def hash_password(password: str) ->str:
    return hashlib.sha256(password.encode()).hexdigest()
@booking_bp.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # 사용자 중복 확인
        with get_user_conn() as conn:
            existing_user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            hashed_pw = hash_password(password)
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_pw)
            )

            if existing_user:
                return render_template("register.html", error="이미 존재하는 아이디입니다.")

            if not username or password:
                return render_template("register.html", error="아이디와 비밀번호를 모두 입력해주세요.")
            # 새 사용자 등록
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()

        return render_template("register.html", success="회원가입이 완료되었습니다.")

    return render_template("register.html")


# ────────────────────────────────────────────────────────────
# 1. 열차 목록 Dashboard
# ────────────────────────────────────────────────────────────
@booking_bp.route("/dashboard")
def dashboard_page():
    """전체 열차 목록을 보여준다."""
    query = """
        SELECT
            train_number      AS train_no,
            departure_station AS dep_station,
            arrival_station   AS arr_station,
            departure_time,
            arrival_time,
            total_seats
          FROM train_info
    """
    with get_train_conn() as conn:
        rows: List[Mapping[str, Any]] = conn.execute(query).fetchall()

    # 열차 유형별 노선 정보
    train_routes_data = {
        "KTX": ["서울", "천안아산", "오송", "서대전", "익산", "광주송정"],
        "무궁화": ["용산", "수원", "천안", "신례원", "홍성", "대천"],
    }

    # 열차 번호가 'KTX301'처럼 되어 있어도 'KTX'로 시작하면 종류는 'KTX'로 인식
    train_info: List[Dict[str, Any]] = []
    for row in rows:
        train_no = row["train_no"]
        if train_no.startswith("KTX"):
            prefix = "KTX"
        elif train_no.startswith("무궁화"):
            prefix = "무궁화"
        else:
            prefix = "기타"

        # 기존 정보에 prefix(열차 종류)를 추가해서 리스트에 저장
        train_info.append({
            **row,
            "prefix": prefix,
        })

    return render_template(
        "dashboard.html",
        train_info=train_info,
        train_routes=train_routes_data,
        show_header=True
    )



# ────────────────────────────────────────────────────────────
# 2. 좌석 조회 페이지
# ────────────────────────────────────────────────────────────

@booking_bp.route("/train/<train_id>/seats")
def seat_page(train_id):
    if "user_id" not in session:
        return redirect(url_for("routes.login_page"))

#지우면 Internal Server Error 발생
    if not train_id:
        flash("열차가 선택되지 않았습니다.")
        return redirect(url_for("routes.dashboard_page"))

    seat_query = """
        SELECT
            seat_id,
            reserved_by
          FROM reserve
         WHERE train_id = ?
    """
    with get_reserve_conn() as conn:
        seat_rows = conn.execute(seat_query, (train_id,)).fetchall()

    seat_status: Dict[str, Any] = {row["seat_id"]: row["reserved_by"] for row in seat_rows}
    session["train_id"] = train_id

    # Dummy pricing data - replace with actual logic from a DB if needed
    train_pricing = {
        'adult_fare': 25000,
        'disabled_discount_percent': 50,
        'child_discount_percent': 30,
        'infant_seat_fare_percent': 25, # 25% of adult fare for an infant seat
    }

    return render_template(
        "seat.html",
        train_id=train_id,
        seat_status=seat_status,
        me=session["user_id"],
        pricing=train_pricing,
        show_header=True,
    )


# ────────────────────────────────────────────────────────────
# 3. 좌석 클릭 → 예매 확인
# ────────────────────────────────────────────────────────────

@booking_bp.route("/confirm", methods=["POST"])
def confirm_page():
    seat_code: str = request.form["seat_id"]
    user_id: str | None = session.get("user_id")
    selected_train: str | None = session.get("train_id")

    if not user_id or not selected_train:
        flash("세션 정보가 없습니다.")
        return redirect(url_for("routes.dashboard_page"))

    # 중복 예약 확인
    duplicate_check_sql = """
        SELECT reserved_by
          FROM reserve
         WHERE train_id = ?
           AND seat_id  = ?
    """
    with get_reserve_conn() as conn:
        row = conn.execute(duplicate_check_sql, (selected_train, seat_code)).fetchone()

    if row and row["reserved_by"]:
        flash("이미 예약된 좌석입니다.")
        return redirect(url_for("routes.seats_page", train_id=selected_train))

    # 열차 상세 정보 조회 (음성 안내용)
    train_detail_query = """
        SELECT
            train_number      AS train_no,
            departure_station AS dep_station,
            arrival_station   AS arr_station,
            departure_time,
            arrival_time
          FROM train_info
         WHERE train_number = ?
    """
    train_details = None
    with get_train_conn() as conn:
        train_details = conn.execute(train_detail_query, (selected_train,)).fetchone()

    if not train_details:
        flash("선택된 열차 정보를 찾을 수 없습니다.")
        return redirect(url_for("routes.dashboard_page"))

    return render_template(
        "confirm.html",
        seat_id=seat_code,
        train_details=train_details,
        show_header=True
    )


# ────────────────────────────────────────────────────────────
# 4. 예매 확정
# ────────────────────────────────────────────────────────────
@booking_bp.route("/book", methods=["POST"])
def finalize_booking():
    user_id: str | None = session.get("user_id")
    selected_train: str | None = session.get("train_id")
    seat_code: str | None = request.form.get("seat_id")

    if not user_id or not selected_train or not seat_code:
        flash("예매 정보가 부족합니다.")
        return redirect(url_for("routes.dashboard_page"))

    update_sql = """
        UPDATE reserve
           SET is_reserved = 1,
               reserved_by = ?,
               reserved_at = datetime('now')
         WHERE seat_id = ?
           AND train_id = ?
    """
    try:
        conn = get_reserve_conn()
        conn.execute(update_sql, (user_id, seat_code, selected_train))
        conn.commit()
        flash(f"{seat_code} 좌석 예매가 완료되었습니다.")
    except Exception as exc:
        flash("예매 처리 중 오류가 발생했습니다.")
        # 실제 운영 시 로그로 기록
    finally:
        conn.close()

    return redirect(url_for("routes.dashboard_page"))
