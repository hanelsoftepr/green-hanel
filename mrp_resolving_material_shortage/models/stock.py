__author__ = 'trananhdung'

from openerp import models, fields, api
from openerp.tools import float_compare, float_is_zero
# from openerp.addons.decimal_precision import decimal_precision as dp


class nppProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    order_production_id = fields.Many2one(comodel_name='mrp.production',
                                          string='for Production')


class nppStockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends('product_id', 'product_qty', 'state')
    def _get_available_location(self):
        quantModel = self.env['stock.quant']
        locations = self.env['stock.location'].search([('usage', '=', 'internal')])
        for move in self:
            if move.state in ['assigned', 'done', 'cancel']:
                continue

            availableLocations = []
            for location in locations:
                if move.product_id.with_context(
                        location=location.id).qty_usable >= move.product_qty:
                    availableLocations.append(location.id)
            move.available_location_ids = self.env['stock.location'].browse(availableLocations)

    available_location_ids = fields.Many2many(
        comodel_name='stock.location', string='Available Locations',
        compute='_get_available_location'
    )

    @api.multi
    def _trigger_assign_production(self):
        to_assign = []
        for r in self:
            if r.picking_id.production_id.id:
                to_assign.append(r.picking_id.production_id.id)
        self.env['mrp.production'].browse(list(set(to_assign))).action_assign()

    @api.multi
    def action_done(self):
        result = super(nppStockMove, self).action_done()
        self._trigger_assign_production()
        return result

    @api.model
    def _prepare_procurement_from_move(self, move):
        result = super(nppStockMove, self)._prepare_procurement_from_move(move)
        qty = self.env.context.get('product_qty', False)
        order_production_id = self.env.context.get('order_production_id', False)
        if qty:
            result.update(
                product_qty=qty,
                # product_uos_qty=(move.product_uos and move.product_uos_qty) or qty,
                order_production_id=order_production_id
            )
        return result

    @api.cr_uid_ids_context
    def do_unreserve(self, cr, uid, move_ids, context=None):
        result = super(nppStockMove, self).do_unreserve(cr, uid, move_ids, context=context)
        to_recheck_availability = []
        for move in self.browse(cr, uid, move_ids, context):
            if move.state in ('confirmed', 'waiting') and move.raw_material_production_id.id:
                to_recheck_availability.append(move.raw_material_production_id.id)
        production_ids = list(set(to_recheck_availability))
        production_model = self.pool.get('mrp.production')
        # production_model.button_unreserve(cr, uid, production_ids, context=context)
        production_model.action_assign(cr, uid, production_ids, context=context)
        return result


class nppStockLocation(models.Model):
    _inherit = 'stock.location'

    # @api.multi
    # def _get_available_qty(self):
    #     product_id = self.env['product.product'].browse(
    #         self.env.context.get('product_id', False))
    #     for loc in self:
    #         if product_id.id:
    #             loc.available_qty = product_id.with_context(
    #                 location=loc.id
    #             ).qty_usable
    #         else:
    #             loc.available_qty = None
    #
    # available_qty = fields.Float(string='Available Quantity',
    #                              compute='_get_available_qty',
    #                              digits=dp.get_precision('Product Unit of Measure'))

    @api.model
    def get_top_parent(self, location):
        if location.location_id.id:
            return self.get_top_parent(location.location_id)
        else:
            return location

    @api.model
    def get_warehouse(self, location):
        view_locations = {}
        for _wh in self.env['stock.warehouse'].search([]):
            view_locations[_wh.view_location_id.id] = _wh.id
        if isinstance(location, int):
            location = self.browse(location)
        wh = False
        while location.id:
            location = location.location_id
            wh = view_locations.get(location.id, False)
            if wh:
                break
        return wh

        # return super(nppStockLocation, self).get_warehouse(location)

    @api.multi
    def get_view_location_warehouse(self):
        """Function to return view location contain input location
        @param self: location need to know who is ancestor :)
        @return: view_location_id - ID of view location contain input location
        """
        self.ensure_one()
        location = self
        warehouses = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.user.company_id.id)]
        )
        view_locations = self.env['stock.location'].browse([w.view_location_id.id for w in warehouses])
        view_location = view_locations.filtered(
                lambda x: x.parent_left < location.parent_left and x.parent_right > location.parent_right
        )
        if view_location:
            return view_location[0].id
        else:
            return False


class nppStockPicking(models.Model):
    _inherit = 'stock.picking'

    production_id = fields.Many2one(comodel_name='mrp.production',
                                    string='For Production',
                                    copy=False)

    @api.multi
    def action_done(self):
        result = super(nppStockPicking, self).action_done()
        for picking in self:
            if picking.production_id.id:
                picking.production_id.action_assign()
        return result

    @api.model
    def _create_backorder(self, picking, backorder_moves=[]):
        backorder_id = super(
                nppStockPicking, self
        )._create_backorder(picking, backorder_moves)
        self.browse(backorder_id).write({
            'production_id': picking.production_id.id
        })
        return backorder_id


class npp_stock_return_picking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        """
            Override _create_return function to copy production_id
            of Stock Operation to Return Transfer of it

            :return new_picking - ID of Stock Operation of Refund
            :return picking_type_id - ID of picking type of warehouse
        """
        new_picking, picking_type_id = super(npp_stock_return_picking, self)._create_returns()
        picking_model = self.env['stock.picking']
        picking = picking_model.browse(self.env.context.get('active_id', []))
        picking_model.browse(new_picking).write({
            'production_id': picking.production_id.id
        })
        return new_picking, picking_type_id


class NppStockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _quants_get_order(self, quantity, move, ops=False, domain=[], orderby='in_date'):
        """ Override odoo base function in module: stock

        """
        params = {
            'quantity': quantity,
            'move': move,
            'ops': ops,
            'domain': domain,
            'orderby': orderby
        }
        if move._name == 'stock.move':
            return super(NppStockQuant, self)._quants_get_order(**params)
        else:
            del params['move']
            del params['ops']
            params['product'] = move
            return self._quants_get_order_all_locations(**params)

    @api.model
    def _quants_get_order_all_locations(self, quantity, product, domain=[], orderby='in_date'):
        domain += [('product_id', '=', product.id)]
        if self.env.context.get('force_company'):
            domain += [('company_id', '=', self.env.context.get('force_company'))]
        else:
            domain += [('company_id', '=', self.env.user.company_id.id)]
        res = []
        offset = 0
        while float_compare(quantity, 0, precision_rounding=product.uom_id.rounding) > 0:
            quants = self.search(domain, order=orderby, limit=10, offset=offset)
            # for quant in quants:
            #     location_id = quant.location_id.id
            #     if location_id not in _location_usable_cache:
            #         _location_usable_cache[location_id] = product.with_context(
            #             location=location_id
            #         ).qty_usable

            if not quants:
                res.append((None, quantity))
                break
            for quant in quants:
                rounding = product.uom_id.rounding
                apply_qty = quant.qty
                if float_compare(value1=apply_qty, value2=0, precision_rounding=rounding) <= 0:
                    continue
                res += [(quant, apply_qty)]
                quantity -= apply_qty
                if float_is_zero(quantity, precision_rounding=rounding):
                    break

            offset += 10
        return res
