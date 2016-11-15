# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from openerp import fields, api, models
from openerp.tools import float_compare
from openerp.exceptions import except_orm
from openerp.addons.decimal_precision import decimal_precision as dp
import datetime


class MRPProductionWizardReverse(models.TransientModel):
    _name = 'mrp.production.wizard.reverse'

    name = fields.Char(string='Name')
    reverse_lines = fields.One2many(comodel_name='stock.move.unconsume',
                                    inverse_name='wizard_id', string='To Reverse')

    @api.model
    def default_get(self, fields_list):
        res = super(MRPProductionWizardReverse, self).default_get(fields_list)
        if not self.env.context.get('active_model', '>"<') == 'mrp.production':
            return res
        production = self.env['mrp.production'].browse(self.env.context.get('active_id', []))
        if production:
            res.update({
                'reverse_lines': []
            })
            for move in production.move_lines2.filtered(lambda x: x.state == 'done'):
                res['reverse_lines'].append((0, 0, {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_qty': move.product_uom_qty,
                    'product_uom': move.product_uom.id,
                    'location_id': move.location_id.id
                }))

        return res

    @api.multi
    def action_do_unconsume(self):
        self.ensure_one()
        self.reverse_lines.action_do_unconsume()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_view_reversed_move(self):
        tree_view_id = self.env.ref('mrp_production_operations_on_each_line'
                                    '.stock_move_unconsume_tree_view').id
        production = self.env['mrp.production'].browse(self.env.context.get('active_id', []))
        if not production:
            return None
        ids = []
        for move in production.move_lines2.filtered(lambda x: x.state == 'done'):
            ids += move.unconsumed_move_ids.ids

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_type': 'form',
            'views': [(tree_view_id, 'tree'), (False, 'form')],
            'target': 'new',
            'domain': [('id', 'in', ids)]
        }


class StockMoveUnconsume(models.TransientModel):
    _name = 'stock.move.unconsume'

    @api.multi
    @api.depends('move_id', 'product_uom', 'restrict_lot_id')
    def _compute_consumed_qty(self):
        uom_model = self.env['product.uom']
        for w in self:
            move = w.move_id
            quants = move.quant_ids.filtered(lambda x: x.qty > 0 and x.location_id.id == move.location_dest_id.id)
            if w.restrict_lot_id.id:
                quants = quants.filtered(lambda x: x.lot_id.id == w.restrict_lot_id.id)
            qty = sum([quant.qty for quant in quants])
            w.consumed_base_uom_qty = qty
            w.consumed_qty = uom_model._compute_qty_obj(
                move.product_id.uom_id, qty, w.product_uom
            )

    wizard_id = fields.Many2one(comodel_name='mrp.production.wizard.reverse')
    move_id = fields.Many2one(comodel_name='stock.move', string='Move')
    consumed_base_uom_qty = fields.Float(string='Consumed Quantity', compute='_compute_consumed_qty')
    consumed_qty = fields.Float(string='Consumed Quantity', compute='_compute_consumed_qty')
    product_id = fields.Many2one(comodel_name='product.product', string='Product',
                                 required=True, select=True)
    product_qty = fields.Float(string='Quantity to Reverse', required=True,
                               digits_compute=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one(comodel_name='product.uom',
                                  string='Product Unit of Measure', required=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Destination Location', required=True)
    restrict_lot_id = fields.Many2one(comodel_name='stock.production.lot', string='Restrict Lot')

    @api.model
    def default_get(self, fields_list):
        res = super(StockMoveUnconsume, self).default_get(fields_list)
        if not self.env.context.get('active_model', '^^!') == 'stock.move':
            return res
        move = self.env['stock.move'].browse(self.env.context.get('active_id'))
        if move:
            res.update({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'product_qty': move.product_uom_qty,
                'product_uom': move.product_uom.id,
                'location_id': move.location_id.id,
                'restrict_lot_id': move.restrict_lot_id.id
            })
        return res

    @api.multi
    def action_do_unconsume(self):
        dp = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for wizard in self:
            move = wizard.move_id
            if move.state != 'done':
                continue

            consumed_qty = wizard.consumed_qty
            if float_compare(wizard.product_qty, consumed_qty, precision_digits=dp) > 0:
                raise except_orm('Error!', 'Reversed quantity larger than consumed quantity for %s.\n'
                                           'Please input reversed quantity less than %s'
                                 % (move.product_id.name_template, consumed_qty))
            time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            reversed_move = move.copy(default={
                'location_id': move.location_dest_id.id,
                'location_dest_id': wizard.location_id.id or move.location_id.id,
                'product_uom_qty': self.env['product.uom']._compute_qty_obj(
                    wizard.product_uom, wizard.product_qty, move.product_uom
                ),
                'restrict_lot_id': wizard.restrict_lot_id.id or move.restrict_lot_id.id,
                'create_date': time_now,
                'date': time_now,
                'state': 'draft',
                'consumed_move_id': move.id
            })
            reversed_move.action_confirm()
            reversed_move.action_reverse_done()
