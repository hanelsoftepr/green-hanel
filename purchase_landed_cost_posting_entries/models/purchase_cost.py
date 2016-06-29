# __author__ = 'trananhdung'

from openerp import fields, models, api, exceptions
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from openerp.api import Environment
from threading import Thread
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class nppPurchaseCostDistrbutionExpense(models.Model):
    _inherit = 'purchase.cost.distribution.expense'

    account_id = fields.Many2one(comodel_name='account.account', string='Expense Account')
    expense_percent_amount = fields.Float(string='Percentage by PO line')

    @api.onchange('type')
    def onchange_type(self):
        self.ensure_one()
        super(nppPurchaseCostDistrbutionExpense, self).onchange_type()
        self.expense_percent_amount = self.type.default_percent_amount
        self.account_id = self.type.default_account_id


class nppPurchaseCostDistribution(models.Model):
    _inherit = 'purchase.cost.distribution'

    @api.multi
    @api.depends('cost_lines', 'cost_lines.expense_amount')
    def _compute_total_expense(self):
        for r in self:
            r.total_expense = sum([x.expense_amount for x in r.cost_lines])

    @api.model
    def _get_default_journal(self):
        _default_journal = self.env['account.journal'].search([('default_cost_distribution', '=', True)], limit=1)
        if _default_journal:
            return _default_journal

    account_journal_id = fields.Many2one(
        comodel_name='account.journal', string='Journal', required=True,
        default=_get_default_journal, domain=[('use_cost_distribution', '=', True)]
    )
    total_expense = fields.Float(compute=_compute_total_expense)

    @api.multi
    def _get_account_move_vals(self):
        return {
            'journal_id': self.account_journal_id.id,
            'period_id': self.env['account.period'].find(self.date)[0].id,
            'date': self.date,
            'ref': 'PCD:' + self.name
        }
        # return vals

    @api.multi
    def _create_account_move(self):
        self.ensure_one()
        vals = self._get_account_move_vals()
        return self.env['account.move'].create(vals)

    def _get_quantity_out(self, line):
        qty_out = 0.00
        for quant in line.move_id.quant_ids:
            if quant.location_id.usage != 'internal':
                qty_out += quant.qty
        return qty_out

    def _create_account_move_line(self, line, move_id, accounts, qty_out):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        debit_account_id = accounts['debit_account']
        credit_account_id = accounts['credit_account']
        already_out_account_id = accounts['out_account']
        amlModel = self.env['account.move.line']
        base_line = {
            'name': line.product_id.name,
            'origin':
                line.move_id.origin + '/' +
                line.move_id.location_id.name + ' > ' +
                line.move_id.location_dest_id.name,
            'move_id': move_id.id,
            'product_id': line.product_id.id,
            'quantity': line.product_qty,
        }
        for expense_line in line.expense_lines:
            credit_account_id = expense_line.distribution_expense.account_id.id\
                                or credit_account_id
            name = base_line['name']
            debit_line = dict(
                base_line,
                account_id=debit_account_id,
                name=name + ' (' + expense_line.distribution_expense.type.name + ')'
            )
            credit_line = dict(
                base_line,
                account_id=credit_account_id,
                name=name + ' (' + expense_line.distribution_expense.type.name + ')'
            )
            diff = expense_line.expense_amount
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            amlModel.create(debit_line)
            amlModel.create(credit_line)
            _logger.info("Created a couple of Account Move Line for Journal Entry!")

            # Create account move lines for quants already out of stock
            if qty_out > 0 and not self.env.context.get('reposting_account', False):
                debit_line = dict(
                    debit_line,
                    name=(line.name + ": " + str(qty_out) + _(' already out')),
                    quantity=qty_out,
                    account_id=already_out_account_id
                )
                credit_line = dict(
                    credit_line,
                    name=(line.name + ": " + str(qty_out) + _(' already out')),
                    quantity=qty_out,
                    account_id=debit_account_id
                )
                diff = diff * qty_out / line.product_qty
                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                amlModel.create(debit_line)
                amlModel.create(credit_line)
        return True

    @api.multi
    def _create_accounting_entries(self, move_id, line):
        accounts = self.env['product.template']\
            .get_product_accounts(line.product_id.product_tmpl_id.id)
        debit_account_id = accounts['property_stock_valuation_account_id']
        already_out_account_id = accounts['stock_account_output']
        credit_account_id = line.product_id.property_account_expense.id \
            or line.product_id.categ_id.property_account_expense_categ.id
        if not debit_account_id:
            raise ValidationError('Valuation Account or Expense Account is not set.')
        accounts = {}
        accounts.clear()
        accounts.update(
            credit_account=credit_account_id,
            debit_account=debit_account_id,
            out_account=already_out_account_id
        )
        qty_out = self._get_quantity_out(line)

        return self._create_account_move_line(line, move_id, accounts, qty_out)

    @api.one
    def action_done(self):
        for line in self.cost_lines:
            if self.cost_update_type == 'direct':
                line.move_id.quant_ids._price_update(line.standard_price_new)
                self._product_price_update(line)
                line.move_id.product_price_update_after_done()
        self.write({'state': 'done'})
        if self.env['purchase.config.settings'].get_distribution_background():
            self._create_thread_posting_accounting_entries()
        else:
            move_id = self._create_account_move()
            for cost_line in self.cost_lines:
                self._create_accounting_entries(move_id, cost_line)

    @api.one
    def _create_thread_posting_accounting_entries(self):
        run_thread = Thread(target=self.run_create_accounting_entries)
        run_thread.daemon = True
        run_thread.start()

    # @api.model
    # def run_create_accounting_entries(self, cost_lines):
    #     move_id = self._create_account_move()
    #     _logger.info("Start create account entries for Purchase Cost Distribution"
    #                  " at %s" % (datetime.now().time().strftime("%H:%M:%S")))
    #     for cost_line in cost_lines:
    #         # Create Accounting Entries
    #
    #         self._create_accounting_entries(move_id, cost_line)
    #     _logger.info("Finish create account entries for Purchase Cost Distribution"
    #                  " at %s" % (datetime.now().time().strftime("%H:%M:%S")))

    @api.one
    def run_create_accounting_entries(self):
        with Environment.manage():
            new_env = Environment(self.pool.cursor(),
                                  self.env.uid,
                                  self.env.context)
            self.env.cr.commit()
            this = self.with_env(env=new_env)
            move_id = this._create_account_move()
            _logger.info("Start create account entries for Purchase Cost Distribution"
                         " at %s" % (datetime.now().time().strftime("%H:%M:%S")))
            for cost_line in this.cost_lines:
                # Create Accounting Entries
                this._create_accounting_entries(move_id, cost_line)

            _logger.info("Finish create account entries for Purchase Cost Distribution"
                         " at %s" % (datetime.now().time().strftime("%H:%M:%S")))
            new_env.cr.commit()
            new_env.cr.close()

    @api.one
    def _calculate_cost(self, line):
        distribution = self
        line.expense_lines.unlink()
        expense_lines = []
        for expense in distribution.expense_lines:
            if (expense.affected_lines and
                    line.id not in expense.affected_lines.ids):
                continue
            if expense.type.calculation_method == 'amount':
                multiplier = line.total_amount
                if expense.affected_lines:
                    divisor = sum([x.total_amount for x in
                                   expense.affected_lines])
                else:
                    divisor = distribution.total_purchase
            elif expense.type.calculation_method == 'percent':
                pass
            elif expense.type.calculation_method == 'price':
                multiplier = line.product_price_unit
                if expense.affected_lines:
                    divisor = sum([x.product_price_unit for x in
                                   expense.affected_lines])
                else:
                    divisor = distribution.total_price_unit
            elif expense.type.calculation_method == 'qty':
                multiplier = line.product_qty
                if expense.affected_lines:
                    divisor = sum([x.product_qty for x in
                                   expense.affected_lines])
                else:
                    divisor = distribution.total_uom_qty
            elif expense.type.calculation_method == 'weight':
                multiplier = line.total_weight
                if expense.affected_lines:
                    divisor = sum([x.total_weight for x in
                                   expense.affected_lines])
                else:
                    divisor = distribution.total_weight
            elif expense.type.calculation_method == 'weight_net':
                multiplier = line.total_weight_net
                if expense.affected_lines:
                    divisor = sum([x.total_weight_net for x in
                                   expense.affected_lines])
                else:
                    divisor = distribution.total_weight_net
            elif expense.type.calculation_method == 'volume':
                multiplier = line.total_volume
                if expense.affected_lines:
                    divisor = sum([x.total_volume for x in
                                   expense.affected_lines])
                else:
                    divisor = distribution.total_volume
            elif expense.type.calculation_method == 'equal':
                multiplier = 1
                divisor = (len(expense.affected_lines) or
                           len(distribution.cost_lines))
            else:
                raise exceptions.Warning(
                    _('No valid distribution type.'))
            if expense.type.calculation_method == 'percent':
                expense_amount = (expense.expense_percent_amount * line.total_amount) / 100
            else:
                try:
                    expense_amount = (expense.expense_amount * multiplier / divisor)
                except:
                    raise ValidationError('Cannot compute expense amount for this case!')

            expense_line = {
                'distribution_expense': expense.id,
                'expense_amount': expense_amount,
                'cost_ratio': expense_amount / line.product_qty,
            }
            expense_lines += [(0, 0, expense_line)]
        line.write({'expense_lines': expense_lines})

    @api.multi
    def action_calculate(self):
        for distribution in self:
            # Check expense lines for amount 0
            if any([(not x.expense_amount and x.calculation_method != 'percent') or
                    (not x.expense_percent_amount and x.calculation_method == 'percent')
                    for x in distribution.expense_lines]):
                raise exceptions.Warning(
                    _('Please enter an amount for all the expenses'))
            # Check if exist lines in distribution
            if not distribution.cost_lines:
                raise exceptions.Warning(
                    _('There is no picking lines in the distribution'))
            # Calculating expense line
            for line in distribution.cost_lines:
                distribution._calculate_cost(line)
            distribution.state = 'calculated'
        return True

    def _compute_new_standard_price(self, product_template, move, cost_ratio):
        # FIXME: Compute Standard price for other cost method
        total_value = product_template.standard_price * product_template.qty_available\
                      + cost_ratio * move.product_qty
        new_price = total_value / product_template.qty_available
        return new_price

    def _product_price_update(self, line):
        """Method that mimicks stock.move's product_price_update_before_done
        method behaviour, but taking into account that calculations are made
        on an already done move, and prices sources are given as parameters.
        """
        move, new_price = line.move_id, line.standard_price_new
        if (move.location_id.usage == 'supplier' and
                move.product_id.cost_method == 'average'):
            product = move.product_id
            product_tmpl = product.product_tmpl_id
            qty_available = product_tmpl.qty_available
            product_avail = qty_available - move.product_qty
            if product_avail <= 0:
                new_std_price = new_price
            else:
                # Get the standard price
                new_std_price = self._compute_new_standard_price(
                    product_tmpl, move, line.cost_ratio)
            # Write the standard price, as SUPERUSER_ID, because a
            # warehouse manager may not have the right to write on products
            # TODO: create group for manage expense cost to do following:
            product.sudo().write({'standard_price': new_std_price})


