import importlib.metadata

try:
    _detected_version = importlib.metadata.version("code-puppy-cn")
    # Ensure we never end up with None or empty string
    __version__ = _detected_version if _detected_version else "0.0.0-dev"
except Exception:
    try:
        __version__ = importlib.metadata.version("code-puppy")
    except Exception:
        # Fallback for source checkouts without installed package metadata.
        __version__ = "0.0.0-dev"
