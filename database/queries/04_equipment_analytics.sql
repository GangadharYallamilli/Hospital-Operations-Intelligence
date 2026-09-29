-- =====================================================
-- 04 EQUIPMENT ANALYTICS
-- =====================================================


-- Query 1: Equipment status summary
-- Shows how many equipment units are operational,
-- under maintenance, or out of service.
SELECT
    e.equipment_status,
    COUNT(e.equipment_id) AS total_equipment,
    ROUND(
        COUNT(e.equipment_id) * 100.0 /
        (SELECT COUNT(*) FROM equipment),
        2
    ) AS percentage
FROM equipment e
GROUP BY e.equipment_status
ORDER BY total_equipment DESC;


-- Query 2: Equipment failures by type
-- Identifies equipment types with the highest number of failures.
SELECT
    e.equipment_type,
    COUNT(e.equipment_id) AS total_equipment,
    SUM(e.failure_count) AS total_failures,
    SUM(e.maintenance_count) AS total_maintenance
FROM equipment e
GROUP BY e.equipment_type
ORDER BY total_failures DESC;


-- Query 3: Equipment performance by department
-- Compares equipment usage and failures across departments.
SELECT
    d.department_name,
    COUNT(e.equipment_id) AS total_equipment,
    ROUND(AVG(e.usage_hours), 2) AS average_usage_hours,
    SUM(e.failure_count) AS total_failures
FROM equipment e
JOIN departments d
    ON e.department_id = d.department_id
GROUP BY d.department_name
ORDER BY total_failures DESC;