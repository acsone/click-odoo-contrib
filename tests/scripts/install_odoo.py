#!/usr/bin/env python
import os
import subprocess
import sys

odoo_branch = sys.argv[1]
odoo_dir = sys.argv[2]


def odoo_installed():
    try:
        import odoo  # noqa

        return True
    except ImportError:
        # odoo < 10
        try:
            import openerp  # noqa

            return True
        except ImportError:
            # odoo not installed
            return False


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
    if "PGHOST" in os.environ and odoo_branch == "8.0":
        # Patch postgres connection mechanism to support connection with PGHOST
        # environment variable. This patch is a backport from 9.0.
        patch_path = os.path.join(os.path.dirname(__file__), "sql_db-8.patch")
        subprocess.check_call(["patch", "-p1", "-i", patch_path], cwd=odoo_dir)


def install_odoo():
    if odoo_branch in ["8.0", "9.0", "10.0", "11.0", "12.0", "13.0"]:
        # setuptools 58 dropped support for 2to3, which is required
        # for dependencies of older Odoo versions
        subprocess.check_call(
            [
                "pip",
                "install",
                "setuptools<58",
            ]
        )
    subprocess.check_call(
        [
            "pip",
            "install",
            "--no-binary",
            "psycopg2",
            "-r",
            "https://raw.githubusercontent.com/OCA/OCB/{}/requirements.txt".format(
                odoo_branch
            ),
        ]
    )
    subprocess.check_call(["pip", "install", "-e", odoo_dir])


def main():
    if not odoo_installed():
        if not odoo_cloned():
            clone_odoo()
        install_odoo()


if __name__ == "__main__":
    main()
