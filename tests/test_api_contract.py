"""FastAPI smoke tests, skipped cleanly when optional UI dependencies are absent."""
import importlib.util
import unittest

@unittest.skipUnless(importlib.util.find_spec("fastapi") is not None, "optional FastAPI not installed")
class APITests(unittest.TestCase):
    def test_read_only_api_exists(self):
        from smartautomation.api import app
        paths = {route.path for route in app.routes}
        self.assertIn("/api/status", paths)
        self.assertIn("/api/readiness", paths)
        self.assertNotIn("/api/run", paths)
        self.assertNotIn("/api/ufo/run", paths)
