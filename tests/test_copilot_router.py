import unittest
from unittest.mock import patch

from backend.copilot_router import classify_question
from backend.sql_analytics import _query, run_sql_question, DATABASE_UNAVAILABLE


class CopilotRouterTests(unittest.TestCase):
    def test_required_questions_route_to_the_intended_backend(self):
        cases = {
            "What is the average length of stay?": ("sql", "average_length_of_stay"),
            "Which department has the most admissions?": ("sql", "most_admissions"),
            "How many appointments were cancelled?": ("sql", "cancelled_appointments_last_month"),
            "How many beds are occupied?": ("sql", "occupied_beds"),
            "How many equipment units are operational?": ("sql", "operational_equipment"),
            "What problems were mentioned in the annual report?": ("rag", None),
            "What does the quality report say about patient safety?": ("rag", None),
            "What is the predicted bed demand next week?": ("ml", "bed_forecast"),
            "What is the predicted length of stay?": ("ml", "length_of_stay"),
            "What is the predicted equipment failure risk?": ("ml", "equipment_failure"),
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                route = classify_question(question)
                self.assertEqual((route.intent, route.model), expected)

    def test_department_is_data_not_sql(self):
        route = classify_question("What is the average LOS in Cardiology?")
        self.assertEqual(route.intent, "sql")
        self.assertEqual(route.model, "average_length_of_stay")
        self.assertEqual(route.department, "Cardiology")

    def test_arbitrary_sql_is_not_a_supported_intent(self):
        self.assertEqual(classify_question("DROP TABLE admissions").intent, "clarify")

    def test_fixed_query_registry_contains_only_select_statements(self):
        keys = (
            "admissions_by_department",
            "average_los_by_department",
            "appointment_status_summary",
            "average_beds_by_department",
            "equipment_status_summary",
            "average_length_of_stay",
            "average_length_of_stay_by_department",
            "cancelled_appointments_last_month",
            "occupied_beds_latest_snapshot",
        )
        for key in keys:
            with self.subTest(key=key):
                query = _query(key).strip().lower()
                self.assertTrue(query.startswith("select"))
                self.assertFalse(any(token in query for token in (" insert ", " update ", " delete ", " drop ", " alter ", " truncate ")))

    def test_department_filter_is_a_bound_parameter(self):
        query = _query("average_length_of_stay_by_department")
        self.assertIn("%s", query)
        self.assertNotIn("Cardiology", query)

    def test_database_unavailable_fallback_is_explicit(self):
        with patch.dict("os.environ", {"MYSQL_READONLY_USER": "", "MYSQL_READONLY_PASSWORD": ""}):
            result = run_sql_question("occupied_beds")
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["answer"], DATABASE_UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()
