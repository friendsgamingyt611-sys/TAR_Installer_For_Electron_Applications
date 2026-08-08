from pathlib import Path
from ...model import AppInfo, SandboxStrategy

def render(app: AppInfo, strategy: SandboxStrategy) -> str:
    executable = f'/opt/{app.appid}/{app.executable}'
    flag = ' --no-sandbox' if strategy is SandboxStrategy.NO_SANDBOX else ''
    icon = f'/opt/{app.appid}/{app.icon}' if app.icon else ''
    icon_line = f'Icon={icon}\n' if icon else ''
    return f'[Desktop Entry]\nName={app.display_name}\nComment=Installed by TIFEA\nExec={executable}{flag} %U\n{icon_line}Terminal=false\nType=Application\nCategories=Utility;\nMimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;\n'
