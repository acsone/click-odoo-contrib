Changes
~~~~~~~

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
