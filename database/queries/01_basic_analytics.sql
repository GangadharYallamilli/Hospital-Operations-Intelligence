-- =====================================================
-- 01 BASIC ANALYTICS
-- =====================================================


-- Query 1: Total admissions by department
-- Find how many admissions each department handled.
SELECT
    d.department_name,
    COUNT(a.admission_id) AS total_admissions
FROM admissions a
JOIN departments d
    ON a.department_id = d.department_id
GROUP BY d.department_name
ORDER BY total_admissions DESC;


-- Query 2: Average length of stay by department
-- Find the average number of days patients stay in each department.
SELECT
    d.department_name,
    ROUND(AVG(a.length_of_stay), 2) AS average_length_of_stay
FROM admissions a
JOIN departments d
    ON a.department_id = d.department_id
GROUP BY d.department_name
ORDER BY average_length_of_stay DESC;


-- Query 3: Monthly admissions trend
-- Find the number of admissions for each month.
SELECT
    DATE_FORMAT(a.admission_date, '%Y-%m') AS admission_month,
    COUNT(a.admission_id) AS total_admissions
FROM admissions a
GROUP BY DATE_FORMAT(a.admission_date, '%Y-%m')
ORDER BY admission_month;