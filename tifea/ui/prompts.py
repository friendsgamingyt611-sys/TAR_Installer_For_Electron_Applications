from ..model import Distro, SandboxStrategy
from pathlib import Path
import re

def confirm(message: str, assume_yes: bool = False) -> bool:
    return assume_yes or input(f'{message} [y/N] ').strip().lower() in {'y', 'yes'}

def choose_strategy(distro: Distro, requested: str | None = None) -> SandboxStrategy:
    if requested: return SandboxStrategy(requested)
    if distro.family.value == 'debian' and distro.apparmor_restricted:
        print('Sandbox strategy:\n  [1] AppArmor profile (recommended)\n  [2] setuid chrome-sandbox\n  [3] --no-sandbox')
        choice = input('Choice [1]: ').strip()
        return {'2': SandboxStrategy.SETUID, '3': SandboxStrategy.NO_SANDBOX}.get(choice, SandboxStrategy.APPARMOR)
    print('Sandbox strategy:\n  [1] setuid chrome-sandbox (recommended)\n  [2] --no-sandbox')
    return SandboxStrategy.NO_SANDBOX if input('Choice [1]: ').strip() == '2' else SandboxStrategy.SETUID

def duplicate_action(display_name: str, assume_yes: bool = False) -> str:
    if assume_yes:
        return 'reinstall'
    print(f'An application named "{display_name}" is already installed.')
    print('  [1] Reinstall the application')
    print('  [2] Rename the application')
    return {'1': 'reinstall', '2': 'rename'}.get(input('Choice [1/2]: ').strip(), 'cancel')

def renamed_id(current_id: str, display_name: str) -> tuple[str, str] | None:
    print('Rename mode:')
    print('  [1] Auto-rename')
    print('  [2] Manual rename')
    mode = input('Choice [1/2]: ').strip()
    if mode == '1':
        index = 2
        while Path(f'/opt/{current_id}-{index}').exists(): index += 1
        return f'{current_id}-{index}', f'{display_name} ({index})'
    if mode == '2':
        value = input('New application name: ').strip()
        ident = re.sub(r'(^-|-$)', '', re.sub(r'[^a-z0-9]+', '-', value.lower()))
        return (ident, value) if ident else None
    return None
