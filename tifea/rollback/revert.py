import os
import subprocess
from pathlib import Path
from ..executor.manifest import Manifest, atomic_write, load_manifest
from ..executor.privileged import run_privileged

def rollback(manifest: Manifest) -> None:
    for action in reversed(manifest.actions):
        if not action.done: continue
        try:
            if action.type in {'symlink', 'mkdir', 'copy_tree'}:
                target = action.path or action.dst
                if target and os.path.lexists(target): run_privileged(['rm', '-rf', target])
            elif action.type in {'write_file', 'write_apparmor_profile'}:
                if action.type == 'write_apparmor_profile' and action.path:
                    subprocess.run(['sudo', 'apparmor_parser', '-R', action.path], check=False)
                if action.path and os.path.lexists(action.path): run_privileged(['rm', '-f', action.path])
            elif action.type == 'chmod' and action.path and action.previous_mode:
                run_privileged(['chmod', action.previous_mode, action.path])
            elif action.type == 'chown' and action.path and action.previous_owner:
                run_privileged(['chown', action.previous_owner, action.path])
            if action.backup and os.path.lexists(action.backup): run_privileged(['mv', action.backup, action.path])
        except (OSError, subprocess.CalledProcessError):
            continue
    manifest.status = 'rolled_back'; atomic_write(manifest)

def uninstall(appid: str) -> None:
    manifest = load_manifest(appid); rollback(manifest); manifest.status = 'uninstalled'; atomic_write(manifest)
