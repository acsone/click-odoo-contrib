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

click-odoo-initdb (beta)
------------------------

.. code::

  Usage: click-odoo-initdb [OPTIONS]

    Create an Odoo database with pre-installed modules.

    Almost like standard Odoo does with the -i option, except this script
    manages a cache of database templates with the exact same addons
    installed. This is particularly useful to save time when initializing test
    databases.

    Cached templates are identified by computing a sha1 checksum of modules
    provided with the -m option, including their dependencies and
    corresponding auto_install modules.

  Options:
    -c, --config PATH         ...
    ...
    -n, --new-database TEXT   Name of new database to create, possibly from
			      cache. If absent, only the cache trimming
			      operation is executed.
    -m, --modules TEXT        Comma separated list of addons to install.
			      [default: base]
    --demo / --no-demo        Load Odoo demo data.  [default: True]
    --cache / --no-cache      Use a cache of database templates with the exact
			      same addons installed. Disabling this option also
			      disables all other cache-related operations such
			      as max-age or size. Note: when the cache is
			      enabled, all attachments created during database
			      initialization are stored in database instead of
			      the default Odoo file store.  [default: True]
    --cache-prefix TEXT       Prefix to use when naming cache template databases
			      (max 8 characters). CAUTION: all databases named
			      like {prefix}-____________-% will eventually be
			      dropped by the cache control mechanism, so choose
			      the prefix wisely.  [default: cache]
    --cache-max-age INTEGER   Drop cache templates that have not been used for
			      more than N days. Use -1 to disable.  [default:
			      30]
    --cache-max-size INTEGER  Keep N most recently used cache templates. Use -1
			      to disable. Use 0 to empty cache.  [default: 5]
    --help                    Show this message and exit.

click-odoo-makepot (stable)
---------------------------

.. code::

  Usage: click-odoo-makepot [OPTIONS]

    Export translation (.pot) files of addons installed in the database and
    present in addons_dir. Additionally, run msgmerge on the existing .po
    files to keep them up to date. Commit changes to git, if any.

  Options:
    -c, --config PATH           ...
    -d, --database TEXT         ...
    ...
    --addons-dir TEXT           [default: .]
    --msgmerge / --no-msgmerge  Merge .pot changes into all .po files
                                [default: False]
    --msgmerge-if-new-pot / --no-msg-merge-if-new-pot
                                Merge .pot changes into all .po files, only
                                if a new .pot file has been created.
                                [default: False]
    --commit / --no-commit      Git commit exported .pot files if needed.
                                [default: False]
    --help                      Show this message and exit.

click-odoo-uninstall (stable)
-----------------------------

.. code::

  Usage: click-odoo-uninstall [OPTIONS]

  Options:
    -c, --config PATH    ...
    -d, --database TEXT  ...
    ...
    -m, --modules TEXT   Comma-separated list of modules to uninstall
			 [required]
    --help               Show this message and exit.

click-odoo-upgrade (stable)
---------------------------

.. code::

  Usage: click-odoo-upgrade [OPTIONS]

    Upgrade an Odoo database (odoo -u), taking advantage of
    module_auto_update's upgrade_changed_checksum method if present.

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

- Stéphane Bidoul (ACSONE_)
- Thomas Binsfeld (ACSONE_)
- Benjamin Willig (ACSONE_)

.. _ACSONE: https://acsone.eu

Maintainer
~~~~~~~~~~

.. image:: https://www.acsone.eu/logo.png
   :alt: ACSONE SA/NV
   :target: https://www.acsone.eu

This project is maintained by ACSONE SA/NV.
