"""JSON Registry Manager."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("json-registry-manager")
except PackageNotFoundError:  # source tree without an installed package
    __version__ = "0.2.0"
