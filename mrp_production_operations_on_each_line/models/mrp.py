# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-


from openerp import models, fields, api
from openerp.tools import float_is_zero, float_compare


class MRPProductionExtend(models.Model):
    _inherit = 'mrp.production'

    @api.one
    def _resolve_create_move_extra(self, produce_product, remaining_qty):
        # In case you need to make more than planned
        # consumed more in wizard than previously planned
        production = self
        extra_move_id = produce_product.copy(default={'product_uom_qty': remaining_qty,
                                                      'production_id': production.id})
        extra_move = self.env['stock.move'].browse(extra_move_id.id)
        extra_move.action_confirm()
        extra_move.action_done()

    @api.multi
    def action_create_product(self, production_qty_uom, precision, wiz=False):
        self.ensure_one()
        production = self
        stock_mov_obj = self.env['stock.move']
        main_production_move = False
        produced_products = {}
        for produced_product in production.move_created_ids2:
            if produced_product.scrapped:
                continue
            if not produced_products.get(produced_product.product_id.id, False):
                produced_products[produced_product.product_id.id] = 0
            produced_products[produced_product.product_id.id] += produced_product.product_qty
        for produce_product in production.move_created_ids:
            subproduct_factor = production._get_subproduct_factor(produce_product.id)
            # lot_id = False
            if wiz:
                lot_id = wiz.lot_id.id
            else:
                lot = self.env.context.get('manufacturing_restrict_lot_id', False)
                lot_id = lot and lot[self.id] or False
            # Needed when producing more than maximum quantity
            qty = min(subproduct_factor * production_qty_uom, produce_product.product_qty)
            new_moves = produce_product.action_consume(qty,
                                                       location_id=produce_product.location_id.id,
                                                       restrict_lot_id=lot_id)
            stock_mov_obj.browse(new_moves).write({'production_id': production.id})
            remaining_qty = subproduct_factor * production_qty_uom - qty

            if not float_is_zero(remaining_qty, precision_digits=precision):
                # In case you need to make more than planned
                # consumed more in wizard than previously planned
                self._resolve_create_move_extra(produce_product, remaining_qty)
                # extra_move_id = produce_product.copy(default={'product_uom_qty': remaining_qty,
                #                                               'production_id': production.id})
                # extra_move = stock_mov_obj.browse(extra_move_id.id)
                # extra_move.action_confirm()
                # extra_move.action_done()

            if produce_product.product_id.id == production.product_id.id:
                main_production_move = produce_product.id
        return main_production_move

    @api.one
    def _resolve_consume_extra_move(self, consume, remaining_qty, raw_material_line, main_production_move):
        production = self
        # consumed more in wizard than previously planned
        product = self.env['product.product'].browse(consume['product_id'])
        extra_move_id = self.env['stock.move'].browse(
            self._make_consume_line_from_data(production, product,
                                              product.uom_id.id,
                                              remaining_qty, False, 0)
        )
        extra_move_id.write(
            {
                'restrict_lot_id': consume['lot_id'],
                'consumed_for': main_production_move,
                # TODO: Why need location_id?
                # 'location_id': raw_material_line and raw_material_line.location_id.id or False
            }
        )
        extra_move_id.action_done()

    @api.one
    def action_consume_all(self, production_qty_uom=False, precision=None,
                           wiz=False, main_production_move=False):
        stock_mov_obj = self.env['stock.move']
        production = self
        if precision is None:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        if wiz:
            consume_lines = []
            for cons in wiz.consume_lines:
                consume_lines.append(
                    {'product_id': cons.product_id.id, 'lot_id': cons.lot_id.id, 'product_qty': cons.product_qty})
        else:
            consume_lines = self._calculate_qty(production, production_qty_uom)
        for consume in consume_lines:
            remaining_qty = consume['product_qty']
            raw_material_line = False
            for raw_material_line in production.move_lines:
                if raw_material_line.state in ('done', 'cancel'):
                    continue
                if float_compare(remaining_qty, 0, precision) <= 0 \
                        and float_compare(raw_material_line.product_qty, 0, precision) > 0:
                    break
                if consume['product_id'] != raw_material_line.product_id.id:
                    continue
                consumed_qty = min(remaining_qty, raw_material_line.product_qty)
                raw_material_line.action_consume(consumed_qty,
                                                 raw_material_line.location_id.id,
                                                 restrict_lot_id=consume['lot_id'],
                                                 consumed_for=main_production_move)
                remaining_qty -= consumed_qty
            if not float_is_zero(remaining_qty, precision_digits=precision):
                # consumed more in wizard than previously planned
                self._resolve_consume_extra_move(consume=consume, remaining_qty=remaining_qty,
                                                 raw_material_line=raw_material_line,
                                                 main_production_move=main_production_move)

