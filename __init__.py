import os
from typing import Dict, Any
from utils import Config

# Load configuration on import
config: Dict[str, Any] = Config.load_env()

# Package metadata
__version__ = "1.0.0"
__author__ = "ergonomech"
__license__ = "MIT"

# Set up package-level variables
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PACKAGE_DIR, 'assets')

# Export version info
__all__ = [
    '__version__',
    '__author__',
    '__license__',
    'config',
    'PACKAGE_DIR',
    'ASSETS_DIR'
]