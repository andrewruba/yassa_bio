from pathlib import Path


def as_path(p: str | Path) -> Path:
    """Expand ~, make absolute, and return a Path."""
    return Path(p).expanduser().resolve()
