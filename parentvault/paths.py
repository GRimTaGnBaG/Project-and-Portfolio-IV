"""Resolve bundled assets separately from writable local application data."""
# Load os for use in this module.
import os
# Bring in Path from pathlib.
from pathlib import Path

# Keep 1 field as asset root.
ASSET_ROOT = Path(__file__).resolve().parents[1]


def data_directory():
    """A copied app keeps records across source updates; tests can override it."""
    # Set override from get.
    override = os.environ.get('PARENTVAULT_DATA_DIR')
    # Choose base based on whether override is present or true.
    base = Path(override) if override else Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ParentVault'
    # Create the output directory before writing files into it.
    base.mkdir(parents=True, exist_ok=True)
    # Return base to the caller.
    return base
