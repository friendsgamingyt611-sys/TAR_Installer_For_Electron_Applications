from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from ..detector.inspect import inspect_archive
from ..detector.metadata import app_id
from ..executor.manifest import load_manifest, manifest_path
from ..model import AppInfo, SandboxStrategy

@dataclass(frozen=True)
class Issue:
    key: str
    label: str
    detail: str
    fixable: bool = True

@dataclass(frozen=True)
class Comparison:
    app: AppInfo
    system_path: Path
    manifest: object | None
    issues: list[Issue]
    checks: list[tuple[str, bool, str]]

def _xdg(mime: str) -> str:
    try:
        return subprocess.check_output(['xdg-mime', 'query', 'default', mime], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ''

def _find_manifest(appid: str, root: Path):
    try:
        return load_manifest(appid)
    except (OSError, ValueError, TypeError):
        pass
    for base in [Path.home() / '.local/share/tifea', Path.home() / '.local/share/targz-installer']:
        for candidate in base.glob('*/manifest.json') if base.exists() else []:
            try:
                data = json.loads(candidate.read_text())
                actions = data.get('actions', [])
                if any(action.get('type') == 'symlink' and action.get('path') == f'/opt/{appid}' and Path(action.get('target', '')).resolve() == root for action in actions):
                    return load_manifest(candidate.parent.name)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
    return None


def compare(system_path: str | Path, tarball: str | Path) -> Comparison:
    app = inspect_archive(tarball)
    requested = Path(system_path).expanduser()
    appid = app_id(requested.name)
    root = requested.resolve()
    manifest = _find_manifest(appid, root)
    issues: list[Issue] = []
    checks: list[tuple[str, bool, str]] = []
    if not requested.exists():
        checks.append(('system application path exists', False, str(requested)))
        issues.append(Issue('system_path', 'System application path missing', f'{requested} does not exist', False))
        return Comparison(app, requested, None, issues, checks)
    binary = root / app.executable
    ok = binary.is_file() and os.access(binary, os.X_OK)
    checks.append(('executable matches archive', ok, str(binary)))
    if not ok: issues.append(Issue('executable', 'Executable mismatch', f'missing or not executable: {binary}'))
    if manifest is None: issues.append(Issue('manifest', 'Manifest missing', f'no TIFEA manifest for {appid}; check is read-only and will not create installation history', False))
    else:
        same_version = manifest.version_hint == app.version_hint
        checks.append(('manifest version matches tarball', same_version, f'installed={manifest.version_hint} archive={app.version_hint}'))
        if not same_version: issues.append(Issue('version', 'Version mismatch', f'installed {manifest.version_hint}, archive {app.version_hint}'))
    desktop = Path('/usr/share/applications') / f'{appid}.desktop'
    desktop_text = desktop.read_text(errors='replace') if desktop.is_file() else ''
    desktop_ok = desktop.is_file() and f'Exec=/opt/{appid}/{app.executable}' in desktop_text
    checks.append(('desktop entry matches executable', desktop_ok, str(desktop)))
    if not desktop_ok: issues.append(Issue('desktop', 'Desktop entry mismatch', str(desktop)))
    if app.icon:
        installed_icon = root / app.icon
        actual_hash = hashlib.sha256(installed_icon.read_bytes()).hexdigest() if installed_icon.is_file() else None
        icon_ok = actual_hash == app.icon_sha256 and f'Icon=/opt/{appid}/{app.icon}' in desktop_text
        checks.append(('original icon matches archive', icon_ok, f'{installed_icon} sha256={actual_hash or "missing"}'))
        if not icon_ok: issues.append(Issue('icon', 'Icon mismatch', f'expected original icon at {installed_icon}'))
    else:
        checks.append(('archive contains icon', True, 'no icon detected or extracted from archive'))
    mime_ok = all(_xdg(mime) == f'{appid}.desktop' for mime in ('x-scheme-handler/http', 'x-scheme-handler/https', 'text/html'))
    checks.append(('xdg-open handlers registered', mime_ok, f'http={_xdg("x-scheme-handler/http")} https={_xdg("x-scheme-handler/https")} html={_xdg("text/html")}'))
    if not mime_ok: issues.append(Issue('xdg', 'xdg-open handlers missing', 'HTTP, HTTPS, and text/html are not all assigned'))
    restorecon_ok = True
    if shutil.which('selinuxenabled') and subprocess.run(['selinuxenabled']).returncode == 0:
        restorecon_ok = subprocess.run(['matchpathcon', '-n', str(root)], capture_output=True).returncode == 0 if shutil.which('matchpathcon') else True
    checks.append(('SELinux path check', restorecon_ok, str(root)))
    if not restorecon_ok: issues.append(Issue('selinux', 'SELinux labeling check failed', str(root)))
    return Comparison(app, requested, manifest, issues, checks)
