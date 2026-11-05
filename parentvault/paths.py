"""Resolve bundled assets separately from writable local application data."""
import os
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parents[1]


def data_directory():
    """A copied app keeps records across source updates; tests can override it."""
    override = os.environ.get('PARENTVAULT_DATA_DIR')
    base = Path(override) if override else Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ParentVault'
    base.mkdir(parents=True, exist_ok=True)
    return base
