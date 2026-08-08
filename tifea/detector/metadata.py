import json
import re
import tarfile
from typing import Any
from .asar import parse_asar_header, walk_asar_files, read_asar_file

def parse_update_yml(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if ':' in line and not line.lstrip().startswith('#'):
            key, value = line.split(':', 1); result[key.strip()] = value.strip().strip('"\'')
    return result

def package_metadata(tar: tarfile.TarFile, entry: str | None) -> dict[str, Any]:
    if not entry:
        return {}
    try:
        if ':' in entry and '.asar:' in entry:
            asar_member_name, internal_path = entry.split(':', 1)
            asar_member = tar.getmember(asar_member_name)
            with tar.extractfile(asar_member) as stream:
                header, base_offset = parse_asar_header(stream)
                files = dict(walk_asar_files(header.get('files', {})))
                if internal_path in files:
                    b = read_asar_file(stream, base_offset, files[internal_path])
                    if b:
                        return json.loads(b.decode('utf-8'))
            return {}
        member = tar.extractfile(entry)
        return json.loads(member.read().decode('utf-8')) if member else {}
    except (OSError, ValueError, json.JSONDecodeError, KeyError):
        return {}

def app_id(value: str) -> str:
    return re.sub(r'(^-|-$)', '', re.sub(r'[^a-z0-9]+', '-', value.lower())) or 'electron-app'
