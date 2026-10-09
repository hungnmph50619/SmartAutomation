"""Offline repository hygiene checks; no UFO execution or API access."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class RepositoryContractTests(unittest.TestCase):
    def test_upstream_is_not_vendor_copied(self):
        self.assertFalse((ROOT / "vendor" / "UFO").exists())

    def test_no_legacy_csharp_operator(self):
        self.assertFalse((ROOT / "src" / "PersonalAI.Web").exists())
        self.assertFalse((ROOT / "src" / "PersonalAI.WindowsAutomation").exists())

    def test_bootstrap_and_ignore_are_present(self):
        self.assertTrue((ROOT / "scripts" / "bootstrap-ufo.ps1").is_file())
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("vendor/UFO/", ignored)
        self.assertIn("agents.yaml", ignored)
        self.assertIn(".env", ignored)

if __name__ == "__main__":
    unittest.main()
