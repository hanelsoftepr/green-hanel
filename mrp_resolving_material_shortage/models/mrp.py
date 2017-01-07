__author__ = 'trananhdung'

from openerp import fields, models, api
from datetime import date, datetime as dt
from openerp.tools import float_compare


class nppMrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    @api.depends('picking_ids')
    def _get_number_of_picking(self):
        for r in self:
            r.picking_count = len(r.picking_ids)

    @api.multi
    @api.depends('server_procurement_ids')
    def _get_procurement_count(self):
        for r in self:
            r.procurement_count = len(r.server_procurement_ids)

    picking_ids = fields.One2many(comodel_name='stock.picking',
                                  inverse_name='production_id',
                                  string='Pickings')
    picking_count = fields.Integer(string='Number of Pickings',
                                   compute='_get_number_of_picking')
    server_procurement_ids = fields.One2many(comodel_name='procurement.order',
                                             inverse_name='order_production_id',
                                             string='Procurements')
    procurement_count = fields.Integer(string='Number of Procurement', compute='_get_procurement_count')

    @api.model
    def _make_production_produce_line(self, production):
        ids = super(nppMrpProduction, self)._make_production_produce_line(production)
        # if self.env.context.get('makeChildManufacturing', False):
        self.env['stock.move'].browse(ids).write({'propagate': False})
        return ids

    def _prepare_prev_stock_move_vals(self, move, location_id, qty):
        move_vals = {
            'location_id': location_id,
            'location_dest_id': move.location_id.id,
            'origin': move.raw_material_production_id.name,
            'product_id': move.product_id.id,
            # 'product_qty': qty,
            'product_uom': move.product_id.uom_id.id,
            'product_uom_qty': qty,
            'name': move.product_id.name,
            'move_dest_id': move.id,
            'date_expected': move.date_expected,
            'propagate': False,
            'sequence': move.sequence,
        }
        return move_vals

    def _create_prev_stock_move_for(self, move, production):
        dp = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        quantity = move.product_qty - move.reserved_availability - sum(
            [p.product_qty for p in production.server_procurement_ids
             if p.state == 'running' and p.product_id.id == move.product_id.id]
        )
        if move.state == 'waiting':
            quantity -= sum([o.product_qty for o in move.move_orig_ids
                             if o.state not in ['cancel', 'done']])
        if float_compare(quantity, 0, dp) <= 0:
            return [[], 0]
        quantModel = self.env['stock.quant']
        moveModel = self.env['stock.move']
        quants0 = quantModel.with_context(for_move_id=move.id).quants_get_preferred_domain(
                quantity, move, ops=False,
                domain=[('reservation_id', '=', False), ('qty', '>', 0)],
                lot_id=move.restrict_lot_id.id,
                preferred_domain_list=[]
        )
        quantModel.quants_reserve(quants0, move)
        # quantity = move.product_qty - move.reserved_availability - sum(
        #     [p.product_qty for p in production.server_procurement_ids
        #      if p.state == 'running' and p.product_id.id == move.product_id.id]
        # )
        #
        # if move.state == 'waiting':
        #     quantity -= sum([o.product_qty for o in move.move_orig_ids
        #                      if o.state not in ['cancel', 'done']])
        removal_strategy = self.env['stock.location'].get_removal_strategy(quantity, move, ops=False)
        quants = quantModel.apply_removal_strategy(
            quantity, move=move.product_id, ops=False,
            domain=[('location_id.usage', '=', 'internal'),
                    ('reservation_id', '=', False),
                    ('qty', '>', 0)],
            removal_strategy=removal_strategy
        )

        move_created = []
        remaining_qty = 0
        quant_location = {}
        for quant in quants:
            if quant[0] is None:
                quant_location[None] = quant[1]
            elif quant[0].location_id.id in quant_location:
                quant_location[quant[0].location_id.id] += quant[1]
            else:
                quant_location[quant[0].location_id.id] = quant[1]
        for location_id in quant_location:
            if location_id is not None:
                move_vals = self._prepare_prev_stock_move_vals(
                    move, location_id, quant_location[location_id])
                move_id = moveModel.create(move_vals)
                move_id.action_confirm()
                move_created.append(move_id)
            else:
                remaining_qty = quant_location[None]

        return move_created, remaining_qty

    def _create_stock_operation(self, location_id, location_dest_id, production):
        vals = {
            'date': dt.today().strftime('%Y-%m-%d %H:%M:%S'),
            'picking_type_id': False,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'origin': production.name,
            'partner_id': self.env.user.partner_id.id,
            'production_id': production.id
        }
        warehouse = self.env['stock.warehouse'].browse(
                self.env['stock.location'].get_warehouse(location_id))
        picking_type_id = False
        if warehouse:
            picking_type_id = warehouse.int_type_id.id
        if not picking_type_id:
            vals.update({'name': 'Internal Transfer'})
        else:
            vals.update({'picking_type_id': picking_type_id})
        return self.env['stock.picking'].create(vals)

    def _create_stock_operations(self, moves, production):
        # ***New function on mrp.production model***
        """This function to create stock operations for MO, for each couple of location
        (source location and destination location) on moves is the same, will be create
        a stock operation on it.
        :param moves - list of moves to create operations,
        :param production - MO
        :return picking_created_ids - list of picking (Stock Operation) ids
        """
        stock_model = self.env['stock.move']
        keyCache = {}
        for move in moves:
            # _key = (move.location_id.get_view_location_warehouse(), move.location_dest_id.id)
            _key = (move.location_id.id, move.location_dest_id.id)
            if _key in keyCache:
                keyCache[_key].append(move.id)
            else:
                keyCache[_key] = [move.id]
        picking_created_ids = []
        for _key in keyCache:
            stockPicking = self._create_stock_operation(_key[0], _key[1], production)
            picking_created_ids.append(stockPicking.id)
            [x[1].write({'sequence': x[0]+1, 'picking_id': stockPicking.id})
             for x in enumerate(stock_model.browse(keyCache[_key]))]
            stock_model.browse(keyCache[_key]).write({'picking_id': stockPicking.id})
            stockPicking.action_confirm()
        return picking_created_ids

    def _make_procurement_to_consume(self, production, move, quantity, precision):
        """Make Procurement for move when quantity in all internal locations not enough to
        provide for this move
        :param production - to get all server procurement of this production
        :param move - procurement fo this move
        :param quantity - need to create procurement with quantity
        :param precision - digits to compare float
        :return
        """

        quantity = quantity - sum([p.product_qty
                                   for p in production.server_procurement_ids
                                   if p.state in ('exception', 'confirmed') and
                                   p.product_id.id == move.product_id.id])
        if float_compare(quantity, 0, precision_digits=precision) <= 0:
            return False
        return self.env['stock.move'].with_context(
                product_qty=quantity,
                order_production_id=production.id,
                procurement_autorun_defer=True
        )._create_procurements(move)

    def _resolve_move_to_consume(self, production):
        """This function to resolve Raw Material is not enough to consume for this Production
        :param production - This is Production to resolve
        :return picking_ids - List of Stock Operation
        """
        listPrevMove = []
        for move in production.move_lines.filtered(
            lambda x: x.state in ['confirmed', 'waiting']
        ):

            prevMove, remaining_qty = self._create_prev_stock_move_for(move, production)
            listPrevMove += prevMove
            if self.env['mrp.config.settings'].get_auto_make_procurement():
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                if float_compare(
                        remaining_qty, 0,
                        precision_digits=precision) > 0:
                    self._make_procurement_to_consume(production, move, remaining_qty, precision)

            # Push move to waiting state if move has original move
            if len([m for m in move.move_orig_ids if m.state not in ('cancel', 'done')]) > 0:
                move.write({'state': 'waiting'})
            else:
                move.write({'state': 'confirmed'})
            if prevMove:
                move.write({'state': 'waiting'})
        return self._create_stock_operations(listPrevMove, production)

    @api.multi
    def _make_stock_operations(self):
        for production in self:
            if production.state != 'ready':
                production.server_procurement_ids.filtered(
                    lambda x: x.state in ('confirmed', 'exception')
                ).run()
                self._resolve_move_to_consume(production)
        return True

    @api.multi
    def action_assign(self):
        """Override action_assign in module mrp to push a context and call some function"""
        _waiting_available = []
        for prod in self:
            if prod.state in ('confirmed', 'in_production'):
                _waiting_available.append(prod.id)
            elif prod.state == 'ready':
                if not prod.test_ready():
                    prod.signal_workflow('button_unreserve')
        _waiting_available = self.browse(_waiting_available)
        result = super(
                nppMrpProduction,
                _waiting_available.with_context(actionAssignManufacturingOrder=True)
        ).action_assign()
        if self.env.context.get('auto_make_stock_operations', False)\
                and self.env['mrp.config.settings'].get_auto_make_stock_operation():
            _waiting_available._make_stock_operations()

        return result

    @api.model
    def _make_consume_line_from_data(self, production, product, uom_id, qty):
        move_id = super(nppMrpProduction, self)._make_consume_line_from_data(
                production, product, uom_id, qty
        )
        move = self.env['stock.move'].browse(move_id)
        vals = {'name': production.name + ': ' + move.name}
        location_id = self.env.context.get('location_id', False)
        if location_id:
            vals.update({'location_id': location_id})
        move.write(vals)
        return move_id

    @api.model
    def _make_production_consume_line(self, line):
        return super(
                nppMrpProduction, self.with_context(
                        location_id=line.bom_line_id.location_id.id)
        )._make_production_consume_line(line)

    @api.multi
    def action_view_pickings(self):
        self.ensure_one()
        return {
            'name': 'Stock Operations',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', self.picking_ids.ids)],
            # 'target': 'new',
        }

    @api.multi
    def action_view_procurements(self):
        self.ensure_one()
        return {
            'name': 'Procurement Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'procurement.order',
            'view_type': 'form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', self.server_procurement_ids.ids)]
        }

    @api.multi
    def action_cancel(self):
        # Todo: If MO is cancelled, all Stock Operations for this MO will be cancel
        for production in self:

            self.env['stock.picking'].browse(
                [p.id for p in production.picking_ids if p.state not in ('cancel', 'done')]
            ).action_cancel()
            self.env['procurement.order'].browse(
                [p.id for p in production.server_procurement_ids if p.state not in ('done', 'cancel')]
            ).cancel()

        res = super(nppMrpProduction, self).action_cancel()
        return res


class nppMrpBom(models.Model):
    _inherit = 'mrp.bom'

    def _build_product_line_vals(self, bom_line_id, workcenter_line_id,
                                 quantity, product_uos_qty):
        vals = super(nppMrpBom, self)._build_product_line_vals(
            bom_line_id,
            workcenter_line_id,
            quantity, product_uos_qty)
        vals.update(bom_line_id=bom_line_id.id)
        return vals


class nppMrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    location_id = fields.Many2one(comodel_name='stock.location', string='Source Location')


class nppProductionProductLine(models.Model):
    _inherit = 'mrp.production.product.line'

    bom_line_id = fields.Many2one(
        comodel_name='mrp.bom.line',
        string='Bill of Material Line'
    )
