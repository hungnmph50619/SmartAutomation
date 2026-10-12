import tempfile
import unittest
from pathlib import Path

from smartautomation.ufo_handoff_patch import (
    RELATIVE_PATH, BACKUP_SUFFIX, MARKER, OLD, NEW, modify,
)


class UfoHandoffPatchTests(unittest.TestCase):
    def create_source(self, directory: str, content: str) -> tuple[Path, Path]:
        root = Path(directory)
        source = root / RELATIVE_PATH
        source.parent.mkdir(parents=True)
        source.write_text(content, encoding="utf-8")
        return root, source

    def test_patch_restore_and_idempotency(self):
        with tempfile.TemporaryDirectory() as d:
            root, source = self.create_source(d, "prefix\n" + OLD + "\nsuffix\n")
            original = source.read_bytes()
            self.assertEqual(modify(root), "applied")
            self.assertIn(MARKER, source.read_text(encoding="utf-8"))
            self.assertIn("Window handoff refused", source.read_text(encoding="utf-8"))
            self.assertEqual(modify(root), "already_applied")
            self.assertEqual(modify(root, restore=True), "restored")
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse(source.with_name(source.name + BACKUP_SUFFIX).exists())

    def test_unsupported_upstream_source_is_left_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            root, source = self.create_source(d, "unrecognized version")
            with self.assertRaisesRegex(RuntimeError, "Unsupported"):
                modify(root)
            self.assertEqual(source.read_text(), "unrecognized version")

    def test_refuse_rollback_if_user_modified_patched_source(self):
        with tempfile.TemporaryDirectory() as d:
            root, source = self.create_source(d, OLD)
            modify(root)
            source.write_text("unrelated code", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "changed since patch"):
                modify(root, restore=True)
            self.assertEqual(source.read_text(encoding="utf-8"), "unrelated code")


if __name__ == "__main__":
    unittest.main()
