import tempfile
import unittest
import zipfile
from pathlib import Path
from smartautomation.docx_verification import verify_docx, verify_docx_package


def make_docx(path: Path, value: str):
    xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           '<w:body><w:p><w:r><w:t>' + value +
           '</w:t></w:r></w:p></w:body></w:document>')
    with zipfile.ZipFile(path, "w") as output:
        output.writestr("[Content_Types].xml", "<Types/>")
        output.writestr("word/document.xml", xml)


class DocxVerificationTests(unittest.TestCase):
    def test_structural_check_rejects_fake_docx(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "fake.docx"
            path.write_bytes(b"not really a Word document")
            self.assertFalse(verify_docx_package(path)["package_valid"])

    def test_structural_check_accepts_real_package_without_claiming_content(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "valid.docx"
            make_docx(path, "some other content")
            result = verify_docx_package(path)
            self.assertTrue(result["package_valid"])
            self.assertNotIn("verified", result)

    def test_valid_content(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.docx"
            make_docx(path, "SMARTAUTOMATION WORD TEST")
            report = verify_docx(path, "SMARTAUTOMATION WORD TEST")
            self.assertTrue(report["verified"])

    def test_incorrect_text_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.docx"
            make_docx(path, "Different content")
            self.assertEqual(verify_docx(path, "SMARTAUTOMATION WORD TEST")["status"], "content_mismatch")

    def test_missing_and_invalid_files_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "missing.docx"
            self.assertEqual(verify_docx(path, "Hello")["status"], "file_missing")
            path.write_text("not a docx", encoding="utf-8")
            self.assertEqual(verify_docx(path, "Hello")["status"], "unreadable_docx")

    def test_empty_expectation_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "missing.docx"
            self.assertEqual(verify_docx(path, " ")["status"], "empty_expected_text")


if __name__ == "__main__":
    unittest.main()
