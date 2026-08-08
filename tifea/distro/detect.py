from pathlib import Path
import os
from ..model import Distro, Family

def _release() -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in Path('/etc/os-release').read_text().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                values[key] = value.strip().strip('"')
    except OSError:
        pass
    return values

def detect() -> Distro:
    r = _release(); ident = r.get('ID', 'unknown'); like = f"{ident} {r.get('ID_LIKE', '')}".lower()
    family = Family.DEBIAN if any(x in like for x in ('debian', 'ubuntu', 'mint')) else Family.REDHAT if any(x in like for x in ('fedora', 'rhel', 'centos', 'alma', 'rocky')) else Family.UNKNOWN
    restricted = family is Family.DEBIAN and Path('/proc/sys/kernel/apparmor_restrict_unprivileged_userns').read_text().strip() == '1' if Path('/proc/sys/kernel/apparmor_restrict_unprivileged_userns').exists() else False
    enforcing = Path('/sys/fs/selinux/enforce').read_text().strip() == '1' if Path('/sys/fs/selinux/enforce').exists() else False
    manager = 'apt' if family is Family.DEBIAN else 'dnf' if family is Family.REDHAT and Path('/usr/bin/dnf').exists() else 'yum' if family is Family.REDHAT else 'unknown'
    return Distro(ident, r.get('PRETTY_NAME', ident), r.get('VERSION_ID', 'unknown'), family, restricted, enforcing, manager)
