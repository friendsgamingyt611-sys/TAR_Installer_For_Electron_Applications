from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

class Family(str, Enum):
    DEBIAN = "debian"
    REDHAT = "redhat"
    UNKNOWN = "unknown"

class SandboxStrategy(str, Enum):
    APPARMOR = "apparmor"
    SETUID = "setuid"
    NO_SANDBOX = "no-sandbox"

@dataclass(frozen=True)
class Distro:
    id: str
    name: str
    version: str
    family: Family
    apparmor_restricted: bool = False
    selinux_enforcing: bool = False
    package_manager: str = "unknown"

@dataclass(frozen=True)
class AppInfo:
    appid: str
    display_name: str
    version_hint: str
    archive: Path
    source_root: str
    executable: str
    chrome_sandbox: str | None
    icon: str | None
    icon_sha256: str | None
    size_bytes: int
    icon_target: str | None = None

@dataclass
class Action:
    type: str
    path: str | None = None
    src: str | None = None
    dst: str | None = None
    target: str | None = None
    mode: str | None = None
    owner: str | None = None
    content: str | None = None
    backup: str | None = None
    previous_mode: str | None = None
    previous_owner: str | None = None
    done: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass(frozen=True)
class InstallPlan:
    app: AppInfo
    distro: Distro
    versioned_root: Path
    strategy: SandboxStrategy
    actions: list[Action] = field(default_factory=list)
