-- 1. Получение расписания студии по часам на выбранный день с определением занятых и свободных интервалов
WITH RECURSIVE params AS (
    SELECT
        7 AS target_studio_id,
        DATE '2024-07-23' AS target_day
),
time_slots AS (
    SELECT
        p.target_studio_id AS studio_id,
        CAST(p.target_day AS TIMESTAMP) AS slot_start,
        CAST(p.target_day AS TIMESTAMP) + INTERVAL '1 hour' AS slot_end
    FROM params p

    UNION ALL

    SELECT
        ts.studio_id,
        ts.slot_end,
        ts.slot_end + INTERVAL '1 hour'
    FROM time_slots ts
    JOIN params p
        ON ts.studio_id = p.target_studio_id
    WHERE ts.slot_end < CAST(p.target_day AS TIMESTAMP) + INTERVAL '24 hour'
)
SELECT
    ts.studio_id,
    s.studio_name,
    ts.slot_start,
    ts.slot_end,
    CASE
        WHEN COUNT(b.booking_id) > 0 THEN 'booked'
        ELSE 'free'
    END AS slot_status
FROM time_slots ts
JOIN music_studio.studios s
    ON s.studio_id = ts.studio_id
LEFT JOIN music_studio.bookings b
    ON b.studio_id = ts.studio_id
   AND b.status IN ('created', 'confirmed', 'completed')
   AND b.start_time < ts.slot_end
   AND b.end_time > ts.slot_start
GROUP BY
    ts.studio_id,
    s.studio_name,
    ts.slot_start,
    ts.slot_end
ORDER BY ts.slot_start;

-- 2. Определение оборудования, которое уже проходило обслуживание
SELECT
    e.equipment_id,
    e.equipment_name,
    e.equipment_type,
    s.studio_name,
    COUNT(em.maintenance_id) AS maintenance_count
FROM music_studio.equipment e
JOIN music_studio.studios s
    ON s.studio_id = e.studio_id
JOIN music_studio.equipment_maintenance em
    ON em.equipment_id = e.equipment_id
GROUP BY
    e.equipment_id,
    e.equipment_name,
    e.equipment_type,
    s.studio_name
ORDER BY maintenance_count DESC, e.equipment_id;

-- 3. Подсчёт суммарной стоимости обслуживания для каждой единицы оборудования
SELECT
    e.equipment_id,
    e.equipment_name,
    e.equipment_type,
    SUM(em.maintenance_cost) AS total_maintenance_cost,
    MAX(em.maintenance_date) AS last_maintenance_date
FROM music_studio.equipment e
JOIN music_studio.equipment_maintenance em
    ON em.equipment_id = e.equipment_id
GROUP BY
    e.equipment_id,
    e.equipment_name,
    e.equipment_type
ORDER BY total_maintenance_cost DESC, e.equipment_id;

-- 4. Определение пользователей с наибольшим количеством бронирований
SELECT
    u.user_id,
    u.full_name,
    COUNT(b.booking_id) AS bookings_count
FROM music_studio.users u
LEFT JOIN music_studio.bookings b
    ON b.user_id = u.user_id
GROUP BY u.user_id, u.full_name
ORDER BY bookings_count DESC, u.user_id;

-- 5. Поиск бронирований, для которых отсутствуют платежи
SELECT
    b.booking_id,
    u.full_name,
    s.studio_name,
    b.start_time,
    b.end_time,
    b.status,
    b.total_cost
FROM music_studio.bookings b
JOIN music_studio.users u
    ON u.user_id = b.user_id
JOIN music_studio.studios s
    ON s.studio_id = b.studio_id
LEFT JOIN music_studio.payments p
    ON p.booking_id = b.booking_id
WHERE p.booking_id IS NULL
ORDER BY b.start_time;

-- 6. Выбор оборудования, находящегося в ремонте или неисправном состоянии
SELECT
    e.equipment_id,
    e.equipment_name,
    e.equipment_type,
    s.studio_name,
    e.status
FROM music_studio.equipment e
JOIN music_studio.studios s
    ON s.studio_id = e.studio_id
WHERE e.status IN ('maintenance', 'broken')
ORDER BY s.studio_name, e.equipment_name;

-- 7. Определение пользователей, суммарные расходы которых превышают среднее значение
WITH user_spending AS (
    SELECT
        u.user_id,
        u.full_name,
        CAST(COALESCE(SUM(b.total_cost), 0) AS NUMERIC(12, 2)) AS total_spent
    FROM music_studio.users u
    LEFT JOIN music_studio.bookings b
        ON b.user_id = u.user_id
    GROUP BY u.user_id, u.full_name
)
SELECT
    us.user_id,
    us.full_name,
    us.total_spent
FROM user_spending us
WHERE us.total_spent > (
    SELECT AVG(total_spent)
    FROM user_spending
)
ORDER BY us.total_spent DESC, us.user_id;

-- 8. Определение студий с выручкой выше средней по всем студиям
WITH studio_revenue AS (
    SELECT
        s.studio_id,
        s.studio_name,
        CAST(COALESCE(SUM(b.total_cost), 0) AS NUMERIC(12, 2)) AS total_revenue
    FROM music_studio.studios s
    LEFT JOIN music_studio.bookings b
        ON b.studio_id = s.studio_id
       AND b.status = 'completed'
    GROUP BY s.studio_id, s.studio_name
)
SELECT
    sr.studio_id,
    sr.studio_name,
    sr.total_revenue
FROM studio_revenue sr
WHERE sr.total_revenue > (
    SELECT AVG(total_revenue)
    FROM studio_revenue
)
ORDER BY sr.total_revenue DESC, sr.studio_id;

-- 9. Определение наиболее часто используемого оборудования по количеству включений в бронирования
SELECT
    e.equipment_id,
    e.equipment_name,
    e.equipment_type,
    s.studio_name,
    COUNT(be.booking_id) AS usage_count
FROM music_studio.equipment e
JOIN music_studio.studios s
    ON s.studio_id = e.studio_id
LEFT JOIN music_studio.booking_equipment be
    ON be.equipment_id = e.equipment_id
GROUP BY
    e.equipment_id,
    e.equipment_name,
    e.equipment_type,
    s.studio_name
ORDER BY usage_count DESC, e.equipment_id;

-- 10. Поиск пользователей, имеющих бронирования, но не оставивших ни одного отзыва
SELECT
    u.user_id,
    u.full_name,
    COUNT(DISTINCT b.booking_id) AS bookings_count
FROM music_studio.users u
JOIN music_studio.bookings b
    ON b.user_id = u.user_id
WHERE NOT EXISTS (
    SELECT 1
    FROM music_studio.reviews r
    WHERE r.user_id = u.user_id
)
GROUP BY u.user_id, u.full_name
ORDER BY bookings_count DESC, u.user_id;
