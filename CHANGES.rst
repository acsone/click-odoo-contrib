Changes
~~~~~~~

.. Future (?)
.. ----------
.. -

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
