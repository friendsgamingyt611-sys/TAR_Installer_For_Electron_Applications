import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tifea.executor.manifest import Manifest, atomic_write, load_manifest, manifest_path
from tifea.model import Action

class TestManifest(unittest.TestCase):
    def test_manifest_serialization(self):
        actions = [Action('mkdir', path='/opt/testapp', done=True)]
        manifest = Manifest(
            appid='testapp',
            display_name='Test App',
            version_hint='1.0.0',
            install_time='2026-08-08T00:00:00Z',
            distro_family='redhat',
            sandbox_strategy='setuid',
            actions=actions
        )
        data = manifest.to_dict()
        self.assertEqual(data['appid'], 'testapp')
        self.assertEqual(data['display_name'], 'Test App')
        self.assertEqual(len(data['actions']), 1)
        self.assertEqual(data['actions'][0]['type'], 'mkdir')

    def test_manifest_path_primary_and_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            home = Path(tmp_dir)
            with patch('pathlib.Path.home', return_value=home):
                primary = manifest_path('myappid')
                self.assertEqual(primary, home / '.local/share/tifea' / 'myappid' / 'manifest.json')

if __name__ == '__main__':
    unittest.main()
