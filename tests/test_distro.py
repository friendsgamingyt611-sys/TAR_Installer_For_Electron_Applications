import unittest
from tifea.model import Distro, Family
from tifea.distro.confinement import choose_strategy

class TestDistroConfinement(unittest.TestCase):
    def test_debian_restricted_defaults_to_apparmor(self):
        distro = Distro('ubuntu', 'Ubuntu', '24.04', Family.DEBIAN, apparmor_restricted=True)
        self.assertEqual(choose_strategy(distro).value, 'apparmor')

    def test_redhat_defaults_to_setuid(self):
        distro = Distro('fedora', 'Fedora', '40', Family.REDHAT)
        self.assertEqual(choose_strategy(distro).value, 'setuid')

if __name__ == '__main__':
    unittest.main()
