# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from openerp import models, api, fields


class StockMoveExtend(models.Model):
    _inherit = 'stock.move'

    consumed_move_id = fields.Many2one(comodel_name='stock.move', string='Consumed Move')
    unconsumed_move_ids = fields.One2many(comodel_name='stock.move',
                                          inverse_name='consumed_move_id',
                                          string='Un-consumed Move')
    state = fields.Selection(selection_add=[('reversed', 'Reversed')])

    @api.multi
    def action_reverse_done(self):
        quant_model = self.env['stock.quant']
        location_model = self.env['stock.location']
        for move in self:
            domain = [('id', 'in', move.consumed_move_id.quant_ids.ids),
                      ('qty', '>', 0),
                      ('location_id', '=', move.location_id.id)]
            if move.restrict_lot_id.id:
                domain.append(('lot_id', '=', move.restrict_lot_id.id))
            removal_strategy = location_model.get_removal_strategy(move.product_qty, move)
            # quants = quant_model.quants_get_preferred_domain(
            #     move.product_qty, move, lot_id=move.restrict_lot_id.id,
            #     domain=domain, preferred_domain_list=[])
            quants = quant_model.quants_get(move.product_qty, move, ops=False,
                                            domain=domain, removal_strategy=removal_strategy)
            quant_model.quants_reserve(quants, move)
            quant_model.quants_move(quants, move, move.location_dest_id,
                                    lot_id=move.restrict_lot_id.id,
                                    owner_id=move.restrict_partner_id.id)
            quant_model.quants_unreserve(move)
        self.write({'state': 'reversed'})

    @api.multi
    def action_open_unconsume_wizard(self):

        return {
            'name': 'Un-consume Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.force_reserve',
            'view_id': self.env.ref('mrp_production_operations_on_each_line'
                                    '.stock_move_unconsume_wizard').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current'
        }
