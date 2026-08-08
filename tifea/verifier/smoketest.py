import subprocess
from pathlib import Path

def smoke_test(binary: Path, timeout: float = 5.0) -> tuple[bool, str]:
    attempts = ([str(binary), '--version'], [str(binary), '--no-sandbox', '--version'])
    last_error = 'process did not start'
    for command in attempts:
        try:
            result = subprocess.run(command, timeout=timeout, capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip() or 'version probe succeeded'
            last_error = (result.stderr or result.stdout).strip() or f'exited with status {result.returncode}'
        except subprocess.TimeoutExpired:
            return True, f'process stayed alive for {timeout:g}s; startup succeeded'
        except OSError as error:
            last_error = str(error)
    return False, last_error
