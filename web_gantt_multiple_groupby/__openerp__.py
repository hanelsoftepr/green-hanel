# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# Next time u need to define a better name for package
{
    'name': 'Web Gantt - Multi Group by',

    'version': '1.0',
    'author': 'Hanelsoft ERP',
    'category': 'Web',
    'sequence': 1,
    'summary': '''Allow users as well as developers easily group tasks by multiple fields
                and add description on each task by fields.\nEasier to manage your projects!''',
    'description': "",
    'depends': ['web_gantt'],
    'data': [
        'templates/templates.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'currency': 'EUR',
    'price': 10.00,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
