from ..model import Distro, Family, SandboxStrategy

def choose_strategy(distro: Distro, requested: str | None = None) -> SandboxStrategy:
    if requested:
        return SandboxStrategy(requested)
    if distro.family is Family.DEBIAN and distro.apparmor_restricted:
        return SandboxStrategy.APPARMOR
    return SandboxStrategy.SETUID
