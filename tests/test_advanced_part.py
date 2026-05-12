import os
from decimal import Decimal

import psycopg2
import pytest


def get_connection():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "postgres"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
    )


@pytest.fixture
def connection():
    conn = get_connection()
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def cursor(connection):
    with connection.cursor() as cur:
        yield cur


def get_active_user_id(cur):
    cur.execute(
        """
        SELECT user_id
        FROM music_studio.users
        WHERE status = 'active'
        ORDER BY user_id
        LIMIT 1;
        """
    )
    row = cur.fetchone()
    assert row is not None, "Нет активного пользователя для тестов"
    return row[0]


def get_inactive_user_id(cur):
    cur.execute(
        """
        SELECT user_id
        FROM music_studio.users
        WHERE status <> 'active'
        ORDER BY user_id
        LIMIT 1;
        """
    )
    row = cur.fetchone()
    assert row is not None, "Нет неактивного пользователя для тестов"
    return row[0]


def get_available_studio_id(cur):
    cur.execute(
        """
        SELECT studio_id
        FROM music_studio.studios
        WHERE status = 'available'
        ORDER BY studio_id
        LIMIT 1;
        """
    )
    row = cur.fetchone()
    assert row is not None, "Нет доступной студии для тестов"
    return row[0]


def get_unavailable_studio_id(cur):
    cur.execute(
        """
        SELECT studio_id
        FROM music_studio.studios
        WHERE status <> 'available'
        ORDER BY studio_id
        LIMIT 1;
        """
    )
    row = cur.fetchone()
    assert row is not None, "Нет недоступной студии для тестов"
    return row[0]


def create_test_booking(cur, user_id, studio_id, start_time, end_time, purpose):
    cur.execute(
        """
        SELECT music_studio.create_booking(
            %s,
            %s,
            %s,
            %s,
            %s
        );
        """,
        (user_id, studio_id, start_time, end_time, purpose),
    )
    return cur.fetchone()[0]


# INDEXES

def test_my_indexes_exist_with_expected_definitions(cursor):
    cursor.execute(
        """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'music_studio'
          AND indexname IN (
              'idx_bookings_studio_time',
              'idx_bookings_user_time',
              'idx_equipment_problem_status'
          );
        """
    )

    indexes = dict(cursor.fetchall())

    assert "idx_bookings_studio_time" in indexes
    assert "ON music_studio.bookings" in indexes["idx_bookings_studio_time"]
    assert "(studio_id, start_time, end_time)" in indexes["idx_bookings_studio_time"]

    assert "idx_bookings_user_time" in indexes
    assert "ON music_studio.bookings" in indexes["idx_bookings_user_time"]
    assert "(user_id, start_time)" in indexes["idx_bookings_user_time"]

    assert "idx_equipment_problem_status" in indexes
    assert "ON music_studio.equipment" in indexes["idx_equipment_problem_status"]
    assert "(status)" in indexes["idx_equipment_problem_status"]
    assert "WHERE" in indexes["idx_equipment_problem_status"]
    assert "maintenance" in indexes["idx_equipment_problem_status"]
    assert "broken" in indexes["idx_equipment_problem_status"]


@pytest.mark.parametrize(
    "query, expected_index",
    [
        (
            """
            EXPLAIN
            SELECT *
            FROM music_studio.bookings
            WHERE studio_id = 1
              AND start_time < TIMESTAMP '2035-01-01 12:00:00'
              AND end_time > TIMESTAMP '2035-01-01 10:00:00';
            """,
            "idx_bookings_studio_time",
        ),
        (
            """
            EXPLAIN
            SELECT *
            FROM music_studio.bookings
            WHERE user_id = 1
            ORDER BY start_time;
            """,
            "idx_bookings_user_time",
        ),
        (
            """
            EXPLAIN
            SELECT *
            FROM music_studio.equipment
            WHERE status IN ('maintenance', 'broken');
            """,
            "idx_equipment_problem_status",
        ),
    ],
)
def test_my_indexes_can_be_used_by_matching_queries(cursor, query, expected_index):
    cursor.execute("SET enable_seqscan = off;")
    cursor.execute(query)

    plan = "\n".join(row[0] for row in cursor.fetchall())

    assert expected_index in plan


# VIEWS

def test_active_bookings_view_has_expected_columns(cursor):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'music_studio'
          AND table_name = 'v_active_bookings'
        ORDER BY ordinal_position;
        """
    )

    columns = [row[0] for row in cursor.fetchall()]

    assert columns == [
        "booking_id",
        "user_id",
        "user_name",
        "studio_id",
        "studio_name",
        "start_time",
        "end_time",
        "duration_hours",
        "purpose",
        "status",
        "total_cost",
    ]


def test_active_bookings_view_contains_only_active_statuses(cursor):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM music_studio.v_active_bookings
        WHERE status NOT IN ('created', 'confirmed');
        """
    )

    assert cursor.fetchone()[0] == 0


