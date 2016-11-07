# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from openerp import models, api, fields
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
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
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
        '''
        Return default quantity of products to consume
        '''
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False)
        )
        prod_obj = self.env["mrp.production"]
        uomModel = self.env["product.uom"]
        consume_lines = []
        new_consume_lines = []
        product_qty = self._get_product_qty()
        if product_qty > 0.0:
            product_uom_qty = uomModel._compute_qty(
                production.product_uom.id,
                production.product_qty,
                production.product_id.uom_id.id
            )
            consume_lines = self._calculate_qty(production, product_qty=product_uom_qty)

        return {'consume_lines': consume_lines}

    @api.one
    def action_do_consume(self):
        production = self.env['mrp.production'].browse(self.env.context.get('active_id', False))
        return production.action_consume_all(wiz=self, precision=None)


class MRPProductionWizardConsumeLine(models.TransientModel):
    _name = 'mrp.production.wizard.consume.line'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product'
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

    @api.multi
    @api.onchange('product_qty', 'product_id')
    def onchange_product_info(self):
        self.ensure_one()
        quants = self.env['stock.quant'].quants_get_prefered_domain(
            self.move_id.location_id, self.product_id,
            self.product_qty, domain=[('qty', '>', 0.0)],
            prefered_domain_list=[[('reservation_id', '=', self.move_id.id)]])
