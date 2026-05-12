-- 1. Представление активных бронирований.
CREATE OR REPLACE VIEW music_studio.v_active_bookings AS
SELECT
    b.booking_id,
    b.user_id,
    u.full_name AS user_name,
    b.studio_id,
    s.studio_name,
    b.start_time,
    b.end_time,
    ROUND(CAST(EXTRACT(EPOCH FROM (b.end_time - b.start_time)) / 3600 AS NUMERIC), 2) AS duration_hours,
    b.purpose,
    b.status,
    b.total_cost
FROM music_studio.bookings b
JOIN music_studio.users u
    ON u.user_id = b.user_id
JOIN music_studio.studios s
    ON s.studio_id = b.studio_id
WHERE b.status IN ('created', 'confirmed');


-- 2. Представление дневной загруженности студий.
CREATE OR REPLACE VIEW music_studio.v_studio_daily_load AS
SELECT
    s.studio_id,
    s.studio_name,
    CAST(b.start_time AS DATE) AS booking_date,
    COUNT(b.booking_id) AS bookings_count,
    ROUND(CAST(SUM(EXTRACT(EPOCH FROM (b.end_time - b.start_time)) / 3600) AS NUMERIC), 2) AS booked_hours,
    COALESCE(SUM(b.total_cost), 0) AS daily_revenue
FROM music_studio.studios s
JOIN music_studio.bookings b
    ON b.studio_id = s.studio_id
WHERE b.status IN ('created', 'confirmed', 'completed')
GROUP BY
    s.studio_id,
    s.studio_name,
    CAST(b.start_time AS DATE);