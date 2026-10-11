import unittest

from smartautomation.jobs import ufo_process_environment


class UfoProcessEncodingTests(unittest.TestCase):
    def test_utf8_settings_override_legacy_codepage(self):
        source = {"PYTHONIOENCODING": "cp1252", "PATH": "example"}
        result = ufo_process_environment(source)
        self.assertEqual(result["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(result["PYTHONUTF8"], "1")
        self.assertEqual(result["PATH"], "example")
        self.assertEqual(source["PYTHONIOENCODING"], "cp1252")


if __name__ == "__main__":
    unittest.main()
