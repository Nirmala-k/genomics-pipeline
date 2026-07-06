import os
import subprocess
from typing import List, Optional


def mkdirs(*paths: str) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)


def run(cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
    """Thin wrapper so every stage logs exactly what it's executing."""
    print(f"[run] {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def fetch(url: str, dest: str, post_cmd: Optional[List[str]] = None) -> None:
    if os.path.exists(dest):
        print(f"[skip] {dest} already exists")
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"[download] {url} -> {dest}")
    run(["wget", "-q", "-O", dest, url])
    if post_cmd:
        run(post_cmd)
