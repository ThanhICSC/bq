# -*- coding: utf-8 -*-
# Copyright (C) 2011 - Daniel Reis
# Copyright (C) 2018 - Liu Jianyun, Henry Zhou
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Import External Data',
    'version': '11.0.1.0.0',
    'category': 'Tools',
    'summary': 'Import Data From Other Database',
    'description': """
Import data directly from other databases.

Installed in the Administration module, menu Settings -> Technical ->
Database Structure -> External Import Tasks.

Features
========

 * Fetched data from the databases are used to build lines equivalent to
   regular import files. These are imported using the standard "load()"
   ORM method, same as regular import function, benefiting from all its features,
   including xml_ids.
 * Each table import is defined by an SQL statement, used to build the
   equivalent for an import file. Each column's name should match the column
   names you would use in an import file. The first column must provide an
   unique identifier for the record, and will be used to build its xml_id.
 * Allow to import many2one fields, same as regular import module.
 * The last sync date is the last successfully execution can be used in the SQL
   using "%(sync)s", or ":sync" in the case of Oracle.
 * When errors are found, only the record with the error fails import. The
   other correct records are committed. However, the "last sync date" will only
   be automatically updated when no errors are found.
 * The import execution can be scheduled to run automatically.

Contributors
============

* Daniel Reis, Odoo Community Association (OCA)
* Maxime Chambreuil <maxime.chambreuil@savoirfairelinux.com>
* Liu Jianyun <lnkdel@gmail.com>
* Henry Zhou <zhouhenry@live.com>
    """,
    'author': "Daniel Reis, "
              "Liu Jianyun, "
              "Henry Zhou, "
              "Odoo Community Association (OCA)",

    'website': 'http://launchpad.net/addons-tko',
    'images': [
        'images/snapshot1.png',
        'images/snapshot2.png',
    ],
    'depends': [
        'base',
        'base_external_dbsource',
    ],
    'data': [
        'views/base_external_import_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'views/base_external_import_demo.xml',
    ],
    'installable': True,
}
