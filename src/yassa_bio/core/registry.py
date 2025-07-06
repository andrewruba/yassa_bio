_registry: dict[tuple[str, str], object] = {}


def register(kind: str, name: str):
    """Decorator: register a plug-in under (kind, name)."""

    def decorator(func_or_cls):
        key = (kind.lower(), name.lower())
        if key in _registry:
            raise KeyError(f"{key} already registered")
        _registry[key] = func_or_cls
        return func_or_cls

    return decorator


def get(kind: str, name: str):
    try:
        return _registry[(kind.lower(), name.lower())]
    except KeyError:
        avail = [k[1] for k in _registry if k[0] == kind.lower()]
        raise KeyError(
            f"No plug-in for ({kind!r}, {name!r}). "
            f"Available: {', '.join(avail) or 'none.'}"
        ) from None
