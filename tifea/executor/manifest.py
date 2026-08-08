from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from ..model import Action, Family, SandboxStrategy

SCHEMA_VERSION = 1

def manifest_path(appid: str) -> Path:
    primary = Path.home() / '.local/share/tifea' / appid / 'manifest.json'
    if primary.exists():
        return primary
    legacy = Path.home() / '.local/share/targz-installer' / appid / 'manifest.json'
    if legacy.exists():
        return legacy
    return primary


@dataclass
class Manifest:
    appid: str
    display_name: str
    version_hint: str
    install_time: str
    distro_family: str
    sandbox_strategy: str
    actions: list[Action]
    status: str = 'in_progress'
    schema_version: int = SCHEMA_VERSION
    current_action: str | None = None
    error_info: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data['actions'] = [a.as_dict() for a in self.actions]
        return data

def atomic_write(manifest: Manifest) -> None:
    destination = manifest_path(manifest.appid)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(manifest.to_dict(), indent=2) + '\n')
    temporary.replace(destination)

def load_manifest(appid: str) -> Manifest:
    data = json.loads(manifest_path(appid).read_text())
    actions = [Action(**item) for item in data.pop('actions')]
    data.pop('schema_version', None)
    return Manifest(actions=actions, **data)

def new_manifest(plan) -> Manifest:
    return Manifest(plan.app.appid, plan.app.display_name, plan.app.version_hint, datetime.now(timezone.utc).isoformat(), plan.distro.family.value, plan.strategy.value, plan.actions)

def adopt_manifest(app, distro, system_root: Path, strategy: SandboxStrategy) -> Manifest:
    """Create a baseline ledger for an existing installation not originally managed by TIFEA."""
    app_root = system_root.resolve()
    actions = [
        Action('mkdir', path=str(app_root), done=True),
        Action('copy_tree', src=str(app.archive), dst=str(app_root), done=True),
        Action('symlink', path=f'/opt/{app.appid}', target=str(app_root), done=True),
        Action('write_file', path=f'/usr/share/applications/{app.appid}.desktop', done=True),
        Action('symlink', path=f'/usr/local/bin/{app.appid}', target=str(app_root / app.executable), done=True),
        Action('xdg_mime_default', path=f'/usr/share/applications/{app.appid}.desktop', done=True),
    ]
    manifest = Manifest(app.appid, app.display_name, app.version_hint, datetime.now(timezone.utc).isoformat(), distro.family.value, strategy.value, actions, status='adopted')
    atomic_write(manifest)
    return manifest
