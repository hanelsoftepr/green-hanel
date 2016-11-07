# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from openerp import fields, api, models


class MRPProductionWizardReverse(models.TransientModel):
    _name = 'mrp.production.wizard.reverse'

    name = fields.Char(string='Name')
    reverse_lines = fields.One2many(comodel_name='mrp.production.wizard.reverse.lines',
                                    inverse_name='wizard_id', string='To Reverse')


class MRPProductionWizardReverseLines(models.TransientModel):
    _name = 'mrp.production.wizard.reverse.lines'