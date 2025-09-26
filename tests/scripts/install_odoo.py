#!/usr/bin/env python
import contextlib
import os
import subprocess
import sys
import tempfile
from urllib.request import urlopen

odoo_branch = sys.argv[1]
odoo_dir = sys.argv[2]


def odoo_installed():
    try:
        import odoo  # noqa
    except ImportError:
        return False
    else:
        return True


def odoo_cloned():
    return os.path.isdir(os.path.join(odoo_dir, ".git"))


def clone_odoo():
    subprocess.check_call(
        [
            "git",
            "clone",
            "--depth=1",
            "-b",
            odoo_branch,
            "https://github.com/odoo/odoo",
            odoo_dir,
        ]
    )


@contextlib.contextmanager
def odoo_requirements(odoo_branch: str):
    """Yield a list of pip install requirements for Odoo dependencies"""
    with urlopen(
        f"https://raw.githubusercontent.com/OCA/OCB/{odoo_branch}/requirements.txt"
    ) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            reqs = response.read()
            # Replace gevent and greenlet with versions that have wheels on PyPI.
            # Remove this when dropping python 3.10 support.
            reqs = reqs.replace(b"gevent==21.8.0", b"gevent==22.10.2")
            reqs = reqs.replace(b"greenlet==1.1.2", b"greenlet==2.0.2")
            tmpfile.write(reqs)
            tmpfile.close()
            try:
                yield ["--no-binary", "psycopg2", "-r", tmpfile.name]
            finally:
                os.unlink(tmpfile.name)


def install_odoo():
    if odoo_branch in ["11.0", "12.0", "13.0"]:
        # setuptools 58 dropped support for 2to3, which is required
        # for dependencies of older Odoo versions
        subprocess.check_call(
            [
                "pip",
                "install",
                "setuptools<58",
            ]
        )
    with odoo_requirements(odoo_branch) as requirements:
        subprocess.check_call(["pip", "install", *requirements])
    odoo_install_cmd = ["pip", "install", "-e", odoo_dir]
    if sys.version_info >= (3, 7):
        odoo_install_cmd.extend(
            ["--use-pep517", "--config-setting=editable_mode=compat"]
        )
    subprocess.check_call(odoo_install_cmd)


def main():
    if not odoo_installed():
        if not odoo_cloned():
            clone_odoo()
        install_odoo()


if __name__ == "__main__":
    main()
