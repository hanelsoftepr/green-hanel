# __author__ = 'trananhdung'

from openerp import models, api, fields


class npp_account_journal(models.Model):
    _inherit = 'account.journal'

    default_cost_distribution = fields.Boolean(string='Default for Cost Distributions',
                                               help='Use Default for Purchase Cost Distributions')
    use_cost_distribution = fields.Boolean(string='Use for Cost Distributions',
                                           help='Check this to use this Journal for Purchase Cost Distributions')

    @api.multi
    @api.onchange('default_cost_distribution')
    def onchange_default_cost_distribution(self):
        for r in self:
            if r.default_cost_distribution:
                r.use_cost_distribution = True
        return

    @api.model
    def _make_only_cost_distribution_journal(self, journal):
        if not journal.default_cost_distribution:
            return
        journals_cost_distribution = self.search([('default_cost_distribution', '=', True), ('id', '!=', journal.id)])
        journals_cost_distribution.write({'default_cost_distribution': False,
                                          'use_cost_distribution': True})

    def _prepare_vals(self, vals):
        if vals.get('default_cost_distribution', False):
            vals.update({'use_cost_distribution': True})

    @api.model
    def create(self, vals):
        self._prepare_vals(vals)
        _object = super(npp_account_journal, self).create(vals)
        self._make_only_cost_distribution_journal(_object)
        return _object

    @api.multi
    def write(self, vals):
        self._prepare_vals(vals)
        _result = super(npp_account_journal, self).write(vals)
        if vals.get('default_cost_distribution', False):
            self._make_only_cost_distribution_journal(self[-1])
        return _result
