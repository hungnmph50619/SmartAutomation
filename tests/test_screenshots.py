import tempfile
import unittest
from pathlib import Path

from smartautomation.screenshots import list_images, image_file


class ScreenshotTests(unittest.TestCase):
    def test_lists_only_action_pngs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "logs" / "smartautomation-a1b2c3d4"
            log.mkdir(parents=True)
            (log / "action_step0.png").write_bytes(b"PNG")
            (log / "agents.yaml").write_text("secret")
            self.assertEqual([x["name"] for x in list_images(root, "smartautomation-a1b2c3d4")], ["action_step0.png"])
            self.assertEqual(image_file(root, "smartautomation-a1b2c3d4", "action_step0.png").name, "action_step0.png")

    def test_rejects_traversal_and_wrong_file_type(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                image_file(root, "../other", "action_step0.png")
            with self.assertRaises(ValueError):
                image_file(root, "smartautomation-a1b2c3d4", "../agents.yaml")
            with self.assertRaises(ValueError):
                image_file(root, "smartautomation-a1b2c3d4", "agents.yaml")


if __name__ == "__main__":
    unittest.main()
