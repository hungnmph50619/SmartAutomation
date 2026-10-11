import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from smartautomation.export_diagnostics import export
from smartautomation.ufo import UfoConfig


class ProcessDiagnosticTests(unittest.TestCase):
    def test_zip_contains_stdout_stderr_without_unrelated_logs(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            task="smartautomation-a1b2c3d4"
            log=base/"ufo"/"logs"/task
            log.mkdir(parents=True)
            (log/"response.log").write_text("test",encoding="utf-8")
            process=base/"process"
            process.mkdir()
            (process/(task+".stderr.log")).write_text("Traceback: handoff error",encoding="utf-8")
            (process/"smartautomation-ffffffff.stderr.log").write_text("other task",encoding="utf-8")
            with patch.dict(os.environ,{"SMARTAUTOMATION_PROCESS_LOGS":str(process)}), patch("smartautomation.export_diagnostics.UfoConfig.from_environment",return_value=UfoConfig(base/"ufo")):
                archive=export(task,desktop=base)
            with zipfile.ZipFile(archive) as z:
                self.assertIn("process/"+task+".stderr.log",z.namelist())
                self.assertNotIn("process/smartautomation-ffffffff.stderr.log",z.namelist())


if __name__=="__main__":
    unittest.main()
