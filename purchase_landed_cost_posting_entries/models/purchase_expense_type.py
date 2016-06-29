# __author__ = 'trananhdung'

from openerp import fields, models


class nppPurchaseExpenseType(models.Model):
    _inherit = 'purchase.expense.type'

    calculation_method = fields.Selection(
        [('amount', 'By amount of the line'),
         ('percent', 'Percentage by PO line'),
         ('price', 'By product price'),
         ('qty', 'By product quantity'),
         ('weight', 'By product weight'),
         ('weight_net', 'By product weight net'),
         ('volume', 'By product volume'),
         ('equal', 'Equally to all lines')], string='Calculation method',
        default='amount')

    default_percent_amount = fields.Float(string='Default Percentage',
                                          default=0.00)
    default_account_id = fields.Many2one(comodel_name='account.account',
                                         string='Default Expense Account')
