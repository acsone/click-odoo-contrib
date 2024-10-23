Changes
~~~~~~~

.. towncrier release notes start

1.20 (2024-10-23)
-----------------

**Features**

- Odoo 18 compatibility (`#150
  <https://github.com/acsone/click-odoo-contrib/pull/150>`_, `#152
  <https://github.com/acsone/click-odoo-contrib/pull/152>`_, `#154
  <https://github.com/acsone/click-odoo-contrib/pull/154>`_)

1.19 (2024-07-22)
-----------------

**Features**

- click-odoo-restoredb: Add ``--neutralize`` option. This works only in odoo 16.0 and above. (`#143 <https://github.com/acsone/click-odoo-contrib/issues/143>`_)


1.18.1 (2023-11-16)
-------------------

**Features**

- click-odoo-update : Do not run/update Odoo when no module needs updating. (`#144 <https://github.com/acsone/click-odoo-contrib/issues/144>`_)


1.18.0 (2023-10-29)
-------------------

**Features**

- Support Odoo 17. (`#190 <https://github.com/acsone/click-odoo-contrib/issues/190>`_)


1.17.0 (2023-09-03)
-------------------

**Features**

- New ``click-odoo-listdb`` command. (`#126 <https://github.com/acsone/click-odoo-contrib/issues/126>`_)
- ``click-odoo-update``: exclude the ``tests/`` directory from checksum computation
  A modification in tests alone should not require a database upgrade. (`#125 <https://github.com/acsone/click-odoo-contrib/issues/125>`_)
- ``click-odoo-update``: set ``create_date`` and ``write_date`` on the ``ir_config_parameter`` checksums record (`#128 <https://github.com/acsone/click-odoo-contrib/issues/128>`_)


1.16.0 (2022-09-21)
-------------------

**Features**

- Add dependency on manifestoo_core to obtain Odoo core addons list (used by
  click-odoo-update to ignore core addons). (`#114 <https://github.com/acsone/click-odoo-contrib/issues/114>`_)
- Adapt click-odoo-update for Odoo 16. (`#119 <https://github.com/acsone/click-odoo-contrib/issues/119>`_)

**Deprecations and Removals**

- Remove support for Python < 3.6 and Odoo < 11. (`#110 <https://github.com/acsone/click-odoo-contrib/issues/110>`_)


1.15.1 (2021-12-04)
-------------------

**Bugfixes**

- Silence Odoo 15 noisy warnings about using autocommit. (`#105 <https://github.com/acsone/click-odoo-contrib/issues/105>`_)


1.15.0 (2021-10-06)
-------------------

**Features**

- Update core addons lists, with Odoo 15 support. (`#104 <https://github.com/acsone/click-odoo-contrib/issues/104>`_)


1.14.0 (2021-06-28)
-------------------

**Features**

- Adding a new option to enable using rsync and hardlinks for copying filestore:
  `--filestore-copy-mode [default|rsync|hardlink]`. (`#86 <https://github.com/acsone/click-odoo-contrib/issues/86>`_)


1.13.0 (2021-06-25)
-------------------

**Features**

- Backup and restore commands: add support for "dump" format (`#79 <https://github.com/acsone/click-odoo-contrib/issues/79>`_)
- ``click-odoo-makepot``: add --modules option to select modules to export. (`#92 <https://github.com/acsone/click-odoo-contrib/issues/92>`_)
- ``click-odoo-update``: also pass all modified modules in ``to upgrade`` state to
  Odoo for update; this helps upgrading when there are new dependencies, in
  combination with Odoo `#72661 <https://github.com/odoo/odoo/pull/72661>`__. (`#97 <https://github.com/acsone/click-odoo-contrib/issues/97>`_)


**Bugfixes**

- ``click-odoo-update``: do not attempt to update addons that are uninstallable. (`#89 <https://github.com/acsone/click-odoo-contrib/issues/89>`_)


1.12.0 (2020-11-25)
-------------------

**Features**

- ``click-odoo-makepot`` gained new options controlling how it merges
  new strings in existing ``.po`` files: ``--no-fuzzy-matching`` and
  ``--purge-old-translation``. (`#87 <https://github.com/acsone/click-odoo-contrib/issues/87>`_)


1.11.0 (2020-10-01)
-------------------

**Features**

- In ``click-odoo-copydb``, reset ``database.*`` system parameters, to prevent
  conflicts between databases (database.uuid, database.secret,
  database.enterprise_code, ...) (`#25 <https://github.com/acsone/click-odoo-contrib/issues/25>`_)
- Add ``click-odoo-restoredb`` command. (`#32 <https://github.com/acsone/click-odoo-contrib/issues/32>`_)
- Update core addons lists (for click-odoo-update --ignore-core-addons),
  including Odoo 14 support. (`#81 <https://github.com/acsone/click-odoo-contrib/issues/81>`_)


