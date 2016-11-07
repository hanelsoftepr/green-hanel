# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-


from openerp import fields, models, api


class MRPProductionWizardForeceAvailability(models.TransientModel):
    _name = 'mrp.production.wizard.force_availability'

    name = fields.Char(string='Name')
    force_lines = fields.One2many(comodel_name='mrp.production.wizard.force_availability.lines',
                                  inverse_name='wizard_id',
                                  string='Product lines')


class MRPProductionWizardForceAvailabilityLines(models.TransientModel):
    _name = 'mrp.production.wizard.force_availability.lines'

    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product')
    product_qty = fields.Float(string='Product Quantity')
    reserved_qty = fields.Float(string='Reserved Quantity')
    remaining_qty = fields.Float(string='Remaining Quantity')
    force_qty = fields.Float(string='Force Quantity')
    move_id = fields.Many2one(string='Stock Move')
    wizard_id = fields.Many2one(comode_name='mrp.production.wizard.force_availability',
                                string='Wizard')
