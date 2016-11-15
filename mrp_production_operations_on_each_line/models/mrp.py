# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-


from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.tools import float_is_zero, float_compare


class MRPProductionExtend(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    @api.depends('move_lines')
    def _compute_show_function_flags(self):
        for production in self:
            moves = production.move_lines
            if all([line.state == 'assigned' for line in moves]) or len(moves) == 0:
                production.show_force_reservation = False
                production.show_produce = True
            else:
                production.show_force_reservation = True
                production.show_produce = False

    show_force_reservation = fields.Boolean(string='Show Force Reservation Button',
                                            compute='_compute_show_function_flags')
    show_produce = fields.Boolean(string='Show Produce Button',
                                  compute='_compute_show_function_flags')

    @api.multi
    def action_open_consume_details(self):
        return {
            'name': 'Consume Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.wizard.consume',
            'target': 'new',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('mrp_production_operations_on_each_line'
                                    '.mrp_production_consume_wizard_form_view').id
        }

    @api.multi
    def action_open_force_details(self):
        return {
            'name': 'Force Reservation Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.wizard.force_availability',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'view_id': self.env.ref('mrp_production_operations_on_each_line'
                                    '.mrp_production_force_reserve_wizard_form_view').id
        }

    @api.multi
    def action_open_reverse_details(self):
        return {
            'name': 'Reversed Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.wizard.reverse',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'view_id': self.env.ref('mrp_production_operations_on_each_line'
                                    '.mrp_production_reversed_wizard_form_view').id
        }

    @api.one
    def _resolve_create_move_extra(self, produce_product, remaining_qty, price_unit=0, main_product=False):
        # In case you need to make more than planned
        # consumed more in wizard than previously planned
        production = self
        extra_move_id = produce_product.copy(default={'product_uom_qty': remaining_qty,
                                                      'production_id': production.id})
        extra_move = self.env['stock.move'].browse(extra_move_id.id)
        if main_product:
            extra_move.write({'price_unit': price_unit})
        extra_move.action_confirm()
        extra_move.action_done()

    @api.multi
    def action_create_product(self, production_qty_uom, precision, total_consume_moves=None, wiz=False):
        """
        Create Finish Product of Production
        :param production_qty_uom:
        :param precision:
        :param total_consume_moves:
        :param wiz:
        :return: None
        """
        self.ensure_one()
        production = self
        if total_consume_moves is None:
            total_consume_moves = set()
        last_production_date = production.move_created_ids2 and max(
            production.move_created_ids2.mapped('date')) or False
        already_consumed_lines = production.move_lines2.filtered(lambda l: l.date > last_production_date)
        total_consume_moves = total_consume_moves.union(already_consumed_lines.ids)
        stock_mov_obj = self.env['stock.move']

        price_unit = 0
        for produce_product in production.move_created_ids:
            is_main_product = (
                                  produce_product.product_id.id == production.product_id.id) and production.product_id.cost_method == 'real'
            if is_main_product:
                total_cost = self._calculate_total_cost(list(total_consume_moves))
                production_cost = self._calculate_workcenter_cost(production.id)
                price_unit = (total_cost + production_cost) / production_qty_uom
            subproduct_factor = production._get_subproduct_factor(produce_product.id)
            lot_id = False
            if wiz:
                lot_id = wiz.lot_id.id

            # Needed when producing more than maximum quantity
            qty = min(subproduct_factor * production_qty_uom, produce_product.product_qty)
            if is_main_product and price_unit:
                produce_product.write({'price_unit': price_unit})
            new_moves = produce_product.action_consume(qty,
                                                       location_id=produce_product.location_id.id,
                                                       restrict_lot_id=lot_id)
            stock_mov_obj.browse(new_moves).write({'production_id': production.id})
            remaining_qty = subproduct_factor * production_qty_uom - qty

            if not float_is_zero(remaining_qty, precision_digits=precision):
                # In case you need to make more than planned
                # consumed more in wizard than previously planned
                self._resolve_create_move_extra(produce_product, remaining_qty, price_unit, is_main_product)

    @api.one
    def _resolve_consume_extra_move(
            self, consume, remaining_qty, raw_material_line, main_production_move, total_consume_moves):
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
        total_consume_moves.add(extra_move_id)
        extra_move_id.action_done()

    @api.one
    def action_consume_all(self, total_consume_moves=None, production_qty_uom=False,
                           precision=None, wiz=False, main_production_move=False):
        """ This function to consume all product of Products to Consume field on Production

        :param total_consume_moves: list of ids
        :param production_qty_uom: float
        :param precision: float
        :param wiz: mrp.production.wizard.consume()
        :param main_production_move: integer
        :return: None
        """
        # stock_mov_obj = self.env['stock.move']
        production = self
        if precision is None:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        if total_consume_moves is None:
            total_consume_moves = set()
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
                if (float_compare(remaining_qty, 0, precision) <= 0) \
                        and (float_compare(raw_material_line.product_qty, 0, precision) > 0):
                    break
                if consume['product_id'] != raw_material_line.product_id.id:
                    continue
                consumed_qty = min(remaining_qty, raw_material_line.product_qty)
                raw_material_line.action_consume(consumed_qty,
                                                 raw_material_line.location_id.id,
                                                 restrict_lot_id=consume['lot_id'],
                                                 consumed_for=main_production_move)
                total_consume_moves.add(raw_material_line.id)
                remaining_qty -= consumed_qty
            if not float_is_zero(remaining_qty, precision_digits=precision):
                # consumed more in wizard than previously planned
                self._resolve_consume_extra_move(consume=consume, remaining_qty=remaining_qty,
                                                 raw_material_line=raw_material_line,
                                                 main_production_move=main_production_move,
                                                 total_consume_moves=total_consume_moves)

    @api.model
    def action_produce(self, production_id, production_qty, production_mode, wiz=False):
        """ To produce final product based on production mode (consume/consume&produce).
        If Production mode is consume, all stock move lines of raw materials will be done/consumed.
        If Production mode is consume & produce, all stock move lines of raw materials will be done/consumed
        and stock move lines of final product will be also done/produced.
        @param production_id: the ID of mrp.production object
        @param production_qty: specify qty to produce in the uom of the production order
        @param production_mode: specify production mode (consume/consume&produce).
        @param wiz: the mrp produce product wizard, which will tell the amount of consumed products needed
        @return: True
        """
        uom_obj = self.env['product.uom']
        production = self.browse(production_id)
        production_qty_uom = uom_obj._compute_qty(production.product_uom.id, production_qty,
                                                  production.product_id.uom_id.id)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        main_production_move = False
        if production_mode == 'consume_produce':
            for produce_product in production.move_created_ids:
                if produce_product.product_id.id == production.product_id.id:
                    main_production_move = produce_product.id

        total_consume_moves = set()
        if production_mode in ['consume', 'consume_produce']:
            production.action_consume_all(
                total_consume_moves=total_consume_moves,
                production_qty_uom=production_qty_uom, precision=precision,
                wiz=wiz, main_production_move=main_production_move
            )

        if production_mode == 'consume_produce':

            production.action_create_product(
                production_qty_uom=production_qty_uom, precision=precision,
                total_consume_moves=total_consume_moves, wiz=wiz
            )
        production.message_post(body=_("%s produced") % self._description)

        # Remove remaining products to consume if no more products to produce
        if not production.move_created_ids and production.move_lines:
            production.move_lines.action_cancel()

        production.signal_workflow('button_produce_done')
        # TODO
        # self.env['stock.quant'].update_usage_account_move_line(production=production)
        return True

    @api.multi
    def test_production_start(self):
        """
        Check for Production if any product is consumed
        The result is value of condition of signal workflow 'button_consume'
        :return: Boolean
        """
        res = True
        for production in self:
            moves = production.move_lines2
            if len(moves) == 0 or \
                    all([line.state == 'cancel' for line in moves]):
                res = False
        return res
