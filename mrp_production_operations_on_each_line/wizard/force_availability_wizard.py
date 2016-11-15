# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-


from openerp import fields, models, api
import openerp.addons.decimal_precision as dp


class MRPProductionWizardForeceAvailability(models.TransientModel):
    _name = 'mrp.production.wizard.force_availability'

    name = fields.Char(string='Name')
    force_lines = fields.One2many(comodel_name='stock.move.force_reserve',
                                  inverse_name='wizard_id',
                                  string='Product lines')

    @api.model
    def default_get(self, fields_list):
        res = super(MRPProductionWizardForeceAvailability, self).default_get(fields_list)
        production = self.env['mrp.production'].browse(self.env.context.get('active_id'))
        if not production:
            return res
        res.update({'force_lines': []})
        for move in production.move_lines:
            if move.state in ('confirmed', 'waiting', 'draft'):
                qty = move.product_qty - move.reserved_availability
                res['force_lines'].append((0, 0, {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_qty': move.product_qty,
                    'product_uom': move.product_id.uom_id.id,
                    'reserved_qty': move.reserved_availability,
                    'remaining_qty': qty,
                    'force_qty': qty,
                    'location_id': move.location_id.id,
                    'lot_id': move.restrict_lot_id.id
                }))
        return res

    @api.multi
    def action_do_force_reserve(self):
        self.ensure_one()
        for line in self.force_lines:
            line.move_id.force_assign()
        return {'type': 'ir.actions.act_window_close'}


class StockMoveForceRserveWizard(models.TransientModel):
    _name = 'stock.move.force_reserve'

    move_id = fields.Many2one(string='Move', comodel_name='stock.move')
    wizard_id = fields.Many2one(comodel_name='mrp.production.wizard.force_availability',
                                string='Wizard')
    product_id = fields.Many2one(string='Product', comodel_name='product.product', required=True, select=True)
    product_qty = fields.Float(string='Product Quantity', required=True,
                               digits=dp.get_precision('Product Unit of Measure'),
                               readonly=True
                               )
    reserved_qty = fields.Float(string='Reserved Quantity',
                                digits=dp.get_precision('Product Unit of Measure'),
                                readonly=True)
    remaining_qty = fields.Float(string='Remaining Quantity',
                                 digits=dp.get_precision('Product Unit of Measure'),
                                 readonly=True
                                 )
    force_qty = fields.Float(string='Force Quantity', digits=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one(string='Product Unit of Measure', comodel_name='product.uom')
    location_id = fields.Many2one(string='Location', comodel_name='stock.location')
    lot_id = fields.Many2one(string='Lot', comodel_name='stock.production.lot')

    @api.model
    def default_get(self, fields_list):
        res = super(StockMoveForceRserveWizard, self).default_get(fields_list)
        move = self.env['stock.move'].browse(self.env.context.get('active_id', []))
        reserved_qty = move.reserved_availability
        product_qty = move.product_qty
        remaining_qty = product_qty - reserved_qty
        if 'product_id' in fields_list:
            res.update({'product_id': move.product_id.id})
        if 'product_uom' in fields_list:
            res.update({'product_uom': move.product_uom.id})
        if 'product_qty' in fields_list:
            res.update({'product_qty': product_qty})
        if 'location_id' in fields_list:
            res.update({'location_id': move.location_id.id})
        if 'restrict_lot_id' in fields_list:
            res.update({'restrict_lot_id': move.restrct_lot_id.id})
        if 'move_id' in fields_list:
            res.update({'move_id': move.id})
        if 'reserved_qty' in fields_list:
            res.update({'reserved_qty': reserved_qty})
        if 'remaining_qty' in fields_list:
            res.update({'remaining_qty': remaining_qty})
        if 'force_qty' in fields_list:
            res.update({'force_qty': remaining_qty})
        return res

    @api.multi
    def do_move_force_reservation(self):
        uom_obj = self.env['product.uom']
        for wiz in self:
            qty = uom_obj._compute_qty(wiz['product_uom'].id, wiz.product_qty, wiz.product_id.uom_id.id)