def test_active_bookings_view_duration_is_calculated_correctly(cursor):
    cursor.execute(
        """
        SELECT start_time, end_time, duration_hours
        FROM music_studio.v_active_bookings
        LIMIT 1;
        """
    )

    row = cursor.fetchone()

    if row is None:
        pytest.skip("В v_active_bookings нет строк для проверки")

    start_time, end_time, duration_hours = row
    expected_hours = Decimal(
        str(round((end_time - start_time).total_seconds() / 3600, 2))
    )

    assert Decimal(duration_hours) == expected_hours


def test_studio_daily_load_view_has_expected_columns(cursor):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'music_studio'
          AND table_name = 'v_studio_daily_load'
        ORDER BY ordinal_position;
        """
    )

    columns = [row[0] for row in cursor.fetchall()]

    assert columns == [
        "studio_id",
        "studio_name",
        "booking_date",
        "bookings_count",
        "booked_hours",
        "daily_revenue",
    ]


def test_studio_daily_load_view_matches_base_tables(cursor):
    cursor.execute(
        """
        SELECT studio_id, booking_date, bookings_count, booked_hours, daily_revenue
        FROM music_studio.v_studio_daily_load
        ORDER BY studio_id, booking_date
        LIMIT 1;
        """
    )

    row = cursor.fetchone()

    if row is None:
        pytest.skip("В v_studio_daily_load нет строк для проверки")

    studio_id, booking_date, bookings_count, booked_hours, daily_revenue = row

    cursor.execute(
        """
        SELECT
            COUNT(b.booking_id),
            ROUND(CAST(SUM(EXTRACT(EPOCH FROM (b.end_time - b.start_time)) / 3600) AS NUMERIC), 2),
            COALESCE(SUM(b.total_cost), 0)
        FROM music_studio.bookings b
        WHERE b.studio_id = %s
          AND CAST(b.start_time AS DATE) = %s
          AND b.status IN ('created', 'confirmed', 'completed');
        """,
        (studio_id, booking_date),
    )

    expected_count, expected_hours, expected_revenue = cursor.fetchone()

    assert bookings_count == expected_count
    assert booked_hours == expected_hours
    assert daily_revenue == expected_revenue


# FUNCTIONS

@pytest.mark.parametrize(
    "start_time, end_time, expected_hours",
    [
        (
            "2035-02-01 10:00:00",
            "2035-02-01 11:00:00",
            Decimal("1.0"),
        ),
        (
            "2035-02-01 10:00:00",
            "2035-02-01 12:30:00",
            Decimal("2.5"),
        ),
        (
            "2035-02-01 10:15:00",
            "2035-02-01 11:45:00",
            Decimal("1.5"),
        ),
    ],
)
def test_calculate_booking_cost_uses_studio_hourly_cost(
    cursor,
    start_time,
    end_time,
    expected_hours,
):
    studio_id = get_available_studio_id(cursor)

    cursor.execute(
        """
        SELECT hourly_cost
        FROM music_studio.studios
        WHERE studio_id = %s;
        """,
        (studio_id,),
    )
    hourly_cost = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT music_studio.calculate_booking_cost(
            %s,
            %s,
            %s
        );
        """,
        (studio_id, start_time, end_time),
    )

    result = cursor.fetchone()[0]

    assert result == round(hourly_cost * expected_hours, 2)


@pytest.mark.parametrize(
    "start_time, end_time",
    [
        (
            "2035-02-02 10:00:00",
            "2035-02-02 10:00:00",
        ),
        (
            "2035-02-02 12:00:00",
            "2035-02-02 10:00:00",
        ),
    ],
)
def test_calculate_booking_cost_rejects_invalid_time_interval(
    cursor,
    start_time,
    end_time,
):
    studio_id = get_available_studio_id(cursor)

    with pytest.raises(psycopg2.Error):
        cursor.execute(
            """
            SELECT music_studio.calculate_booking_cost(
                %s,
                %s,
                %s
            );
            """,
            (studio_id, start_time, end_time),
        )


def test_calculate_booking_cost_rejects_unknown_studio(cursor):
    with pytest.raises(psycopg2.Error):
        cursor.execute(
            """
            SELECT music_studio.calculate_booking_cost(
                -1,
                TIMESTAMP '2035-02-03 10:00:00',
                TIMESTAMP '2035-02-03 12:00:00'
            );
            """
        )


def test_is_studio_available_returns_true_for_empty_future_slot(cursor):
    studio_id = get_available_studio_id(cursor)

    cursor.execute(
        """
        SELECT music_studio.is_studio_available(
            %s,
            TIMESTAMP '2035-02-04 10:00:00',
            TIMESTAMP '2035-02-04 12:00:00'
        );
        """,
        (studio_id,),
    )

    assert cursor.fetchone()[0] is True


