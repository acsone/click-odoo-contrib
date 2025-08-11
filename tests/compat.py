import sys

from packaging.version import Version

from click.testing import CliRunner as ClickCliRunner

if sys.version_info < (3, 8):
    from importlib_metadata import version  # type: ignore[import]
else:
    from importlib.metadata import version


def CliRunner():
    if Version(version("click")) < Version("8.2"):
        # Remove this with dropping Python 3.9 support because click 8.2 is
        # python 3.10+ only
        return ClickCliRunner(mix_stderr=False)  # Avoid mixing stderr with stdout
    return ClickCliRunner()
