import argparse
import json
import traceback
from dataclasses import replace
from pathlib import Path
from .detector import inspect_archive
from .distro import detect
from .distro.confinement import choose_strategy
from .executor import execute
from .executor.manifest import adopt_manifest, atomic_write, load_manifest, manifest_path
from .planner import build_plan
from .planner.fix import build_fix_actions
from .rollback import rollback, uninstall
from .ui import choose_strategy as prompt_strategy
from .ui import Progress, confirm, duplicate_action, message, renamed_id, show_checks, show_comparison, show_error_info, show_installs, show_plan
from .verifier.compare import compare
from .model import InstallPlan, SandboxStrategy
from .verifier import verify

def _display_name_in_use(name: str, excluding: str | None = None) -> bool:
    for base in [Path.home() / '.local/share/tifea', Path.home() / '.local/share/targz-installer']:
        for manifest_path_value in base.glob('*/manifest.json') if base.exists() else []:
            if excluding and manifest_path_value.parent.name == excluding:
                continue
            try:
                if json.loads(manifest_path_value.read_text()).get('display_name', '').casefold() == name.casefold():
                    return True
            except (OSError, json.JSONDecodeError):
                continue
    return False


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='tifea', description='Install prebuilt Electron tarballs safely', add_help=False)
    p.add_argument('-h', '--help', '-help', action='help', help='show this help message and exit')
    sub = p.add_subparsers(dest='command', required=True)
    install = sub.add_parser('install'); install.add_argument('archive', nargs='+'); install.add_argument('--dry-run', action='store_true'); install.add_argument('--yes', action='store_true'); install.add_argument('--sandbox', choices=['apparmor', 'setuid', 'no-sandbox'])
    reinstall = sub.add_parser('reinstall'); reinstall.add_argument('archive', nargs='+'); reinstall.add_argument('--dry-run', action='store_true'); reinstall.add_argument('--yes', action='store_true'); reinstall.add_argument('--sandbox', choices=['apparmor', 'setuid', 'no-sandbox'])
    check = sub.add_parser('check'); check.add_argument('system_path'); check.add_argument('archive')
    fix = sub.add_parser('fix'); fix.add_argument('system_path'); fix.add_argument('archive'); fix.add_argument('--yes', action='store_true')
    sub.add_parser('list'); remove = sub.add_parser('uninstall'); remove.add_argument('appid')
    return p

def install_command(args) -> int:
    archive = ' '.join(args.archive)
    app = inspect_archive(archive); distro = detect()
    existing = manifest_path(app.appid).exists() or Path(f'/opt/{app.appid}').exists()
    replace_existing = False
    if existing and args.command == 'install':
        choice = duplicate_action(app.display_name, args.yes)
        if choice == 'cancel': return 0
        if choice == 'reinstall':
            if manifest_path(app.appid).exists():
                replace_existing = True
            else: raise RuntimeError(f'{app.display_name} exists at /opt/{app.appid}, but has no TIFEA manifest')
        else:
            renamed = renamed_id(app.appid, app.display_name)
            if not renamed: return 0
            new_id, new_name = renamed
            if manifest_path(new_id).exists() or Path(f'/opt/{new_id}').exists():
                raise RuntimeError(f'the renamed application ID is already in use: {new_id}')
            if _display_name_in_use(new_name, excluding=app.appid):
                raise RuntimeError(f'the renamed application name is already in use: {new_name}')
            app = replace(app, appid=new_id, display_name=new_name)
            if not confirm(f'Use application name "{new_name}" with command "{new_id}"?', args.yes): return 0
    elif existing and args.command == 'reinstall':
        if manifest_path(app.appid).exists():
            replace_existing = True
        else: raise RuntimeError(f'{app.display_name} exists at /opt/{app.appid}, but has no TIFEA manifest')
    strategy = choose_strategy(distro, args.sandbox) if (args.yes or args.dry_run) else prompt_strategy(distro, args.sandbox) if app.chrome_sandbox else choose_strategy(distro, args.sandbox)
    if strategy is None: raise RuntimeError('could not select sandbox strategy')
    plan = build_plan(app, distro, strategy); show_plan(plan)
    if args.dry_run: return 0
    if not confirm('Execute this exact plan?', args.yes): return 0
    if replace_existing:
        uninstall(app.appid)
    message(f'Manifest: {manifest_path(app.appid)}')
    message('Executing manifest actions:')
    try:
        manifest = execute(plan, on_action=Progress(plan.actions))
    except Exception as error:
        try:
            manifest = load_manifest(app.appid)
            manifest.error_info = {'exception': str(error), 'type': type(error).__name__, 'traceback': traceback.format_exc()}
            atomic_write(manifest)
        except Exception:
            manifest = None
        show_error_info(plan, str(manifest_path(app.appid)), error=error, traceback_text=traceback.format_exc(), manifest=manifest)
        if manifest:
            rollback(manifest)
        message('Installation was rolled back.')
        return 1
    checks = verify(plan); show_checks(checks)
    if not all(ok for _, ok, _ in checks):
        failed = [f'{label}: {detail}' for label, ok, detail in checks if not ok]
        manifest.error_info = {'failed_checks': failed}
        atomic_write(manifest)
        show_error_info(plan, str(manifest_path(app.appid)), checks=checks)
        rollback(manifest)
        message('Installation was rolled back.')
        if distro.family.value == 'redhat' and strategy.value == 'setuid':
            message('Fedora/RHEL setuid sandbox verification failed. Retry with: --sandbox no-sandbox')
        return 1
    message(f'\n{app.display_name} installed successfully. Run: {app.appid}'); return 0

