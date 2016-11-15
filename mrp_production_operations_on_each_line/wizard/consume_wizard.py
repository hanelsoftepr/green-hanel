# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from openerp import models, api, fields
from openerp.addons.decimal_precision import decimal_precision as dp
from common import _commonCalculateQty


class MRPConsumeWizard(models.TransientModel):
    _name = 'mrp.production.wizard.consume'

    name = fields.Char(string='Name')
    consume_lines = fields.One2many(
        comodel_name='mrp.production.wizard.consume.line',
        inverse_name='produce_id',
        string='To Consumes',
    )

    @api.model
    def _get_product_qty(self):
        """ To obtain product quantity
        @param self: The object pointer.
        @return: Quantity
        """
        prod = self.env['mrp.production'].browse(
            self.env.context.get('active_id', []))
        done = 0.0
        for move in prod.move_created_ids2:
            if move.product_id == prod.product_id:
                if not move.scrapped:
                    done += move.product_uom_qty  # As uom of produced products and production order should correspond
        return prod.product_qty - done

    @api.model
    def _calculate_qty(self, production, product_qty):
        result = _commonCalculateQty(self, production)
        return result

    @api.model
    def default_get(self, fields_list):
        """
        Return default quantity of products to consume,
        Use only on mrp.production model by active_model is 'mrp.production'
        """
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False)
        )
        uom_model = self.env["product.uom"]
        consume_lines = []
        product_qty = self._get_product_qty()
        if product_qty > 0.0:
            product_uom_qty = uom_model._compute_qty(
                production.product_uom.id,
                production.product_qty,
                production.product_id.uom_id.id
            )
            moves =  self.env.context.get('__SPECICIFIC_MOVES__', [])
            if moves:
                moves = self.env['stock.move'].browse(moves)
                consume_lines = self._calculate_qty(product_qty=product_uom_qty, moves=moves)
            else:
                consume_lines = self._calculate_qty(production, product_qty=product_uom_qty)

        return {'consume_lines': consume_lines}

    @api.one
    def action_do_consume(self):
        production_model = self.env['mrp.production']
        production = production_model.browse(self.env.context.get('active_id', False))
        if production:
            production.action_consume_all(wiz=self, precision=None)
            production.signal_workflow('button_consume')
        return {'type': 'ir.actions.act_window_close'}


class MRPProductionWizardConsumeLine(models.TransientModel):
    _name = 'mrp.production.wizard.consume.line'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product', required=True
    )
    product_qty = fields.Float(
        string='Quantity (in default UoM)',
        digits=dp.get_precision('Product Unit of Measure')
    )
    lot_id = fields.Many2one(comodel_name='stock.production.lot',
                             string='Lot No.')
    move_id = fields.Many2one(comodel_name='stock.move', string='Move Line')
    produce_id = fields.Many2one(
        comodel_name='mrp.production.wizard.consume',
        string='Wizard',
    )


class StockMoveConsume(models.TransientModel):
    _inherit = 'stock.move.consume'

    @api.multi
    def do_move_consume(self):
        res = super(StockMoveConsume, self).do_move_consume()
        move = self.env['stock.move'].browse(self.env.context.get('active_id', []))
        if not move:
            return res
        move.raw_material_production_id.signal_workflow('button_consume')
        return res
