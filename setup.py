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
    include_package_data=True,
    setup_requires=["setuptools-scm"],
    install_requires=[
        "click-odoo>=1.3.0",
        "manifestoo-core>=0.7",
        "importlib_resources ; python_version<'3.9'",
    ],
    python_requires=">=3.6",
    license="LGPLv3+",
    author="ACSONE SA/NV",
    author_email="info@acsone.eu",
    url="http://github.com/acsone/click-odoo-contrib",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: "
        "GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Odoo",
    ],
    entry_points="""
        [console_scripts]
        click-odoo-uninstall=click_odoo_contrib.uninstall:main
        click-odoo-update=click_odoo_contrib.update:main
        click-odoo-copydb=click_odoo_contrib.copydb:main
        click-odoo-dropdb=click_odoo_contrib.dropdb:main
        click-odoo-initdb=click_odoo_contrib.initdb:main
        click-odoo-listdb=click_odoo_contrib.listdb:main
        click-odoo-backupdb=click_odoo_contrib.backupdb:main
        click-odoo-restoredb=click_odoo_contrib.restoredb:main
        click-odoo-makepot=click_odoo_contrib.makepot:main
    """,
)
