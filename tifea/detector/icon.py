import tarfile
import hashlib
from pathlib import PurePosixPath
from typing import BinaryIO
from .asar import parse_asar_header, walk_asar_files, read_asar_file

EXCLUDED_DIR_PATTERNS = ('/extensions/', '/node_modules/', '/out/vs/', '/vendor/', '/dist/media/')

def is_excluded_path(path: str) -> bool:
    lower = path.lower()
    return any(pattern in lower for pattern in EXCLUDED_DIR_PATTERNS)

def rank_icon_path(name: str) -> tuple[int, int, int, int]:
    lower = name.lower()
    suffix = PurePosixPath(name).suffix.lower()
    stem = PurePosixPath(name).stem.lower()

    # 1. Format priority (PNG/SVG preferred on Linux)
    fmt_score = 0 if suffix in ('.png', '.svg') else (1 if suffix == '.xpm' else 2)

    # 2. Location priority
    if any(loc in lower for loc in ('/linux/', '/build/', '/assets/', '/static/', '/icons/', '/pixmaps/')):
        loc_score = 0
    elif '/resources/' in lower:
        loc_score = 1
    else:
        loc_score = 2

    # 3. Name priority
    if stem in ('icon', 'logo', 'app', 'code'):
        name_score = 0
    elif any(token in stem for token in ('icon', 'logo', 'app', 'code')):
        name_score = 1
    else:
        name_score = 2

    # 4. Path length
    return fmt_score, loc_score, name_score, len(name)

def find_icon(names: list[str], root: str) -> str | None:
    prefix = f"{root}/" if root else ""
    candidates = [
        n for n in names
        if n.startswith(prefix)
        and PurePosixPath(n).suffix.lower() in {'.png', '.svg', '.xpm', '.ico', '.icns'}
        and not is_excluded_path(n)
    ]
    return min(candidates, key=rank_icon_path, default=None)

def find_icon_in_asar(asar_stream: BinaryIO, asar_member_name: str) -> tuple[str, str, bytes, str] | None:
    """Find and return best icon candidate inside an ASAR stream.
    Returns (target_spec, dst_icon_filename, icon_bytes, sha256_hash) or None.
    target_spec format: 'asar_member_name:internal_path'
    """
    try:
        header, base_offset = parse_asar_header(asar_stream)
        files = list(walk_asar_files(header.get('files', {})))
        candidates = [
            (path, info) for path, info in files
            if PurePosixPath(path).suffix.lower() in {'.png', '.svg', '.xpm', '.ico', '.icns'}
            and not is_excluded_path(path)
            and not info.get('unpacked')
        ]
        if not candidates:
            return None
        best_path, best_info = min(candidates, key=lambda c: rank_icon_path(c[0]))
        icon_bytes = read_asar_file(asar_stream, base_offset, best_info)
        if not icon_bytes:
            return None
        target_spec = f"{asar_member_name}:{best_path}"
        dst_filename = PurePosixPath(best_path).name
        sha256_hash = hashlib.sha256(icon_bytes).hexdigest()
        return target_spec, dst_filename, icon_bytes, sha256_hash
    except Exception:
        return None

def extract_icon(tar: tarfile.TarFile, member_name: str, destination: str) -> None:
    if ':' in member_name and '.asar:' in member_name:
        asar_member_name, internal_path = member_name.split(':', 1)
        asar_member = tar.getmember(asar_member_name)
        with tar.extractfile(asar_member) as stream:
            header, base_offset = parse_asar_header(stream)
            files = dict(walk_asar_files(header.get('files', {})))
            if internal_path not in files:
                raise ValueError(f"icon {internal_path} not found in ASAR {asar_member_name}")
            icon_bytes = read_asar_file(stream, base_offset, files[internal_path])
            if not icon_bytes:
                raise ValueError(f"icon {internal_path} in ASAR is empty or unpacked")
            with open(destination, 'wb') as target:
                target.write(icon_bytes)
        return

    member = tar.getmember(member_name)
    if not member.isfile():
        raise ValueError('icon entry is not a regular file')
    with tar.extractfile(member) as source, open(destination, 'wb') as target:
        target.write(source.read())

def icon_sha256(tar: tarfile.TarFile, member_name: str | None) -> str | None:
    if not member_name:
        return None
    if ':' in member_name and '.asar:' in member_name:
        asar_member_name, internal_path = member_name.split(':', 1)
        try:
            asar_member = tar.getmember(asar_member_name)
            with tar.extractfile(asar_member) as stream:
                header, base_offset = parse_asar_header(stream)
                files = dict(walk_asar_files(header.get('files', {})))
                if internal_path in files:
                    b = read_asar_file(stream, base_offset, files[internal_path])
                    if b:
                        return hashlib.sha256(b).hexdigest()
        except Exception:
            return None
        return None
    try:
        member = tar.getmember(member_name)
        source = tar.extractfile(member)
        if source is None:
            return None
        return hashlib.sha256(source.read()).hexdigest()
    except (KeyError, OSError):
        return None
