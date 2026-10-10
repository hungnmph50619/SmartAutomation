import tempfile
import unittest
from pathlib import Path
from smartautomation.ufo_compatibility import inspect_ufo_hooks


class UfoCompatibilityTests(unittest.TestCase):
    def test_missing_ufo_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            probe = inspect_ufo_hooks(Path(folder))
        self.assertFalse(probe["available"])
        self.assertFalse(probe["action_guard_supported"])

    def test_known_processor_hook_does_not_authorize_action_blocking(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            one = root / "ufo/agents/processors/core/processor_framework.py"
            two = root / "ufo/agents/processors/strategies/host_agent_processing_strategy.py"
            one.parent.mkdir(parents=True)
            two.parent.mkdir(parents=True)
            one.write_text(
                "class ProcessorTemplate:\n"
                " async def process(self):\n"
                "  await middleware.before_process(self, context)\n"
                "  await strategy.execute(self.agent, context)\n",
                encoding="utf-8"
            )
            two.write_text(
                "class HostActionExecutionStrategy:\n"
                " async def execute(self, agent, context):\n"
                "  return None\n",
                encoding="utf-8"
            )
            probe = inspect_ufo_hooks(root)
            self.assertTrue(probe["available"])
            self.assertTrue(probe["processor_middleware_detected"])
            self.assertFalse(probe["action_guard_supported"])

    def test_unknown_structure_stays_disabled(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            one = root / "ufo/agents/processors/core/processor_framework.py"
            two = root / "ufo/agents/processors/strategies/host_agent_processing_strategy.py"
            one.parent.mkdir(parents=True)
            two.parent.mkdir(parents=True)
            one.write_text("class Other: pass", encoding="utf-8")
            two.write_text("class Other: pass", encoding="utf-8")
            self.assertFalse(inspect_ufo_hooks(root)["available"])


if __name__ == "__main__":
    unittest.main()
