-- =====================================================
-- 06 DATABASE VALIDATION
-- =====================================================


-- Check 1: Verify row counts in all tables.
SELECT 'departments' AS table_name, COUNT(*) AS total_rows
FROM departments
UNION ALL
SELECT 'admissions', COUNT(*)
FROM admissions
UNION ALL
SELECT 'appointments', COUNT(*)
FROM appointments
UNION ALL
SELECT 'beds', COUNT(*)
FROM beds
UNION ALL
SELECT 'equipment', COUNT(*)
FROM equipment;


-- Check 2: Check for invalid department IDs in admissions.
SELECT COUNT(*) AS invalid_admission_departments
FROM admissions a
LEFT JOIN departments d
    ON a.department_id = d.department_id
WHERE d.department_id IS NULL;


-- Check 3: Check for invalid department IDs in appointments.
SELECT COUNT(*) AS invalid_appointment_departments
FROM appointments a
LEFT JOIN departments d
    ON a.department_id = d.department_id
WHERE d.department_id IS NULL;


-- Check 4: Check for invalid department IDs in beds.
SELECT COUNT(*) AS invalid_bed_departments
FROM beds b
LEFT JOIN departments d
    ON b.department_id = d.department_id
WHERE d.department_id IS NULL;


-- Check 5: Check for invalid department IDs in equipment.
SELECT COUNT(*) AS invalid_equipment_departments
FROM equipment e
LEFT JOIN departments d
    ON e.department_id = d.department_id
WHERE d.department_id IS NULL;