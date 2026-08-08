import os
import shutil
import subprocess
import tarfile
import tempfile
import traceback
from collections.abc import Callable
from pathlib import Path
from .manifest import Manifest, atomic_write, new_manifest
from .privileged import ensure_sudo, run_privileged
from ..detector.icon import extract_icon
from ..model import Action, InstallPlan

def _exists(path: str) -> bool:
    return os.path.lexists(path)

def _extract_safe(archive: tarfile.TarFile, destination: str) -> None:
    base = Path(destination).resolve()
    for member in archive.getmembers():
        if member.issym() or member.islnk():
            raise ValueError(f'archive links are not supported: {member.name}')
        target = (base / member.name).resolve()
        if target != base and base not in target.parents:
            raise ValueError(f'unsafe archive path: {member.name}')
        archive.extract(member, destination)

def _backup(a: Action) -> None:
    if a.path and _exists(a.path):
        a.backup = f'{a.path}.tifea-backup'
        run_privileged(['mv', a.path, a.backup])

def _run_action(a: Action, plan: InstallPlan) -> None:
    if a.type == 'mkdir': run_privileged(['mkdir', '-p', a.path])
    elif a.type == 'copy_tree':
        with tempfile.TemporaryDirectory(prefix='tifea-') as tmp:
            with tarfile.open(a.src, 'r:*') as archive: _extract_safe(archive, tmp)
            source = Path(tmp) / plan.app.source_root if plan.app.source_root else Path(tmp)
            run_privileged(['cp', '-a', f'{source}/.', a.dst])
    elif a.type == 'copy_icon':
        with tempfile.TemporaryDirectory(prefix='tifea-icon-') as tmp:
            temporary = Path(tmp) / Path(a.dst).name
            with tarfile.open(a.src, 'r:*') as archive:
                target = a.target or (f"{plan.app.source_root}/{plan.app.icon}" if plan.app.source_root and plan.app.icon else plan.app.icon)
                if not target:
                    raise ValueError(f'icon target missing for {a.dst}')
                extract_icon(archive, target, str(temporary))
            run_privileged(['install', '-D', '-m', '0644', str(temporary), a.dst])
    elif a.type == 'symlink':
        _backup(a); run_privileged(['ln', '-s', a.target, a.path])
    elif a.type == 'chmod':
        a.previous_mode = oct(os.stat(a.path).st_mode & 0o7777)[2:]; run_privileged(['chmod', a.mode, a.path])
    elif a.type == 'chown':
        a.previous_owner = subprocess.check_output(['stat', '-c', '%U:%G', a.path], text=True).strip(); run_privileged(['chown', a.owner, a.path])
    elif a.type in {'write_file', 'write_apparmor_profile'}:
        _backup(a)
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.write(a.content or ''); temporary = temp.name
        try:
            run_privileged(['install', '-D', '-m', '0644', temporary, a.path])
            if a.type == 'write_apparmor_profile': run_privileged(['apparmor_parser', '-r', a.path])
        finally: os.unlink(temporary)
    elif a.type == 'restorecon':
        command = list(['restorecon', '-Rv', a.path]) if os.geteuid() == 0 else ['sudo', 'restorecon', '-Rv', a.path]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    elif a.type == 'desktop_db_refresh':
        command = shutil.which('update-desktop-database')
        if command: subprocess.run([command, str(Path.home() / '.local/share/applications')], check=False)
    elif a.type == 'icon_cache_refresh':
        return
    elif a.type == 'xdg_mime_default':
        for mime in ('x-scheme-handler/http', 'x-scheme-handler/https', 'text/html'):
            subprocess.run(['xdg-mime', 'default', Path(a.path).name, mime], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

def execute(plan: InstallPlan, on_action: Callable[[Action, str], None] | None = None, manifest: Manifest | None = None, actions: list[Action] | None = None) -> Manifest:
    manifest = manifest or new_manifest(plan)
    if actions is not None:
        manifest.actions.extend(actions)
    atomic_write(manifest); ensure_sudo()
    try:
        for action in actions or manifest.actions:
            manifest.current_action = action.type
            atomic_write(manifest)
            if on_action: on_action(action, 'start')
            _run_action(action, plan)
            action.done = True
            atomic_write(manifest)
            if on_action: on_action(action, 'done')
        manifest.current_action = None; manifest.status = 'installed'; atomic_write(manifest); return manifest
    except Exception as error:
        manifest.status = 'failed'
        manifest.error_info = {'exception': str(error), 'type': type(error).__name__, 'traceback': traceback.format_exc()}
        atomic_write(manifest)
        raise
