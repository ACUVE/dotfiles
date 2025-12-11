from .typer import main
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = ["main", "__version__"]
