"""Backward-compatibility alias module for tifea."""
import sys
import tifea as _tifea

sys.modules['targz_installer'] = _tifea
__version__ = _tifea.__version__
