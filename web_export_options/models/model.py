# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from openerp.models import BaseModel

__export_xml_id = BaseModel._BaseModel__export_xml_id
__export_rows = BaseModel._BaseModel__export_rows


def __flexible_export_xml_id(self):
    if not self.env.context.get('flexible_data', False):
        return __export_xml_id(self)
    if self.env.context.get('get_id', False):
        return self.ids[0]
    return str(self.name_get()[0][1])


def __flexible_export_rows(self, fields):
    if not self.env.context.get('flexible_data', False):
        return __export_rows(self, fields)
    if self.env.context.get('depth', [0])[0] == 0:
        self.env.context['depth'][0] += 1
        return __export_rows(self.with_context(get_id=True), fields)
    return __export_rows(self.with_context(get_id=False), fields)


BaseModel._BaseModel__export_xml_id = __flexible_export_xml_id
BaseModel._BaseModel__export_rows = __flexible_export_rows
