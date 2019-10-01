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

click-odoo-copydb (beta)
------------------------

.. code::

  Usage: click-odoo-copydb [OPTIONS] SOURCE DEST

    Create an Odoo database by copying an existing one.

    This script copies using postgres CREATEDB WITH TEMPLATE. It also copies
    the filestore.

  Options:
    -c, --config FILE       ...
    ...
    -f, --force-disconnect  Attempt to disconnect users from the template
                            database.
    --unless-dest-exists    Don't report error if destination database already
                            exists.
    --if-source-exists      Don't report error if source database does not
                            exist.
    --help                  Show this message and exit.

click-odoo-dropdb (beta)
------------------------

.. code::

  Usage: click-odoo-dropdb [OPTIONS] DBNAME

    Drop an Odoo database and associated file store.

  Options:
    -c, --config FILE  ...
    ...
    --if-exists        Don't report error if database doesn't exist.
    --help             Show this message and exit.

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
    -c, --config FILE         ...
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
    --unless-exists           Don't report error if database already exists.
    --help                    Show this message and exit.

click-odoo-backupdb (beta)
--------------------------

.. code::

  Usage: click-odoo-backupdb [OPTIONS] DBNAME DEST

    Create an Odoo database backup.

    This script dumps the database using pg_dump. It also copies the filestore.

    Unlike Odoo, this script allows you to make a backup of a database without
    going through the web interface. This avoids timeout and file size
    limitation problems when databases are too large.

    It also allows you to make a backup directly to a directory. This type of
    backup has the advantage that it reduces memory consumption since the
    files in the filestore are directly copied to the target directory as well
    as the database dump.

  Options:
    -c, --config FILE           ...
    ...
  --force                       Don't report error if destination file/folder
                                already exists.  [default: False]
  --if-exists                   Don't report error if database does not exist.
  --format [zip|folder]         Output format  [default: zip]
  --filestore / --no-filestore  Include filestore in backup  [default: True]
  --help                        Show this message and exit.

click-odoo-makepot (stable)
---------------------------

.. code::

  Usage: click-odoo-makepot [OPTIONS]

    Export translation (.pot) files of addons installed in the database and
    present in addons_dir. Additionally, run msgmerge on the existing .po
    files to keep them up to date. Commit changes to git, if any.

  Options:
    -c, --config FILE           ...
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

click-odoo-update (beta)
------------------------

.. code::

  Usage: click-odoo-update [OPTIONS]

    Update an Odoo database (odoo -u), automatically detecting addons to
    update based on a hash of their file content, compared to the hashes
    stored in the database.

    It allows updating in parallel while another Odoo instance is still
    running against the same database, by using a watcher that aborts the
    update in case a DB lock happens.

  Options:
    -c, --config FILE            Specify the Odoo configuration file. Other ways
                                 to provide it are with the ODOO_RC or
                                 OPENERP_SERVER environment variables, or
                                 ~/.odoorc (Odoo >= 10) or ~/.openerp_serverrc.
    --addons-path TEXT           Specify the addons path. If present, this
                                 parameter takes precedence over the addons path
                                 provided in the Odoo configuration file.
    -d, --database TEXT          Specify the database name. If present, this
                                 parameter takes precedence over the database
                                 provided in the Odoo configuration file.
    --log-level TEXT             Specify the logging level. Accepted values
                                 depend on the Odoo version, and include debug,
                                 info, warn, error.  [default: info]
    --logfile FILE               Specify the log file.
    --i18n-overwrite             Overwrite existing translations
    --update-all                 Force a complete upgrade (-u base)
    --if-exists                  Don't report error if database doesn't exist
    --watcher-max-seconds FLOAT  Max DB lock seconds allowed before aborting the
                                 update process. Default: 0 (disabled).
    --help                       Show this message and exit.

click-odoo-upgrade (deprecated, see click-odoo-update)
------------------------------------------------------

.. code::

  Usage: click-odoo-upgrade [OPTIONS]

    Upgrade an Odoo database (odoo -u), taking advantage of
    module_auto_update's upgrade_changed_checksum method if present.

  Options:
    -c, --config FILE    ...
    -d, --database TEXT  ...
    ...
    --i18n-overwrite     Overwrite existing translations
    --upgrade-all        Force a complete upgrade (-u base)
    --if-exists          Don't report error if database doesn't exist.
    --help               Show this message and exit.

Useful links
~~~~~~~~~~~~

- pypi page: https://pypi.org/project/click-odoo-contrib
- code repository: https://github.com/acsone/click-odoo-contrib
- report issues at: https://github.com/acsone/click-odoo-contrib/issues

.. _click-odoo: https://pypi.python.org/pypi/click-odoo

Development
~~~~~~~~~~~

To run tests, type ``tox``. Tests are made using pytest. To run tests matching
a specific keyword for, say, Odoo 12 and python 3.6, use
``tox -e py36-12.0 -- -k keyword``.

This project uses `black <https://github.com/ambv/black>`_
as code formatting convention, as well as isort and flake8.
To make sure local coding convention are respected before
you commit, install
`pre-commit <https://github.com/pre-commit/pre-commit>`_ and
run ``pre-commit install`` after cloning the repository.

Credits
~~~~~~~

Contributors:

- Stéphane Bidoul (ACSONE_)
- Thomas Binsfeld (ACSONE_)
- Benjamin Willig (ACSONE_)
- Jairo Llopis (Tecnativa_)
- Laurent Mignon (ACSONE_)

.. _ACSONE: https://acsone.eu
.. _Tecnativa: https://tecnativa.com

Maintainer
~~~~~~~~~~

.. image:: https://www.acsone.eu/logo.png
   :alt: ACSONE SA/NV
   :target: https://www.acsone.eu

This project is maintained by ACSONE SA/NV.
