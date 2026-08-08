from typing import Any
from ..model import InstallPlan

def show_plan(plan: InstallPlan) -> None:
    print(f'\nDetected: Electron application ("{plan.app.display_name}")')
    print(f'Version: {plan.app.version_hint}\nDistro: {plan.distro.name} ({plan.distro.family.value})')
    print('\nPlanned actions:')
    print(f'  icon: {plan.app.icon or "not detected"}')
    for index, action in enumerate(plan.actions, 1): print(f'  {index}. {action.type}' + (f' {action.path}' if action.path else ''))

def show_checks(checks: list[tuple[str, bool, str]]) -> None:
    for label, passed, detail in checks: print(f"{'✓' if passed else '✗'} {label}: {detail}")

def show_comparison(comparison: Any) -> None:
    print(f'\nCheck: {comparison.app.display_name}')
    print(f'  system path: {comparison.system_path}')
    show_checks(comparison.checks)
    if comparison.issues:
        print('\nIssues:')
        for issue in comparison.issues: print(f'  ✗ {issue.label}: {issue.detail}' + (' [fixable]' if issue.fixable else ' [manual]'))
    else:
        print('\n✓ System installation matches the tarball.')

def message(text: str) -> None:
    print(text)

def show_installs(names: list[str]) -> None:
    for name in names: print(name)

class Progress:
    frames = ('⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏')

    def __init__(self, actions: list[Any]) -> None:
        self.actions = actions
        self.index = 0
        self.frame = 0

    def __call__(self, action: Any, state: str) -> None:
        if state == 'start':
            self.index += 1
            label = action.type.replace('_', ' ')
            detail = action.path or action.dst or action.target or ''
            print(f'  [{self.index}/{len(self.actions)}] {self.frames[self.frame]} {label} {detail}', end='', flush=True)
            self.frame = (self.frame + 1) % len(self.frames)
        else:
            print('\r' + (' ' * 100) + '\r', end='')
            label = action.type.replace('_', ' ')
            detail = action.path or action.dst or action.target or ''
            print(f'  [{self.index}/{len(self.actions)}] ✓ {label} {detail}')

def show_error_info(plan: InstallPlan, manifest_path: str, *, error: Exception | None = None, checks: list[tuple[str, bool, str]] | None = None, traceback_text: str | None = None, manifest: Any = None) -> None:
    print('\nError Info:')
    print(f'  archive: {plan.app.archive}')
    print(f'  appid: {plan.app.appid}')
    print(f'  version: {plan.app.version_hint}')
    print(f'  distro: {plan.distro.name} ({plan.distro.family.value})')
    print(f'  sandbox strategy: {plan.strategy.value}')
    print(f'  install root: {plan.versioned_root}')
    print(f'  executable: {plan.versioned_root / plan.app.executable}')
    print(f'  manifest: {manifest_path}')
    actions = manifest.actions if manifest is not None else plan.actions
    completed = [a.type for a in actions if a.done]
    pending = [a.type for a in actions if not a.done]
    print(f'  completed actions: {", ".join(completed) or "none"}')
    print(f'  pending action: {manifest.current_action if manifest is not None and manifest.current_action else pending[0] if pending else "none"}')
    if error:
        print(f'  exception: {type(error).__name__}: {error}')
    if checks:
        for label, passed, detail in checks:
            if not passed: print(f'  failed check: {label}: {detail}')
    if traceback_text:
        print('  traceback:')
        for line in traceback_text.rstrip().splitlines(): print(f'    {line}')
