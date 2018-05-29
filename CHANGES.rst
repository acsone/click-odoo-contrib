Changes
~~~~~~~

.. Future (?)
.. ----------
.. -

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
