"""Read settings from a local .env file, for running the service on a developer's machine.

A hosting provider sets environment variables itself and has no .env file, so this does
nothing there. A variable that is already set is never replaced. The file is listed in
.gitignore: it holds API keys and must not be committed.
"""

import os
from pathlib import Path

DEFAULT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def load_env_file(path: Path = DEFAULT_ENV_FILE) -> list[str]:
    """Set each NAME=value line of the file that is not already set. Returns the names set."""
    if not path.is_file():
        return []
    loaded = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if name and value and name not in os.environ:
            os.environ[name] = value
            loaded.append(name)
    return loaded
