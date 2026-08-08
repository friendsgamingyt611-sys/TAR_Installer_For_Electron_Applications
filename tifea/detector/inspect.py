from pathlib import Path
import tarfile
import re
from .fingerprint import source_root
from .icon import find_icon, find_icon_in_asar, icon_sha256
from .metadata import app_id, package_metadata
from ..model import AppInfo

def inspect_archive(archive: str | Path) -> AppInfo:
    path = Path(archive).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {path} (current directory: {Path.cwd()})')
    with tarfile.open(path, 'r:*') as tar:
        names = [m.name for m in tar.getmembers()]
        root = source_root(names); prefix = f'{root}/' if root else ''
        package = next((n for n in names if n.endswith('resources/app/package.json')), None)
        asar_member = next((n for n in names if n.endswith('resources/app.asar')), None)
        if package is None and asar_member is not None:
            package = f"{asar_member}:package.json"

        metadata = package_metadata(tar, package)
        fallback_name = re.sub(r'\.(tar\.gz|tgz|tar\.xz|tar\.bz2|tar)$', '', path.name, flags=re.IGNORECASE)
        display = str(metadata.get('productName') or metadata.get('name') or fallback_name)
        ident = app_id(str(metadata.get('name') or display))
        candidates = [f'{prefix}{x}' for x in (metadata.get('name'), ident, 'electron') if x]
        executable = next((x for x in candidates if x in names), None)
        if executable is None:
            files = [member for member in tar.getmembers() if member.isfile() and member.name.startswith(prefix)]
            preferred = {ident, str(metadata.get('name', '')).lower(), 'electron'}
            executable = next((member.name for member in files if member.name[len(prefix):].lower() in preferred and member.mode & 0o111), None)
            if executable is None:
                executable = next((member.name for member in files if '/' not in member.name[len(prefix):] and member.mode & 0o111 and Path(member.name).suffix == '' and not any(word in member.name.lower() for word in ('license', 'readme', 'notice', 'version'))), None)
        if not executable: raise ValueError('could not identify an application executable')
        sandbox = next((n for n in names if n.endswith('chrome-sandbox')), None)

        icon_path = find_icon(names, prefix)
        icon_rel: str | None = None
        icon_hash: str | None = None
        icon_target: str | None = None

        if icon_path:
            icon_rel = icon_path[len(prefix):]
            icon_hash = icon_sha256(tar, icon_path)
            icon_target = icon_path
        elif asar_member:
            asar_obj = tar.getmember(asar_member)
            stream = tar.extractfile(asar_obj)
            if stream:
                res = find_icon_in_asar(stream, asar_member)
                if res:
                    target_spec, dst_filename, _, sha256_hash = res
                    icon_rel = dst_filename
                    icon_hash = sha256_hash
                    icon_target = target_spec

        return AppInfo(
            ident,
            display,
            str(metadata.get('version', 'unknown')),
            path,
            root,
            executable[len(prefix):],
            sandbox[len(prefix):] if sandbox else None,
            icon_rel,
            icon_hash,
            path.stat().st_size,
            icon_target,
        )