1.10.1 (2020-04-29)
-------------------

**Bugfixes**

- click-odoo-update: fix packaging issue (missing core addons lists). (`#77 <https://github.com/acsone/click-odoo-contrib/issues/77>`_)


1.10.0 (2020-04-28)
-------------------

**Features**

- click-odoo-initdb: add support of dot and underscore in database name. (`#35 <https://github.com/acsone/click-odoo-contrib/issues/35>`_)
- click-odoo-update: added --list-only option. (`#68 <https://github.com/acsone/click-odoo-contrib/issues/68>`_)
- click-odoo-update: add --ignore-addons and --ignore-core-addons options to
  exclude addons from checksum change detection. (`#69 <https://github.com/acsone/click-odoo-contrib/issues/69>`_)


**Improved Documentation**

- initdb, dropdb, update: move out of beta. (`#70 <https://github.com/acsone/click-odoo-contrib/issues/70>`_)


**Deprecations and Removals**

- Remove deprecated click-odoo-upgrade. (`#71 <https://github.com/acsone/click-odoo-contrib/issues/71>`_)


1.9.0 (2020-03-23)
------------------
- click-odoo-update: acquire an advisory lock on the database so multiple
  instances of click-odoo-update will not start at the same time on the
  same database (useful when there are several Odoo instances running
  on the same database and all running click-odoo-update at startup)

1.8.0 (2019-10-01)
------------------
- Support Odoo SaaS versions
- click-odoo-update now has some support for updating while another Odoo
  instance is running against the same database, by using a watcher that
  aborts the update in case a DB lock happens (this is an advanced feature)

1.7.0 (2019-09-02)
------------------
- makepot: always check validity of .po files

1.6.0 (2019-03-28)
------------------
- update: support postgres 9.4
- backupdb: work correctly when list_db is false too
- backupdb: new --(no-)filestore option
- dropdb: refactored to use Odoo api instead of custom code

1.5.0 (2019-02-05)
------------------
- add click-odoo-backupdb

1.4.1 (2018-11-21)
------------------
- fix broken click-odoo-update --i18n-overwrite

1.4.0 (2018-11-19)
------------------

- new click-odoo-update which implements the functionality of module_auto_update
  natively, alleviating the need to have module_auto_update installed in the database,
  and is more robust (it does a regular -u after identifying modules to update)
- upgrade: deprecated in favor of click-odoo-update
- initdb: save installed checksums so click-odoo-update can readily use them
- initdb: add --addons-path option
- copydb: fix error when source filestore did not exist

1.3.1 (2018-11-05)
------------------
- Add --unless-exists option to click-odoo-initdb

1.3.0 (2018-10-31)
------------------
- Add click-odoo-copydb
- Add click-odoo-dropdb
- Add --if-exists option to click-odoo-upgrade

1.2.0 (2018-10-07)
------------------
- Odoo 12 support

1.1.4 (2018-06-21)
------------------
- makepot: fix issue when addons-dir is not current directory
  (this should also fix issues when there are symlinks)

1.1.3 (2018-06-20)
------------------
- makepot: add --commit-message option

1.1.2 (2018-06-20)
------------------
- makepot: force git add in case .pot are in .gitignore
  (made for https://github.com/OCA/maintainer-quality-tools/issues/558)

1.1.1 (2018-06-16)
------------------
- makepot: add --msgmerge-if-new-pot option

1.1.0 (2018-06-13, Sevilla OCA code sprint)
-------------------------------------------
- add click-odoo-makepot
- in click-odoo-initdb, include active=True modules in hash computation
  (because modules with active=True are auto installed by Odoo)

1.0.4 (2018-06-02)
------------------
- update module list after creating a database from cache, useful when
  we are creating a database in an environment where modules have
  been added since the template was created

1.0.3 (2018-05-30)
------------------
- fix: handle situations where two initdb start at the same time
  ending up with an "already exists" error when creating the cached template

1.0.2 (2018-05-29)
------------------
- fix: initdb now stores attachments in database when cache is enabled,
  so databases created from cache do not miss the filestore

1.0.1 (2018-05-27)
------------------
- better documentation
- fix: initdb now takes auto_install modules into account

1.0.0 (2018-05-27)
------------------
- add click-odoo-initdb

1.0.0b3 (2018-05-17)
--------------------
- be more robust in rare case button_upgrade fails silently

1.0.0b2 (2018-03-28)
--------------------
- uninstall: commit and hide --rollback
- upgrade: refactor to add composable function


1.0.0b1 (2018-03-28)
--------------------
- upgrade: save installed checksums after full upgrade


1.0.0a1 (2018-03-22)
--------------------
- first alpha
- click-odoo-uninstall
- click-odoo-upgrade
