__author__ = 'trananhdung'

from openerp import fields, models, api
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class reposting_account_entries_wizad(models.TransientModel):
    _name = 'reposting.account.entries.wizard'
    _description = 'Posting Account Entries for Purchase Cost Distribution'

    cost_distribution_id = fields.Many2one(
        comodel_name='purchase.cost.distribution',
        string='Purchase Cost Distribution to Posting Journal Entries'
    )

    @api.multi
    def action_reporting_account_entries(self):
        self.ensure_one()
        this = self.cost_distribution_id
        move_id = this._create_account_move()
        _logger.info("Start create account entries for Purchase Cost Distribution"
                     " at %s" % (datetime.now().time().strftime("%H:%M:%S")))

        for cost_line in this.cost_lines:
            # Create Accounting Entries
            if cost_line.state == 'done':
                this.with_context(reposting_account=True)._create_accounting_entries(move_id, cost_line)
        # this.run_subthread(move_id, cost_lines[0])

        _logger.info("Finish create account entries for Purchase Cost Distribution"
                     " at %s" % (datetime.now().time().strftime("%H:%M:%S")))
