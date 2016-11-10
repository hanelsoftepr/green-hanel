# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    HanelSoftERP, product of Hanel Software Solutions JSC (C) 2013
#    Website: http://www.hanelsofterp.com
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

{
    'name': 'Web - Exported Options',
    'description': '',
    'summary': 'Adding an option for exporting with flexible data',
    'version': '1.0',
    'category': 'web',
    'author': 'Hanel Software Solutions',
    'website': 'hanelsofterp.com',
    'depends': ['web'],
    'qweb': ['static/src/xml/template.xml'],
    'data': ['templates/src.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 30,
    'currency': 'EUR'
}
