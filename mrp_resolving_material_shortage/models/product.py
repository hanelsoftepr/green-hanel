__author__ = 'trananhdung'

# from openerp import models, fields, api
# from openerp.addons.decimal_precision import decimal_precision as dp
#
#
# class nppProductProduct(models.Model):
#     _inherit = 'product.product'
#
#     @api.multi
#     def _get_usable_qty(self):
#         product_ids = [p.id for p in self]
#         quantLocationDomain, _, _ = self._get_domain_locations()
#         quantLocationDomain = [('product_id', 'in', product_ids)] + quantLocationDomain + \
#                               [('reservation_id', '=', False)]
#         quants = self.env['stock.quant'].read_group(domain=quantLocationDomain, fields=['id', 'product_id', 'qty'], groupby=['product_id'])
#         quant_keep = self.env['stock.quant.keep']
#         usable_qty = {}
#         for quant in quants:
#             usable_qty[quant['product_id'][0]] = quant['qty']
#         for product in self:
#             keep = quant_keep.search([('move_id', '!=', False),
#                                       ('product_id', '=', product.id)])
#             qty = 0.00
#             if product.id in usable_qty:
#                 qty = usable_qty[product.id]
#             if len(keep) > 0:
#                 qty = qty - sum([x.qty for x in keep])
#             product.qty_usable = qty
#
#     # Todo: Waiting for Customer confirm
#     # prepare_location_id = fields.Many2one(
#     #     comodel_name='stock.location', string='Prepare Location'
#     # )
#
#     qty_usable = fields.Float(string='Usable Quantity',
#                               compute='_get_usable_qty',
#                               digits=dp.get_precision('Product Unit of Measure'))
