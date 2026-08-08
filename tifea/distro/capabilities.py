from pathlib import Path
from ..model import Distro

def has_command(name: str) -> bool:
    return any((Path(directory) / name).exists() for directory in ("/usr/bin", "/usr/sbin", "/bin", "/sbin"))

def summary(distro: Distro) -> dict[str, bool | str]:
    return {"apparmor_restricted": distro.apparmor_restricted, "selinux_enforcing": distro.selinux_enforcing, "package_manager": distro.package_manager, "desktop_validator": has_command("desktop-file-validate"), "restorecon": has_command("restorecon")}