@pytest.mark.parametrize(
    "check_start, check_end, expected_available",
    [
        (
            "2035-02-05 09:00:00",
            "2035-02-05 10:00:00",
            True,
        ),
        (
            "2035-02-05 12:00:00",
            "2035-02-05 13:00:00",
            True,
        ),
        (
            "2035-02-05 09:00:00",
            "2035-02-05 11:00:00",
            False,
        ),
        (
            "2035-02-05 11:00:00",
            "2035-02-05 13:00:00",
            False,
        ),
        (
            "2035-02-05 10:30:00",
            "2035-02-05 11:30:00",
            False,
        ),
        (
            "2035-02-05 09:00:00",
            "2035-02-05 13:00:00",
            False,
        ),
    ],
)
def test_is_studio_available_handles_interval_boundaries(
    cursor,
    check_start,
    check_end,
    expected_available,
):
    user_id = get_active_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    create_test_booking(
        cursor,
        user_id,
        studio_id,
        "2035-02-05 10:00:00",
        "2035-02-05 12:00:00",
        "Boundary test",
    )

    cursor.execute(
        """
        SELECT music_studio.is_studio_available(
            %s,
            %s,
            %s
        );
        """,
        (studio_id, check_start, check_end),
    )

    assert cursor.fetchone()[0] is expected_available


def test_is_studio_available_returns_false_for_unavailable_studio(cursor):
    studio_id = get_unavailable_studio_id(cursor)

    cursor.execute(
        """
        SELECT music_studio.is_studio_available(
            %s,
            TIMESTAMP '2035-02-06 10:00:00',
            TIMESTAMP '2035-02-06 12:00:00'
        );
        """,
        (studio_id,),
    )

    assert cursor.fetchone()[0] is False


def test_create_booking_function_returns_new_booking_id(cursor):
    user_id = get_active_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    booking_id = create_test_booking(
        cursor,
        user_id,
        studio_id,
        "2035-02-07 10:00:00",
        "2035-02-07 12:00:00",
        "Create booking test",
    )

    assert isinstance(booking_id, int)

    cursor.execute(
        """
        SELECT user_id, studio_id, status, purpose
        FROM music_studio.bookings
        WHERE booking_id = %s;
        """,
        (booking_id,),
    )

    assert cursor.fetchone() == (
        user_id,
        studio_id,
        "created",
        "Create booking test",
    )


def test_create_booking_function_rejects_inactive_user(cursor):
    inactive_user_id = get_inactive_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    with pytest.raises(psycopg2.Error):
        create_test_booking(
            cursor,
            inactive_user_id,
            studio_id,
            "2035-02-08 10:00:00",
            "2035-02-08 12:00:00",
            "Inactive user test",
        )


def test_create_booking_function_rejects_unavailable_studio(cursor):
    user_id = get_active_user_id(cursor)
    studio_id = get_unavailable_studio_id(cursor)

    with pytest.raises(psycopg2.Error):
        create_test_booking(
            cursor,
            user_id,
            studio_id,
            "2035-02-09 10:00:00",
            "2035-02-09 12:00:00",
            "Unavailable studio test",
        )


def test_create_booking_function_rejects_invalid_purpose_by_table_check(cursor):
    user_id = get_active_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    with pytest.raises(psycopg2.Error):
        create_test_booking(
            cursor,
            user_id,
            studio_id,
            "2035-02-10 10:00:00",
            "2035-02-10 12:00:00",
            "test",
        )


# TRIGGERS

def test_booking_trigger_sets_total_cost_on_direct_insert(cursor):
    user_id = get_active_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    cursor.execute(
        """
        INSERT INTO music_studio.bookings (
            user_id,
            studio_id,
            start_time,
            end_time,
            purpose,
            status,
            total_cost
        )
        VALUES (
            %s,
            %s,
            TIMESTAMP '2035-03-01 10:00:00',
            TIMESTAMP '2035-03-01 12:00:00',
            'Direct trigger test',
            'created',
            0
        )
        RETURNING booking_id, total_cost;
        """,
        (user_id, studio_id),
    )

    booking_id, total_cost = cursor.fetchone()

    assert isinstance(booking_id, int)
    assert total_cost > 0


def test_booking_trigger_rejects_direct_insert_for_inactive_user(cursor):
    user_id = get_inactive_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    with pytest.raises(psycopg2.Error):
        cursor.execute(
            """
            INSERT INTO music_studio.bookings (
                user_id,
                studio_id,
                start_time,
                end_time,
                purpose,
                status,
                total_cost
            )
            VALUES (
                %s,
                %s,
                TIMESTAMP '2035-03-02 10:00:00',
                TIMESTAMP '2035-03-02 12:00:00',
                'Direct trigger test',
                'created',
                0
            );
            """,
            (user_id, studio_id),
        )


