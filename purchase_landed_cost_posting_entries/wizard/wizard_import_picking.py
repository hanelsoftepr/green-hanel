# __author__ = 'trananhdung'

from openerp import models, fields


class NppPickingImportWizard(models.TransientModel):
    _inherit = "picking.import.wizard"

    supplier = fields.Many2one(
        comodel_name='res.partner', string='Supplier', required=False,
        domain="[('supplier',  '=', True)]")
