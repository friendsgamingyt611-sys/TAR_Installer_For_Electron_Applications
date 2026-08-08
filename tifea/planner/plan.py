from datetime import datetime, timezone
from pathlib import Path
from ..model import Action, AppInfo, Distro, InstallPlan, SandboxStrategy, Family
from .actions import action
from .templates.apparmor_profile import render as render_apparmor
from .templates.desktop_entry import render as render_desktop

def build_plan(app: AppInfo, distro: Distro, strategy: SandboxStrategy) -> InstallPlan:
    root = Path('/opt') / f'{app.appid}-{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}'
    actions = [action('mkdir', path=str(root)), action('copy_tree', src=str(app.archive), dst=str(root)), action('symlink', path=f'/opt/{app.appid}', target=str(root))]
    if app.icon and app.icon_target:
        actions.append(action('copy_icon', src=str(app.archive), dst=str(root / app.icon), target=app.icon_target))
    if app.chrome_sandbox and strategy is SandboxStrategy.SETUID:
        sandbox = root / app.chrome_sandbox
        actions += [action('chmod', path=str(sandbox), mode='4755'), action('chown', path=str(sandbox), owner='root:root')]
    if app.chrome_sandbox and strategy is SandboxStrategy.APPARMOR:
        actions.append(action('write_apparmor_profile', path=f'/etc/apparmor.d/{app.appid}', content=render_apparmor(app, str(root))))
    actions += [
        action('write_file', path=f'/usr/share/applications/{app.appid}.desktop', content=render_desktop(app, strategy)),
        action('symlink', path=f'/usr/local/bin/{app.appid}', target=f'/opt/{app.appid}/{app.executable}'),
        action('xdg_mime_default', path=f'/usr/share/applications/{app.appid}.desktop'),
    ]
    if distro.family is Family.REDHAT:
        actions.append(action('restorecon', path=str(root)))
    actions += [action('desktop_db_refresh'), action('icon_cache_refresh')]
    return InstallPlan(app, distro, root, strategy, actions)
