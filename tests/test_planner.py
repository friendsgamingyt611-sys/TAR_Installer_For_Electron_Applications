import tempfile
import unittest
from pathlib import Path
from tifea.model import AppInfo, Distro, Family, SandboxStrategy
from tifea.planner import build_plan

class TestPlanner(unittest.TestCase):
    def test_planner_does_not_touch_filesystem(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            app = AppInfo('demo', 'Demo', '1.0', Path(tmp_dir) / 'demo.tar.gz', 'linux-unpacked', 'demo', 'chrome-sandbox', None, None, 10)
            plan = build_plan(app, Distro('ubuntu', 'Ubuntu', '24.04', Family.DEBIAN), SandboxStrategy.APPARMOR)
            self.assertTrue(any(action.type == 'write_apparmor_profile' for action in plan.actions))
            self.assertTrue(any(action.type == 'write_file' for action in plan.actions))

if __name__ == '__main__':
    unittest.main()
