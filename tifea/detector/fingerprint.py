def is_electron(names: list[str]) -> bool:
    return any(name.endswith('chrome-sandbox') for name in names) and any('/resources/' in name and name.endswith('app.asar') or name.endswith('resources/app/package.json') for name in names)

def source_root(names: list[str]) -> str:
    for name in names:
        parts = name.rstrip('/').split('/')
        if 'linux-unpacked' in parts:
            return '/'.join(parts[:parts.index('linux-unpacked') + 1])
    roots = {name.split('/', 1)[0] for name in names if '/' in name}
    return next(iter(roots), '') if len(roots) == 1 else ''
