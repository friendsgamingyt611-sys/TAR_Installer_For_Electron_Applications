import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from tifea.detector import inspect_archive
from tests.test_asar import create_mock_asar

class TestDetector(unittest.TestCase):
    def test_detects_electron_tarball(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive = Path(tmp_dir) / 'demo.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                for name, data in [('linux-unpacked/demo', b'#!/bin/sh\n'), ('linux-unpacked/chrome-sandbox', b'x'), ('linux-unpacked/resources/app/package.json', b'{"name":"demo","productName":"Demo","version":"1.0"}')]:
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            app = inspect_archive(archive)
            self.assertEqual(app.appid, 'demo')
            self.assertEqual(app.executable, 'demo')

    def test_detects_electron_asar_tarball(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive = Path(tmp_dir) / 'asar_demo.tar.gz'
            asar_data = create_mock_asar({
                'package.json': b'{"name":"asarapp","productName":"ASAR App","version":"2.1.0"}',
                'icon.png': b'\x89PNG\r\n\x1a\nfake_asar_icon_data'
            })
            with tarfile.open(archive, 'w:gz') as tar:
                for name, data in [
                    ('demo-x64/asarapp', b'#!/bin/sh\n'),
                    ('demo-x64/chrome-sandbox', b'x'),
                    ('demo-x64/resources/app.asar', asar_data)
                ]:
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))

            app = inspect_archive(archive)
            self.assertEqual(app.appid, 'asarapp')
            self.assertEqual(app.display_name, 'ASAR App')
            self.assertEqual(app.version_hint, '2.1.0')
            self.assertEqual(app.executable, 'asarapp')
            self.assertEqual(app.icon, 'icon.png')
            self.assertEqual(app.icon_target, 'demo-x64/resources/app.asar:icon.png')

if __name__ == '__main__':
    unittest.main()
