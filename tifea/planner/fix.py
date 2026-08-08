from pathlib import Path
from ..model import Action, AppInfo
from ..verifier.compare import Comparison
from .templates.desktop_entry import render

def build_fix_actions(comparison: Comparison) -> list[Action]:
    app = comparison.app; root = comparison.system_path.resolve(); actions: list[Action] = []
    keys = {issue.key for issue in comparison.issues}
    if 'icon' in keys and app.icon:
        member = f'{app.source_root}/{app.icon}' if app.source_root else app.icon
        actions.append(Action('copy_icon', src=str(app.archive), dst=str(root / app.icon), target=member))
    if 'desktop' in keys:
        strategy = comparison.manifest.sandbox_strategy if comparison.manifest else 'no-sandbox'
        from ..model import SandboxStrategy
        actions.append(Action('write_file', path=f'/usr/share/applications/{app.appid}.desktop', content=render(app, SandboxStrategy(strategy))))
    if 'xdg' in keys:
        actions.append(Action('xdg_mime_default', path=f'/usr/share/applications/{app.appid}.desktop'))
    if 'selinux' in keys:
        actions.append(Action('restorecon', path=str(root)))
    return actions
