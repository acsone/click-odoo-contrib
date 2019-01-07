# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name="click-odoo-contrib",
    description="click-odoo scripts collection",
    long_description="\n".join(
        (
            open(os.path.join(here, "README.rst")).read(),
            open(os.path.join(here, "CHANGES.rst")).read(),
        )
    ),
    use_scm_version=True,
    packages=find_packages(),
    setup_requires=["setuptools-scm"],
    install_requires=["click-odoo>=1.3.0"],
    license="LGPLv3+",
    author="ACSONE SA/NV",
    author_email="info@acsone.eu",
    url="http://github.com/acsone/click-odoo-contrib",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: "
        "GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: Odoo",
    ],
    entry_points="""
        [console_scripts]
        click-odoo-uninstall=click_odoo_contrib.uninstall:main
        click-odoo-upgrade=click_odoo_contrib.upgrade:main
        click-odoo-update=click_odoo_contrib.update:main
        click-odoo-copydb=click_odoo_contrib.copydb:main
        click-odoo-dropdb=click_odoo_contrib.dropdb:main
        click-odoo-initdb=click_odoo_contrib.initdb:main
        click-odoo-backupdb=click_odoo_contrib.backupdb:main
        click-odoo-makepot=click_odoo_contrib.makepot:main
    """,
)
