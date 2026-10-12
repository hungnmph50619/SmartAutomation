import ast
import tempfile
import unittest
from pathlib import Path

from smartautomation.ufo_start_apps_patch import (
    RELATIVE_PATH, BACKUP_SUFFIX, MARKER, ANCHOR, INSERT, modify
)


class StartAppsUfoPatchTests(unittest.TestCase):
    def test_patch_is_reversible_and_syntax_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / RELATIVE_PATH
            source.parent.mkdir(parents=True)
            source.write_text("def host():\n" + ANCHOR + "\n", encoding="utf-8")
            before = source.read_bytes()
            self.assertEqual(modify(root), "applied")
            current = source.read_text(encoding="utf-8")
            self.assertIn(MARKER, current)
            self.assertIn("discover_installed_applications", current)
            self.assertIn("launch_installed_application", current)
            self.assertIn("select_application_window", current)
            ast.parse(current)
            self.assertEqual(modify(root), "already_applied")
            self.assertEqual(modify(root, restore=True), "restored")
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(source.with_name(source.name + BACKUP_SUFFIX).exists())

    def test_does_not_modify_unrecognized_upstream(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / RELATIVE_PATH
            source.parent.mkdir(parents=True)
            source.write_text("unknown UFO version", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Unsupported"):
                modify(root)
            self.assertEqual(source.read_text(encoding="utf-8"), "unknown UFO version")

    def test_no_arbitrary_shell_runner(self):
        self.assertNotIn("shell=True", INSERT)
        self.assertNotIn("eval(", INSERT)
        self.assertIn("Get-StartApps", INSERT)
        self.assertIn("uniquely installed", INSERT)


if __name__ == "__main__":
    unittest.main()
