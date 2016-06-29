# __author__ = 'trananhdung'

from openerp import models, fields, api


class NppPurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    @api.model
    def get_default_distribution_background(self, fields):
        value = eval(self.env.ref('purchase_landed_cost_posting_entries.npp_cost_distribution_config').value)
        return {'distribution_background': value}

    @api.model
    def get_distribution_background(self):
        value = eval(self.env.ref('purchase_landed_cost_posting_entries.npp_cost_distribution_config').value)
        return value

    @api.multi
    def set_distribution_background(self):
        self.ensure_one()
        self.env.ref('purchase_landed_cost_posting_entries.npp_cost_distribution_config').write({
            'value': str(self.distribution_background)
        })

    distribution_background = fields.Boolean(string='Run Cost Distribution in Background')
