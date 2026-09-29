-- =====================================================
-- 02 APPOINTMENT ANALYTICS
-- =====================================================


-- Query 1: Appointment status summary
-- Shows the number and percentage of appointments by status.
SELECT
    a.appointment_status,
    COUNT(a.appointment_id) AS total_appointments,
    ROUND(
        COUNT(a.appointment_id) * 100.0 /
        (SELECT COUNT(*) FROM appointments),
        2
    ) AS percentage
FROM appointments a
GROUP BY a.appointment_status
ORDER BY total_appointments DESC;


-- Query 2: Average waiting time by department
-- Shows which departments have longer appointment waiting times.
SELECT
    d.department_name,
    COUNT(a.appointment_id) AS total_appointments,
    ROUND(AVG(a.wait_time_days), 2) AS average_wait_time
FROM appointments a
JOIN departments d
    ON a.department_id = d.department_id
GROUP BY d.department_name
ORDER BY average_wait_time DESC;


-- Query 3: No-show rate by department
-- Shows the number and percentage of missed appointments by department.
SELECT
    d.department_name,
    COUNT(a.appointment_id) AS total_appointments,
    SUM(
        CASE
            WHEN a.appointment_status = 'No-Show' THEN 1
            ELSE 0
        END
    ) AS no_show_count,
    ROUND(
        SUM(
            CASE
                WHEN a.appointment_status = 'No-Show' THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(a.appointment_id),
        2
    ) AS no_show_rate
FROM appointments a
JOIN departments d
    ON a.department_id = d.department_id
GROUP BY d.department_name
ORDER BY no_show_rate DESC;