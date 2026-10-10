import importlib.util
import pathlib
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "validate_ufo_json.py"
spec = importlib.util.spec_from_file_location("validate_ufo_json", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class JsonValidationTests(unittest.TestCase):
    def test_valid_object(self):
        self.assertEqual(module.validate('{"Status": "CONTINUE"}')[0], True)

    def test_rejects_invalid_json_without_echoing_private_data(self):
        secret = "private-token-must-not-appear"
        ok, message = module.validate('{"secret": "' + secret + '", "Action": [}')
        self.assertFalse(ok)
        self.assertIn("line=", message)
        self.assertNotIn(secret, message)
        self.assertNotIn("Action", message)

    def test_rejects_non_object(self):
        ok, message = module.validate("[]")
        self.assertFalse(ok)
        self.assertEqual(message, "invalid-shape: expected JSON object")

    def test_accepts_utf8_bom_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = pathlib.Path(tmp) / "model.json"
            file.write_text('{"status":"ok"}', encoding="utf-8-sig")
            self.assertTrue(module.validate(file.read_text(encoding="utf-8-sig"))[0])


if __name__ == "__main__":
    unittest.main()
