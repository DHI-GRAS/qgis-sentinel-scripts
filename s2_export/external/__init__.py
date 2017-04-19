import sys
import os

def _append_relative_path(path):
    sys.path.append(os.path.join(
        os.path.dirname(os.path.realpath(__file__)), path))

try:
    import gdal_utils
except ImportError:
    _append_relative_path('gdal_utils')
    import gdal_utils