def main() -> None:
    args = parser().parse_args()
    try:
        if args.command in {'install', 'reinstall'}: code = install_command(args)
        elif args.command == 'check':
            result = compare(args.system_path, args.archive); show_comparison(result); code = 1 if result.issues else 0
        elif args.command == 'fix':
            result = compare(args.system_path, args.archive); show_comparison(result)
            if any(issue.key == 'system_path' for issue in result.issues):
                message(f'Cannot fix: system application path does not exist: {result.system_path}')
                message('No manifest was created and no files were changed.')
                code = 1
                continue_fix = False
            else:
                continue_fix = True
            fix_cancelled = False
            if continue_fix and result.manifest is None:
                proceed = confirm('No TIFEA manifest exists. Generate a baseline manifest from this existing installation?', args.yes)
                if not proceed:
                    message('Fix cancelled; no manifest was created.')
                    code = 0
                    fix_cancelled = True
                    actions = []
                else:
                    message('Generating baseline manifest. This records the current state; it cannot reconstruct old backups.')
                    desktop_path = Path('/usr/share/applications') / f'{result.app.appid}.desktop'
                    desktop_text = desktop_path.read_text(errors='replace') if desktop_path.is_file() else ''
                    strategy = SandboxStrategy.NO_SANDBOX if '--no-sandbox' in desktop_text else choose_strategy(detect())
                    result = replace(result, manifest=adopt_manifest(result.app, detect(), result.system_path, strategy))
                    actions = build_fix_actions(result)
            elif continue_fix:
                actions = build_fix_actions(result)
            else:
                actions = []
            if fix_cancelled:
                pass
            elif not actions:
                code = 0 if not result.issues else 1
            elif not confirm(f'Apply {len(actions)} necessary repair action(s)?', args.yes):
                code = 0
            else:
                app = result.app
                manifest = result.manifest
                if manifest is None: raise RuntimeError('cannot repair an installation without a TIFEA manifest')
                distro = detect()
                plan = InstallPlan(app, distro, result.system_path.resolve(), SandboxStrategy(manifest.sandbox_strategy), actions)
                execute(plan, on_action=Progress(actions), manifest=manifest, actions=actions); repaired = compare(args.system_path, args.archive); show_comparison(repaired); code = 1 if repaired.issues else 0
        elif args.command == 'uninstall': uninstall(args.appid); message(f'Uninstalled {args.appid}.'); code = 0
        else:
            rows = []
            for base in [Path.home() / '.local/share/tifea', Path.home() / '.local/share/targz-installer']:
                if base.exists():
                    rows.extend(base.glob('*/manifest.json'))
            show_installs(sorted(list({row.parent.name for row in rows})))
            code = 0

    except Exception as error:
        message(f'Error: {error}'); code = 1
    raise SystemExit(code)
