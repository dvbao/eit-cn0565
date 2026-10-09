"""Configuration service used by the interface, and the configurable data folder."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.core.config import data_root  # noqa: E402
from app.services import configuration  # noqa: E402


class ConfigurationServiceTests(unittest.TestCase):
    def test_describes_the_repository_settings_and_design(self):
        m = configuration.describe_measurement(configuration.list_measurement_files()[0])
        self.assertEqual((m["problems"], m["n_measurements"], round(m["frame_s"], 1)), ([], 208, 20.6))
        d = configuration.describe_design(configuration.list_design_files()[0], configuration.list_measurement_files()[0])
        self.assertEqual((d["problems"], d["n_blocks"], round(d["task_hold_s"], 2)), ([], 39, 23.09))

    def test_data_root_can_point_elsewhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "data" / "hardware", Path(tmp) / "hardware")
            cfg = Path(tmp) / "hardware" / "measurement-16el-50kHz.json"
            settings = json.loads(cfg.read_text())
            settings.update(n_electrodes=8)                 # 8 electrodes with the 16-cup wiring
            cfg.write_text(json.dumps(settings))
            os.environ["EIT_DATA_ROOT"] = tmp
            try:
                self.assertEqual(data_root(), Path(tmp))
                m = configuration.describe_measurement(configuration.list_measurement_files()[0])
                self.assertEqual(configuration.list_design_files(), [])
            finally:
                del os.environ["EIT_DATA_ROOT"]
        self.assertEqual(m["n_measurements"], 40)
        self.assertTrue(any("defines 16 electrodes" in p for p in m["problems"]))


if __name__ == "__main__":
    unittest.main()
