-- =====================================================
-- 03 BED ANALYTICS
-- =====================================================


-- Query 1: Average bed occupancy by department
-- Shows which departments use their available beds the most.
SELECT
    d.department_name,
    ROUND(AVG(b.occupancy_rate), 2) AS average_occupancy_rate
FROM beds b
JOIN departments d
    ON b.department_id = d.department_id
GROUP BY d.department_name
ORDER BY average_occupancy_rate DESC;


-- Query 2: Average occupied and available beds by department
-- Shows the average number of beds currently occupied and available.
SELECT
    d.department_name,
    ROUND(AVG(b.occupied_beds), 2) AS average_occupied_beds,
    ROUND(AVG(b.available_beds), 2) AS average_available_beds
FROM beds b
JOIN departments d
    ON b.department_id = d.department_id
GROUP BY d.department_name
ORDER BY average_occupied_beds DESC;


-- Query 3: Monthly bed occupancy trend
-- Shows how hospital bed utilization changes month by month.
SELECT
    DATE_FORMAT(b.record_date, '%Y-%m') AS record_month,
    ROUND(AVG(b.occupancy_rate), 2) AS average_occupancy_rate
FROM beds b
GROUP BY DATE_FORMAT(b.record_date, '%Y-%m')
ORDER BY record_month;