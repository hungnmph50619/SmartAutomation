import tempfile
import unittest
from pathlib import Path
from smartautomation.save_target import requested_save_target, assess_saved_target, guide_save_target


class SaveTargetTests(unittest.TestCase):
    def test_explicit_desktop_target(self):
        root=Path("C:/Users/Test")
        target=requested_save_target("Save SmartAutomation-Word-Test.docx on Desktop",home=root)
        self.assertEqual(target,root/"Desktop"/"SmartAutomation-Word-Test.docx")
        self.assertIn(str(target),guide_save_target("Save SmartAutomation-Word-Test.docx on Desktop",target))

    def test_no_guess_if_folder_missing_or_ambiguous(self):
        self.assertIsNone(requested_save_target("Create Document.docx",home=Path("/tmp")))
        self.assertIsNone(requested_save_target("Create A.docx and B.docx on Desktop",home=Path("/tmp")))
        self.assertIsNone(requested_save_target("Save A.docx on Desktop and Documents",home=Path("/tmp")))

    def test_verify_only_correct_location(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"Documents").mkdir()
            (root/"Desktop").mkdir()
            (root/"Documents"/"A.docx").write_bytes(b"test")
            target=root/"Desktop"/"A.docx"
            self.assertEqual(assess_saved_target(target)["save_target_status"],"missing_target_file")
            target.write_bytes(b"test")
            self.assertTrue(assess_saved_target(target)["save_target_verified"])


if __name__=="__main__":
    unittest.main()
