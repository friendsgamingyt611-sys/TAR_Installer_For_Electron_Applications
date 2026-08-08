import os
import subprocess
from collections.abc import Sequence

def ensure_sudo() -> None:
    if os.geteuid() != 0:
        subprocess.run(['sudo', '-v'], check=True)

def run_privileged(args: Sequence[str]) -> None:
    command = list(args) if os.geteuid() == 0 else ['sudo', *args]
    subprocess.run(command, check=True)
