# __author__ = 'trananhdung'

from openerp import models, api, fields


class NppMrpConfigSettings(models.Model):
    _inherit = 'mrp.config.settings'

    @api.model
    def get_default_auto_make_stock_operation(self, fields):
        value = eval(self.env.ref('mrp_stock_operations.npp_default_auto_make_stock_operation_value').value)
        return {'auto_make_stock_operation': value}

    @api.model
    def get_auto_make_stock_operation(self):
        return eval(self.env.ref('mrp_stock_operations.npp_default_auto_make_stock_operation_value').value)

    @api.multi
    def set_auto_make_stock_operation(self):
        self.ensure_one()
        self.env.ref('mrp_stock_operations.npp_default_auto_make_stock_operation_value').write({
            'value': str(self.auto_make_stock_operation)
        })
        if not self.auto_make_stock_operation:
            self.env.ref('mrp_stock_operations.npp_default_auto_make_procurement_value').write({
                'value': 'False'
            })

    @api.model
    def get_default_auto_make_procurement(self, fields):
        value = eval(self.env.ref('mrp_stock_operations.npp_default_auto_make_procurement_value').value)
        return {'auto_make_procurement': value}

    @api.model
    def get_auto_make_procurement(self):
        return eval(self.env.ref('mrp_stock_operations.npp_default_auto_make_procurement_value').value)

    @api.multi
    def set_auto_make_procurement(self):
        self.ensure_one()
        self.env.ref('mrp_stock_operations.npp_default_auto_make_procurement_value').write({
            'value': str(self.auto_make_procurement)
        })

    auto_make_stock_operation = fields.Boolean(
        string='Automatically resolving by Internal Transfers',
        help='Allow automatically create Internal Transfers to '
             'resolve shortage of Raw Material in Raw Material Location')
    auto_make_procurement = fields.Boolean(
        string='Automatically resolving by Procurement Order',
        help='Allow automatically create Procurement Order when '
             'Raw Material is not enough in all Locations')

    @api.onchange('auto_make_stock_operation')
    def onchange_auto_make_stock_operation(self):
        if not self.auto_make_stock_operation:
            self.auto_make_procurement = False
