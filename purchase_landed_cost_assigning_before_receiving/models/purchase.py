__author__ = 'trananhdung'

from openerp import models, fields, api


class nppPurchase(models.Model):
    _inherit = 'purchase.order'

    landed_cost = fields.Boolean(string='Landed Cost', default=False)

    @api.multi
    def wkf_confirm_order(self):
        return super(
            nppPurchase, self.with_context(
                nppConfirmPurchaseOrder=True)
        ).wkf_confirm_order()

    @api.multi
    def action_picking_create(self):
        for order in self:
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'origin': order.name,
                'landed_cost': order.landed_cost
            }
            picking_id = self.env['stock.picking'].create(picking_vals)
            self._create_stock_moves(order, order.order_line, picking_id.id)
        return picking_id

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(nppPurchase, self).onchange_partner_id(partner_id)
        landed_cost = self.env['res.partner'].browse(partner_id).landed_cost
        res['value'].update({'landed_cost': landed_cost})
        return res
