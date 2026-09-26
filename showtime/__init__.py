"""Common module information"""

from importlib.metadata import version, PackageNotFoundError

__version__ = 'unknown'
__url__ = 'https://github.com/aquilax/showtime'

try:
    __version__ = version("your_package_name")
except PackageNotFoundError:
    pass

