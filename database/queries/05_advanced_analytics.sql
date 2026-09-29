-- =====================================================
-- 05 ADVANCED ANALYTICS
-- =====================================================


-- Query 1: Rank departments by total admissions
-- RANK() assigns a position to each department based on admissions.
WITH department_admissions AS (
    SELECT
        a.department_id,
        COUNT(a.admission_id) AS total_admissions
    FROM admissions a
    GROUP BY a.department_id
)
SELECT
    d.department_name,
    da.total_admissions,
    RANK() OVER (
        ORDER BY da.total_admissions DESC
    ) AS admission_rank
FROM department_admissions da
JOIN departments d
    ON da.department_id = d.department_id
ORDER BY admission_rank;


-- Query 2: Monthly admissions with previous month comparison
-- LAG() allows us to compare each month with the previous month.
WITH monthly_admissions AS (
    SELECT
        DATE_FORMAT(a.admission_date, '%Y-%m') AS admission_month,
        COUNT(a.admission_id) AS total_admissions
    FROM admissions a
    GROUP BY DATE_FORMAT(a.admission_date, '%Y-%m')
)
SELECT
    admission_month,
    total_admissions,
    LAG(total_admissions) OVER (
        ORDER BY admission_month
    ) AS previous_month_admissions,
    total_admissions -
    LAG(total_admissions) OVER (
        ORDER BY admission_month
    ) AS change_from_previous_month
FROM monthly_admissions
ORDER BY admission_month;


-- Query 3: Departments with above-average length of stay
-- The CTE calculates department-level averages,
-- then the main query compares them with the hospital average.
WITH department_los AS (
    SELECT
        a.department_id,
        AVG(a.length_of_stay) AS average_los
    FROM admissions a
    GROUP BY a.department_id
),
hospital_average AS (
    SELECT
        AVG(a.length_of_stay) AS hospital_avg_los
    FROM admissions a
)
SELECT
    d.department_name,
    ROUND(dl.average_los, 2) AS average_length_of_stay,
    ROUND(ha.hospital_avg_los, 2) AS hospital_average_los
FROM department_los dl
JOIN departments d
    ON dl.department_id = d.department_id
CROSS JOIN hospital_average ha
WHERE dl.average_los > ha.hospital_avg_los
ORDER BY dl.average_los DESC;