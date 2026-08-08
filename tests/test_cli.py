import unittest
from tifea.cli import parser

class TestCLIParser(unittest.TestCase):
    def setUp(self):
        self.parser = parser()

    def test_parse_install_command(self):
        args = self.parser.parse_args(['install', '/path/to/app.tar.gz', '--dry-run', '--sandbox', 'no-sandbox'])
        self.assertEqual(args.command, 'install')
        self.assertEqual(args.archive, ['/path/to/app.tar.gz'])
        self.assertTrue(args.dry_run)
        self.assertEqual(args.sandbox, 'no-sandbox')

    def test_parse_check_command(self):
        args = self.parser.parse_args(['check', '/opt/app', '/path/to/app.tar.gz'])
        self.assertEqual(args.command, 'check')
        self.assertEqual(args.system_path, '/opt/app')
        self.assertEqual(args.archive, '/path/to/app.tar.gz')

    def test_parse_list_command(self):
        args = self.parser.parse_args(['list'])
        self.assertEqual(args.command, 'list')

    def test_parse_uninstall_command(self):
        args = self.parser.parse_args(['uninstall', 'myapp'])
        self.assertEqual(args.command, 'uninstall')
        self.assertEqual(args.appid, 'myapp')

if __name__ == '__main__':
    unittest.main()
