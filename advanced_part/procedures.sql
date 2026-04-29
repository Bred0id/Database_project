-- 1. Функция расчета стоимости бронирования.
CREATE OR REPLACE FUNCTION music_studio.calculate_booking_cost(
    p_studio_id INT,
    p_start_time TIMESTAMP,
    p_end_time TIMESTAMP
)
RETURNS NUMERIC(12, 2)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_hourly_cost NUMERIC(10, 2);
    v_hours NUMERIC;
BEGIN
    IF p_end_time <= p_start_time THEN
        RAISE EXCEPTION 'End time must be greater than start time';
    END IF;

    SELECT hourly_cost
    INTO v_hourly_cost
    FROM music_studio.studios
    WHERE studio_id = p_studio_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Studio with id % does not exist', p_studio_id;
    END IF;

    v_hours := EXTRACT(EPOCH FROM (p_end_time - p_start_time)) / 3600;

    RETURN ROUND(v_hourly_cost * v_hours, 2);
END;
$$;


-- 2. Функция проверки доступности студии.
CREATE OR REPLACE FUNCTION music_studio.is_studio_available(
    p_studio_id INT,
    p_start_time TIMESTAMP,
    p_end_time TIMESTAMP,
    p_exclude_booking_id INT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_studio_status VARCHAR(20);
BEGIN
    IF p_end_time <= p_start_time THEN
        RAISE EXCEPTION 'End time must be greater than start time';
    END IF;

    SELECT status
    INTO v_studio_status
    FROM music_studio.studios
    WHERE studio_id = p_studio_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Studio with id % does not exist', p_studio_id;
    END IF;

    IF v_studio_status <> 'available' THEN
        RETURN FALSE;
    END IF;

    RETURN NOT EXISTS (
        SELECT 1
        FROM music_studio.bookings b
        WHERE b.studio_id = p_studio_id
          AND b.status IN ('created', 'confirmed')
          AND (p_exclude_booking_id IS NULL OR b.booking_id <> p_exclude_booking_id)
          AND b.start_time < p_end_time
          AND b.end_time > p_start_time
    );
END;
$$;


-- 3. Процедура создания бронирования.
CREATE OR REPLACE PROCEDURE music_studio.create_booking(
    p_user_id INT,
    p_studio_id INT,
    p_start_time TIMESTAMP,
    p_end_time TIMESTAMP,
    p_purpose VARCHAR(100)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_status VARCHAR(20);
    v_total_cost NUMERIC(12, 2);
BEGIN
    SELECT status
    INTO v_user_status
    FROM music_studio.users
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User with id % does not exist', p_user_id;
    END IF;

    IF v_user_status <> 'active' THEN
        RAISE EXCEPTION 'User with id % is not active', p_user_id;
    END IF;

    IF NOT music_studio.is_studio_available(
        p_studio_id,
        p_start_time,
        p_end_time
    ) THEN
        RAISE EXCEPTION 'Studio with id % is not available for this time interval', p_studio_id;
    END IF;

    v_total_cost := music_studio.calculate_booking_cost(
        p_studio_id,
        p_start_time,
        p_end_time
    );

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
        p_user_id,
        p_studio_id,
        p_start_time,
        p_end_time,
        p_purpose,
        'created',
        v_total_cost
    );
END;
$$;