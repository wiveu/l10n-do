from copy import deepcopy
from datetime import timedelta
import json
from uuid import uuid4
from unittest.mock import patch

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestFiscalPosInvoicing(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id |= cls.env.ref('point_of_sale.group_pos_manager')
        cls.company = cls.env.company
        cls.sale_journal = cls.company_data['default_journal_sale']
        cls.sale_journal.l10n_do_fiscal_journal = True
        cls.fiscal_type = cls.env.ref('l10n_do_ncf.fiscal_type_consumo')
        cls.sequence = cls.env['account.fiscal.sequence'].create({
            'name': 'POS regression authorization', 'company_id': cls.company.id,
            'fiscal_type_id': cls.fiscal_type.id, 'state': 'active',
            'sequence_start': 1, 'sequence_end': 999, 'number_next_actual': 80,
            'expiration_date': fields.Date.today() + timedelta(days=30),
        })
        cls.pos_receivable = cls.env['account.account'].create({
            'name': 'POS clearing regression', 'code': 'POSREC',
            'account_type': 'asset_receivable', 'reconcile': True,
            'company_ids': [(6, 0, cls.company.ids)],
        })
        cls.company.account_default_pos_receivable_account_id = cls.pos_receivable
        cls.pay_later = cls.env['pos.payment.method'].create({
            'name': 'Customer account regression', 'split_transactions': True,
            'receivable_account_id': cls.company_data['default_account_receivable'].id,
        })
        cls.cash_journal = cls.env['account.journal'].create({
            'name': 'Cash regression', 'code': 'PCSH', 'type': 'cash',
            'company_id': cls.company.id,
        })
        cls.bank_journal = cls.env['account.journal'].create({
            'name': 'Bank regression', 'code': 'PBNK', 'type': 'bank',
            'company_id': cls.company.id,
        })
        for journal in cls.cash_journal | cls.bank_journal:
            journal.inbound_payment_method_line_ids.payment_account_id = journal.default_account_id
        cls.cash = cls.env['pos.payment.method'].create({
            'name': 'Cash regression', 'journal_id': cls.cash_journal.id,
            'receivable_account_id': cls.pos_receivable.id,
        })
        cls.bank = cls.env['pos.payment.method'].create({
            'name': 'Bank regression', 'journal_id': cls.bank_journal.id,
            'receivable_account_id': cls.pos_receivable.id,
        })
        cls.identified_bank = cls.bank.copy({'name': 'Identified bank regression',
                                             'split_transactions': True})
        cls.config = cls.env['pos.config'].create({
            'name': 'Fiscal invoicing regression', 'journal_id': cls.sale_journal.id,
            'invoice_journal_id': cls.sale_journal.id, 'cash_control': False,
            'pos_partner_id': cls.partner_b.id,
            'payment_method_ids': [(6, 0, (cls.pay_later | cls.cash | cls.bank | cls.identified_bank).ids)],
        })
        cls.session = cls.env['pos.session'].create({'config_id': cls.config.id})
        cls.tax = cls.env['account.tax'].create({
            'name': 'POS tax regression', 'amount': 18, 'amount_type': 'percent',
            'type_tax_use': 'sale', 'company_id': cls.company.id,
        })
        (cls.tax.invoice_repartition_line_ids | cls.tax.refund_repartition_line_ids).filtered(
            lambda line: line.repartition_type == 'tax').account_id = cls.company_data['default_account_tax_sale']
        cls.product = cls.env['product.product'].create({
            'name': 'POS service regression', 'type': 'service', 'list_price': 100,
            'property_account_income_id': cls.company_data['default_account_revenue'].id,
            'taxes_id': [(6, 0, cls.tax.ids)],
        })

    def order_data(self, method=None, fiscal_type=None, sequence=None, reserve=True, **values):
        fiscal_type = fiscal_type or self.fiscal_type
        sequence = sequence or self.sequence
        operation = str(uuid4())
        reservation = self.env['pos.order']._get_next_fiscal_sequence(
            fiscal_type.id, self.company.id, [],
            json.dumps({'uuid': operation, 'session_id': self.session.id})) if reserve else {'ncf': False}
        return {
            'uuid': operation, 'name': 'Order ' + operation,
            'session_id': self.session.id, 'user_id': self.env.uid,
            'partner_id': self.partner_a.id, 'state': 'paid', 'to_invoice': False,
            'amount_total': 118, 'amount_tax': 18, 'amount_paid': 118, 'amount_return': 0,
            'ncf': reservation['ncf'], 'fiscal_type_id': fiscal_type.id,
            'fiscal_sequence_id': sequence.id,
            'ncf_expiration_date': sequence.expiration_date,
            'lines': [(0, 0, {'product_id': self.product.id, 'qty': 1, 'price_unit': 100,
                             'tax_ids': [(6, 0, self.tax.ids)],
                             'price_subtotal': 100, 'price_subtotal_incl': 118})],
            'payment_ids': [(0, 0, {'amount': 118,
                                   'payment_method_id': (method or self.pay_later).id})],
            **values,
        }

    def sync(self, data):
        result = self.env['pos.order'].with_context(generate_pdf=False).sync_from_ui(deepcopy(data))
        return self.env['pos.order'].browse(result['pos.order'][0]['id'])

    def test_fiscal_sync_invoices_without_checkbox_and_retries_once(self):
        data = self.order_data()
        counter = self.sequence.number_next_actual
        order = self.sync([data])
        self.assertEqual(order.state, 'invoiced')
        self.assertEqual(order.account_move.state, 'posted')
        self.assertEqual(order.account_move.ref, data['ncf'])
        self.assertEqual(order.account_move.amount_total, 118)
        self.assertEqual(order.account_move.amount_tax, 18)
        invoice = order.account_move
        self.assertEqual(self.sync([data]), order)
        self.assertEqual(order.account_move, invoice)
        self.assertEqual(len(order.payment_ids), 1)
        self.assertEqual(self.sequence.number_next_actual, counter)

    def test_explicit_invoice_is_not_duplicated(self):
        data = self.order_data(to_invoice=True)
        order = self.sync([data])
        self.assertEqual(order.state, 'invoiced')
        self.assertEqual(self.env['account.move'].search_count([
            ('company_id', '=', self.company.id), ('ref', '=', data['ncf']),
            ('move_type', '=', 'out_invoice')]), 1)

    def test_checkout_with_pos_cashier_permissions(self):
        cashier = new_test_user(self.env, login='fiscal_pos_cashier',
            groups='base.group_user,point_of_sale.group_pos_user',
            company_id=self.company.id, company_ids=[(6, 0, self.company.ids)])
        data = self.order_data(user_id=cashier.id)
        result = self.env['pos.order'].with_user(cashier).with_context(
            generate_pdf=False).sync_from_ui([data])
        order = self.env['pos.order'].browse(result['pos.order'][0]['id'])
        self.assertEqual(order.state, 'invoiced')
        self.assertEqual(order.account_move.state, 'posted')
        self.assertEqual(order.account_move.ref, data['ncf'])

    def test_fiscal_refund_without_invoice_checkbox(self):
        original = self.sync([self.order_data()])
        fiscal_type = self.env.ref('l10n_do_ncf.fiscal_type_credit_note')
        sequence = self.env['account.fiscal.sequence'].create({
            'name': 'Refund regression authorization', 'company_id': self.company.id,
            'fiscal_type_id': fiscal_type.id, 'state': 'active',
            'sequence_start': 1, 'sequence_end': 999, 'number_next_actual': 80,
            'expiration_date': self.sequence.expiration_date,
        })
        data = self.order_data(fiscal_type=fiscal_type, sequence=sequence,
            amount_total=-118, amount_tax=-18, amount_paid=-118,
            ncf_origin_out=original.ncf,
            lines=[(0, 0, {'product_id': self.product.id, 'qty': -1, 'price_unit': 100,
                          'tax_ids': [(6, 0, self.tax.ids)],
                          'price_subtotal': -100, 'price_subtotal_incl': -118,
                          'refunded_orderline_id': original.lines.id})],
            payment_ids=[(0, 0, {'amount': -118, 'payment_method_id': self.pay_later.id})])
        refund = self.sync([data])
        self.assertEqual(refund.state, 'invoiced')
        self.assertEqual(refund.account_move.state, 'posted')
        self.assertEqual(refund.account_move.move_type, 'out_refund')
        self.assertEqual(refund.account_move.ref, data['ncf'])
        self.assertEqual(refund.account_move.amount_total, 118)

    def test_missing_customer_uses_configured_default(self):
        order = self.sync([self.order_data(partner_id=False)])
        self.assertEqual(order.partner_id, self.partner_b)
        self.assertEqual(order.account_move.partner_id, self.partner_b)
        self.assertEqual(order.account_move.state, 'posted')

    def test_missing_default_customer_rejects_checkout(self):
        self.config.pos_partner_id = False
        data = self.order_data(partner_id=False)
        with self.assertRaises(UserError), self.cr.savepoint():
            self.sync([data])
        self.assertFalse(self.env['pos.order'].search([('uuid', '=', data['uuid'])]))

    def test_draft_and_nonfiscal_orders_are_not_forced_to_invoice(self):
        draft = self.sync([self.order_data(state='draft')])
        self.assertEqual(draft.state, 'draft')
        self.assertFalse(draft.account_move)
        self.sale_journal.l10n_do_fiscal_journal = False
        paid = self.sync([self.order_data(ncf=False)])
        self.assertEqual(paid.state, 'paid')
        self.assertFalse(paid.account_move)

    def test_open_session_keeps_fiscal_cash_receipt(self):
        count_before = self.env['account.payment'].search_count([])
        order = self.sync([self.order_data(self.cash)])
        self.assertEqual(order.state, 'invoiced')
        self.assertEqual(order.account_move.amount_residual, 0)
        self.assertEqual(self.env['account.payment'].search_count([]), count_before + 1)
        self.assertTrue(order.payment_ids.account_move_id)

    def posted_balances(self):
        self.env.flush_all()
        self.cr.execute('''SELECT account_id,round(sum(balance)::numeric,2)
            FROM account_move_line WHERE company_id=%s AND parent_state='posted'
            GROUP BY account_id HAVING round(sum(balance)::numeric,2)<>0 ORDER BY account_id''',
            [self.company.id])
        return self.cr.fetchall()

    def assert_closed_session_invoice(self, method):
        data = self.order_data(method)
        data.pop('name')
        order = self.env['pos.order'].create(data)
        self.session.cash_register_balance_end_real = self.session.cash_register_balance_end
        # Historical uninvoiced cash/bank sales closed against a balancing receivable.
        self.session.action_pos_session_closing_control(
            balancing_account=self.pos_receivable,
            amount_to_balance=-118 if method != self.pay_later else 0)
        self.assertEqual(self.session.state, 'closed')
        self.assertEqual(order.state, 'done')
        closing_entry = self.session.move_id
        before = self.posted_balances()
        payment_count = self.env['account.payment'].search_count([])
        order.with_context(generate_pdf=False).action_pos_order_invoice()
        self.assertEqual(order.account_move.state, 'posted')
        self.assertEqual(order.account_move.ref, data['ncf'])
        self.assertEqual(self.env['account.payment'].search_count([]), payment_count)
        self.assertEqual(self.posted_balances(), before)
        reversal = self.env['account.move'].search([('reversed_pos_order_id', '=', order.id)])
        self.assertEqual(len(reversal), 1)
        self.assertEqual(reversal.state, 'posted')
        self.assertEqual(self.session.move_id, closing_entry)
        self.assertEqual(order.account_move.amount_residual, 118 if method == self.pay_later else 0)
        moves = self.env['account.move'].search_count([])
        order.with_context(generate_pdf=False).action_pos_order_invoice()
        self.assertEqual(self.env['account.move'].search_count([]), moves)

    def test_closed_session_cash_does_not_collect_again(self):
        self.assert_closed_session_invoice(self.cash)

    def test_closed_session_bank_does_not_collect_again(self):
        self.assert_closed_session_invoice(self.bank)

    def test_closed_session_identified_bank_payment(self):
        self.assert_closed_session_invoice(self.identified_bank)

    def test_closed_session_credit_remains_unpaid(self):
        self.assert_closed_session_invoice(self.pay_later)

    def test_checkout_allocates_number_only_with_posted_invoice(self):
        data = self.order_data(reserve=False)
        before = self.sequence.number_next_actual
        order = self.sync([data])
        self.assertEqual(order.state, 'invoiced')
        self.assertEqual(order.ncf, 'B0200000080')
        self.assertEqual(order.account_move.ref, order.ncf)
        self.assertEqual(self.sequence.number_next_actual, before + 1)

    def test_draft_interruption_consumes_no_number_and_can_resume(self):
        data = self.order_data(reserve=False, state='draft')
        before = self.sequence.number_next_actual
        draft = self.sync([data])
        self.assertFalse(draft.ncf)
        self.assertFalse(draft.account_move)
        self.assertEqual(self.sequence.number_next_actual, before)
        data.update(state='paid', access_token=draft.access_token,
                    lines=[(1, draft.lines.id, data['lines'][0][2])],
                    payment_ids=[(1, draft.payment_ids.id, data['payment_ids'][0][2])])
        recovered = self.sync([data])
        self.assertEqual(recovered, draft)
        self.assertEqual(recovered.state, 'invoiced')
        self.assertEqual(recovered.ncf, 'B0200000080')
        self.assertEqual(self.sequence.number_next_actual, before + 1)

    def test_invoice_failure_rolls_back_number_order_and_payments_then_recovers(self):
        data = self.order_data(self.cash, reserve=False)
        before = self.sequence.number_next_actual
        payments = self.env['account.payment'].search_count([])
        logs = self.env['pos.order.ncf.log'].search_count([])
        with self.assertRaisesRegex(ConnectionError, 'interrupted'), self.cr.savepoint():
            with patch.object(type(self.env['pos.order']), '_generate_pos_order_invoice',
                              side_effect=ConnectionError('interrupted')):
                self.sync([data])
        self.assertEqual(self.sequence.number_next_actual, before)
        self.assertEqual(self.env['pos.order.ncf.log'].search_count([]), logs)
        self.assertEqual(self.env['account.payment'].search_count([]), payments)
        self.assertFalse(self.env['pos.order'].search([('uuid', '=', data['uuid'])]))
        recovered = self.sync([data])
        self.assertEqual(recovered.ncf, 'B0200000080')
        self.assertEqual(recovered.state, 'invoiced')
        self.assertEqual(self.env['account.payment'].search_count([]), payments + 1)

    def test_failure_after_posting_rolls_back_entire_checkout(self):
        data = self.order_data(self.cash, reserve=False)
        payments = self.env['account.payment'].search_count([])
        original = type(self.env['pos.order'])._generate_pos_order_invoice
        def interrupted(order):
            original(order)
            self.assertEqual(order.account_move.state, 'posted')
            self.assertEqual(self.env['account.payment'].search_count([]), payments + 1)
            raise ConnectionError('after posting')
        moves = self.env['account.move'].search_count([])
        with self.assertRaisesRegex(ConnectionError, 'after posting'), self.cr.savepoint():
            with patch.object(type(self.env['pos.order']), '_generate_pos_order_invoice', interrupted):
                self.sync([data])
        self.assertEqual(self.env['account.move'].search_count([]), moves)
        self.assertEqual(self.env['account.payment'].search_count([]), payments)
        self.assertEqual(self.sequence.number_next_actual, 80)
        self.assertFalse(self.env['pos.order'].search([('uuid', '=', data['uuid'])]))
        self.assertEqual(self.sync([data]).state, 'invoiced')

    def test_lost_checkout_reply_recovers_same_number_without_collecting_twice(self):
        data = self.order_data(self.cash, reserve=False)
        first = self.sync([data])
        self.assertEqual(first.state, 'invoiced')
        invoice = first.account_move
        counter = self.sequence.number_next_actual
        payments = self.env['account.payment'].search_count([])
        recovered = self.sync([data])
        self.assertEqual(recovered, first)
        self.assertEqual(recovered.account_move, invoice)
        self.assertEqual(recovered.ncf, 'B0200000080')
        self.assertEqual(self.sequence.number_next_actual, counter)
        self.assertEqual(self.env['account.payment'].search_count([]), payments)
        self.assertEqual(len(recovered.payment_ids), 1)

    def test_legacy_browser_cannot_reserve_a_number_without_saving(self):
        before = self.sequence.number_next_actual
        with self.assertRaisesRegex(UserError, 'Reload'):
            self.env['pos.order'].get_next_fiscal_sequence(self.fiscal_type.id, self.company.id, [],
                json.dumps({'uuid': str(uuid4()), 'session_id': self.session.id}))
        self.assertEqual(self.sequence.number_next_actual, before)

    def test_missing_operation_identifier_does_not_consume_a_number(self):
        data = self.order_data(reserve=False, uuid=False)
        with self.assertRaisesRegex(UserError, 'identifier'), self.cr.savepoint():
            self.sync([data])
        self.assertEqual(self.sequence.number_next_actual, 80)
