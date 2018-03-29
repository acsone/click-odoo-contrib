click-odoo-contrib
==================

.. image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3
.. image:: https://badge.fury.io/py/click-odoo-contrib.svg
    :target: http://badge.fury.io/py/click-odoo-contrib

``click-odoo-contrib`` is a set of useful Odoo maintenance functions.
They are available as CLI scripts (based on click-odoo_), as well
as composable python functions.

.. contents::

Scripts
~~~~~~~

click-odoo-uninstall
--------------------

.. code::

  Usage: click-odoo-uninstall [OPTIONS]

  Options:
    -c, --config PATH    ...
    -d, --database TEXT  ...
    ...
    -m, --modules TEXT   Comma-separated list of modules to uninstall
			 [required]
    --help               Show this message and exit.

click-odoo-upgrade
--------------------

.. code::

  Usage: click-odoo-upgrade [OPTIONS]

  Options:
    -c, --config PATH    ...
    -d, --database TEXT  ...
    ...
    --i18n-overwrite     Overwrite existing translations
    --upgrade-all        Force a complete upgrade (-u base)
    --help               Show this message and exit.
    
Useful links
~~~~~~~~~~~~

- pypi page: https://pypi.org/project/click-odoo-contrib
- code repository: https://github.com/acsone/click-odoo-contrib
- report issues at: https://github.com/acsone/click-odoo-contrib/issues

.. _click-odoo: https://pypi.python.org/pypi/click-odoo

Credits
~~~~~~~

Contributors:

- Stéphane Bidoul (`ACSONE <http://acsone.eu/>`_)
- Thomas Binsfeld (`ACSONE <http://acsone.eu/>`_)

Maintainer
~~~~~~~~~~

.. image:: https://www.acsone.eu/logo.png
   :alt: ACSONE SA/NV
   :target: https://www.acsone.eu

This project is maintained by ACSONE SA/NV.
