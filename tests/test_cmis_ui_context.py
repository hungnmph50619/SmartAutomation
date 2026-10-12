import unittest
from smartautomation.cmis_ui_context import compare_ui_hierarchy


class UiContextTests(unittest.TestCase):
    def test_comparison_is_never_action_grounding(self):
        old = {"ui_control_type": "Button", "ui_parent_control_type": "Window"}
        current = {"ui_control_type": "Button", "ui_parent_control_type": "Window"}
        same = compare_ui_hierarchy(old, current)
        self.assertTrue(same["matches"])
        self.assertIsNone(same["action_suggestion"])
        self.assertFalse(same["execution_allowed"])
        different = compare_ui_hierarchy(old, {"ui_control_type": "Edit",
                                               "ui_parent_control_type": "Window"})
        self.assertFalse(different["matches"])
        unknown = compare_ui_hierarchy(old, {})
        self.assertEqual(unknown["status"], "insufficient_ui_context")

if __name__ == "__main__":
    unittest.main()