def test_booking_trigger_rejects_direct_insert_for_unavailable_studio(cursor):
    user_id = get_active_user_id(cursor)
    studio_id = get_unavailable_studio_id(cursor)

    with pytest.raises(psycopg2.Error):
        cursor.execute(
            """
            INSERT INTO music_studio.bookings (
                user_id,
                studio_id,
                start_time,
                end_time,
                purpose,
                status,
                total_cost
            )
            VALUES (
                %s,
                %s,
                TIMESTAMP '2035-03-03 10:00:00',
                TIMESTAMP '2035-03-03 12:00:00',
                'Direct trigger test',
                'created',
                0
            );
            """,
            (user_id, studio_id),
        )


def test_booking_trigger_rejects_direct_overlapping_insert(cursor):
    user_id = get_active_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    cursor.execute(
        """
        INSERT INTO music_studio.bookings (
            user_id,
            studio_id,
            start_time,
            end_time,
            purpose,
            status,
            total_cost
        )
        VALUES (
            %s,
            %s,
            TIMESTAMP '2035-03-04 10:00:00',
            TIMESTAMP '2035-03-04 12:00:00',
            'Direct trigger test',
            'created',
            0
        );
        """,
        (user_id, studio_id),
    )

    with pytest.raises(psycopg2.Error):
        cursor.execute(
            """
            INSERT INTO music_studio.bookings (
                user_id,
                studio_id,
                start_time,
                end_time,
                purpose,
                status,
                total_cost
            )
            VALUES (
                %s,
                %s,
                TIMESTAMP '2035-03-04 11:00:00',
                TIMESTAMP '2035-03-04 13:00:00',
                'Direct overlap test',
                'created',
                0
            );
            """,
            (user_id, studio_id),
        )


@pytest.mark.parametrize(
    "payment_status, expected_booking_status",
    [
        ("paid", "confirmed"),
        ("refunded", "cancelled"),
    ],
)
def test_payment_trigger_changes_booking_status_by_payment_status(
    cursor,
    payment_status,
    expected_booking_status,
):
    user_id = get_active_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    booking_id = create_test_booking(
        cursor,
        user_id,
        studio_id,
        f"2035-03-05 10:00:00",
        f"2035-03-05 12:00:00",
        "Payment trigger test",
    )

    cursor.execute(
        """
        SELECT total_cost
        FROM music_studio.bookings
        WHERE booking_id = %s;
        """,
        (booking_id,),
    )
    total_cost = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO music_studio.payments (
            booking_id,
            amount,
            payment_method,
            status
        )
        VALUES (%s, %s, 'card', %s);
        """,
        (booking_id, total_cost, payment_status),
    )

    cursor.execute(
        """
        SELECT status
        FROM music_studio.bookings
        WHERE booking_id = %s;
        """,
        (booking_id,),
    )

    assert cursor.fetchone()[0] == expected_booking_status


def test_payment_trigger_rejects_wrong_payment_amount(cursor):
    user_id = get_active_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    booking_id = create_test_booking(
        cursor,
        user_id,
        studio_id,
        "2035-03-06 10:00:00",
        "2035-03-06 12:00:00",
        "Payment trigger test",
    )

    with pytest.raises(psycopg2.Error):
        cursor.execute(
            """
            INSERT INTO music_studio.payments (
                booking_id,
                amount,
                payment_method,
                status
            )
            VALUES (%s, 1, 'card', 'paid');
            """,
            (booking_id,),
        )


def test_payment_trigger_rejects_non_refund_payment_for_cancelled_booking(cursor):
    user_id = get_active_user_id(cursor)
    studio_id = get_available_studio_id(cursor)

    booking_id = create_test_booking(
        cursor,
        user_id,
        studio_id,
        "2035-03-07 10:00:00",
        "2035-03-07 12:00:00",
        "Cancelled payment test",
    )

    cursor.execute(
        """
        UPDATE music_studio.bookings
        SET status = 'cancelled'
        WHERE booking_id = %s;
        """,
        (booking_id,),
    )

    cursor.execute(
        """
        SELECT total_cost
        FROM music_studio.bookings
        WHERE booking_id = %s;
        """,
        (booking_id,),
    )
    total_cost = cursor.fetchone()[0]

    with pytest.raises(psycopg2.Error):
        cursor.execute(
            """
            INSERT INTO music_studio.payments (
                booking_id,
                amount,
                payment_method,
                status
            )
            VALUES (%s, %s, 'card', 'paid');
            """,
            (booking_id, total_cost),
        )