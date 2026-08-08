import os
import stat
import subprocess
import hashlib
from pathlib import Path
from .smoketest import smoke_test
from ..model import InstallPlan, SandboxStrategy

def verify(plan: InstallPlan) -> list[tuple[str, bool, str]]:
    root = plan.versioned_root; binary = root / plan.app.executable
    checks = [('binary present and executable', binary.is_file() and os.access(binary, os.X_OK), str(binary)), ('install symlink resolves', Path(f'/opt/{plan.app.appid}').is_dir(), f'/opt/{plan.app.appid}')]
    desktop = Path(f'/usr/share/applications/{plan.app.appid}.desktop')
    valid = desktop.is_file()
    validator = subprocess.run(['desktop-file-validate', str(desktop)], capture_output=True) if valid and shutil_which('desktop-file-validate') else None
    checks.append(('desktop entry valid', valid and (validator is None or validator.returncode == 0), str(desktop)))
    if plan.app.icon:
        icon = root / plan.app.icon
        icon_hash = hashlib.sha256(icon.read_bytes()).hexdigest() if icon.is_file() else None
        supported = icon.suffix.lower() in {'.png', '.svg', '.xpm', '.ico', '.icns'}
        original = icon_hash == plan.app.icon_sha256 if plan.app.icon_sha256 else icon.is_file()
        desktop_icon = next((line.split('=', 1)[1].strip() for line in desktop.read_text(errors='replace').splitlines() if line.startswith('Icon=')), '') if desktop.is_file() else ''
        points_to_icon = desktop_icon == str(Path(f'/opt/{plan.app.appid}') / plan.app.icon)
        checks.append(('original application icon present', icon.is_file() and supported and original and points_to_icon, f'{icon} sha256={icon_hash or "missing"} desktop_icon={desktop_icon or "missing"}'))
    else:
        checks.append(('application icon metadata', True, 'no icon detected or extracted from archive'))
    mime_values = {}
    for mime in ('x-scheme-handler/http', 'x-scheme-handler/https', 'text/html'):
        try:
            mime_values[mime] = subprocess.check_output(['xdg-mime', 'query', 'default', mime], text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            mime_values[mime] = ''
    xdg_ok = all(value == f'{plan.app.appid}.desktop' for value in mime_values.values())
    checks.append(('xdg-open handlers registered', xdg_ok, ', '.join(f'{key}={value or "missing"}' for key, value in mime_values.items())))
    if plan.app.chrome_sandbox and plan.strategy is SandboxStrategy.SETUID:
        sandbox = root / plan.app.chrome_sandbox
        if sandbox.exists():
            metadata = sandbox.stat()
            mode = stat.S_IMODE(metadata.st_mode)
            owner_ok = metadata.st_uid == 0 and metadata.st_gid == 0
            sandbox_ok = mode == 0o4755 and owner_ok
            detail = f'{sandbox} mode={mode:04o} uid={metadata.st_uid} gid={metadata.st_gid}'
        else:
            sandbox_ok = False
            detail = f'{sandbox} missing'
        checks.append(('chrome-sandbox mode 4755 and root-owned', sandbox_ok, detail))
    if plan.strategy is SandboxStrategy.APPARMOR: checks.append(('AppArmor profile present', Path(f'/etc/apparmor.d/{plan.app.appid}').exists(), f'/etc/apparmor.d/{plan.app.appid}'))
    smoke_ok, smoke_detail = smoke_test(binary); checks.append(('smoke test', smoke_ok, smoke_detail))
    return checks

def shutil_which(command: str) -> str | None:
    import shutil
    return shutil.which(command)
