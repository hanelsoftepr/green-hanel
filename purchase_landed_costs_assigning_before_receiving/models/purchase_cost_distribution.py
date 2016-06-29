__author__ = 'trananhdung'

from openerp import fields, models, api
from openerp.api import Environment
from openerp import SUPERUSER_ID
from threading import Thread
from datetime import datetime, time
from openerp.http import request
import logging

_logger = logging.getLogger(__name__)


class nppPurchaseCostDistributionExpense(models.Model):
    _inherit = 'purchase.cost.distribution.expense'

    picking_id = fields.Many2one(comodel_name='stock.picking',
                                 string='Incoming Shipment')
    distribution = fields.Many2one(required=False)


class nppPurchaseCostDistributionLine(models.Model):
    _inherit = 'purchase.cost.distribution.line'

    state = fields.Selection(
        selection=[('new', 'New'),
                   ('wait', 'Waiting for Transfer'),
                   ('ready', 'Ready'),
                   ('done', 'Done')],
        string='Status',
        default='new'
    )


class nppPurchaseCostDistrbution(models.Model):
    _inherit = 'purchase.cost.distribution'

    state = fields.Selection(
        [('draft', 'Draft'),
         ('calculated', 'Calculated'),
         ('partially', 'Partially Done'),
         ('done', 'Done'),
         ('error', 'Error'),
         ('cancel', 'Cancel')], string='Status', readonly=True,
        default='draft')

    # Override function _calculate_cost
    @api.one
    def _calculate_cost(self, line):
        if line.state != 'done':
            super(nppPurchaseCostDistrbution, self)._calculate_cost(line)
            if line.picking_id.state == 'done':
                line.write({'state': 'ready'})
            else:
                line.write({'state': 'wait'})
        else:
            return

    @api.multi
    def sub_thread_create_accounting_entries(self, move_id, cost_line):
        with Environment.manage():
            new_env = Environment(self.pool.cursor(),
                                  self.env.uid,
                                  self.env.context
                                  )
            self.env.cr.commit()
            this = self.with_env(env=new_env).browse(self.ids)
            this._create_accounting_entries(move_id, cost_line)
            this.env.cr.commit()
            this.env.cr.close()

    @api.multi
    def run_subthread(self, move_id, cost_line):
        # self.env.cr.commit()
        sub_thread = Thread(
                target=self.sub_thread_create_accounting_entries,
                args=(move_id, cost_line)
        )
        sub_thread.daemon = True
        sub_thread.start()

    @api.model
    def run_create_accounting_entries(self):
        with Environment.manage():
            new_env = Environment(self.pool.cursor(),
                                  self.env.uid,
                                  self.env.context)
            self.env.cr.commit()

            this = self.with_env(env=new_env).browse(self.env.context.get('active_id', []))
            move_id = this._create_account_move()
            _logger.info("Start create account entries for Purchase Cost Distribution"
                         " at %s" % (datetime.now().time().strftime("%H:%M:%S")))
            cost_lines = this.cost_lines.browse(self.env.context.get('cost_lines', False))
            for cost_line in cost_lines:
                # Create Accounting Entries
                this._create_accounting_entries(move_id, cost_line)
            # this.run_subthread(move_id, cost_lines[0])

            _logger.info("Finish create account entries for Purchase Cost Distribution"
                         " at %s" % (datetime.now().time().strftime("%H:%M:%S")))
            new_env.cr.commit()
            new_env.cr.close()

    @api.model
    def _create_thread_posting_accounting_entries(self):
        run_thread = Thread(target=self.run_create_accounting_entries)
        run_thread.daemon = True
        run_thread.start()

    # Override function action_done
    @api.one
    def action_done(self):
        change_line_ids = []
        picking_id = self.env.context.get('forPickingID', False)
        for line in self.cost_lines:
            if line.state == 'ready' and \
                    (not picking_id or (picking_id and line.picking_id.id == picking_id)
                     ):
                change_line_ids.append(line.id)
                if self.cost_update_type == 'direct':
                    line.move_id.quant_ids._price_update(line.standard_price_new)
                    self._product_price_update(line)
                    line.move_id.product_price_update_after_done()
                line.write({'state': 'done'})
        if change_line_ids:
            change_line_ids = self.env['purchase.cost.distribution.line'].browse(change_line_ids)
            if self.env['purchase.config.settings'].distribution_background:
                self.with_context(
                    cost_lines=change_line_ids,
                    active_id=self.id
                )._create_thread_posting_accounting_entries()
            else:
                move_id = self._create_account_move()
                for cost_line in change_line_ids:
                    self._create_accounting_entries(move_id, cost_line)

        if len(self.cost_lines) == len(
            self.cost_lines.filtered(lambda x: x.state == 'done')
        ):
            self.state = 'done'
        elif len(self.cost_lines) == len(
            self.cost_lines.filtered(lambda x: x.state != 'done')
        ):
            self.state = 'calculated'
        else:
            self.state = 'partially'
