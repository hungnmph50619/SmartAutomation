import tempfile
import unittest
import zipfile
from pathlib import Path
from smartautomation.docx_verification import verify_docx


def make_docx(path: Path, value: str):
    xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           '<w:body><w:p><w:r><w:t>' + value +
           '</w:t></w:r></w:p></w:body></w:document>')
    with zipfile.ZipFile(path, "w") as output:
        output.writestr("[Content_Types].xml", "<Types/>")
        output.writestr("word/document.xml", xml)


class DocxVerificationTests(unittest.TestCase):
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
