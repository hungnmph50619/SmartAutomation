import unittest
from types import SimpleNamespace
from smartautomation.window_handoff_contract import verify_window_selection


class WindowHandoffContractTests(unittest.TestCase):
    def test_valid_selected_window(self):
        result=[SimpleNamespace(status="success",result={"root_name":"Document","window_info":{"name":"Document"}})]
        self.assertTrue(verify_window_selection("select_application_window",result,"3")["handoff_allowed"])

    def test_shell_action_cannot_enable_handoff(self):
        result=[{"status":"success","result":{"root_name":"Anything","window_info":{}}}]
        self.assertFalse(verify_window_selection("run_shell",result,"3")["handoff_allowed"])

    def test_failed_or_missing_selection_never_enables_handoff(self):
        values=[[],["error"],[{"status":"failure","result":{"root_name":"Document","window_info":{}}}],
                [{"status":"success","result":"error"}],
                [{"status":"success","result":{"root_name":"","window_info":{}}}]]
        for value in values:
            with self.subTest(value=value):
                self.assertFalse(verify_window_selection("select_application_window",value,"3")["handoff_allowed"])

    def test_unidentified_window_cannot_enable_handoff(self):
        self.assertFalse(verify_window_selection("select_application_window",[{"status":"success","result":{"root_name":"x","window_info":{}}}],None)["handoff_allowed"])


if __name__=="__main__":
    unittest.main()
