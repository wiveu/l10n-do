from odoo import fields
from odoo.tests.common import TransactionCase


class CommonSetup(TransactionCase):
    def setUp(self):
        super(CommonSetup, self).setUp()

        # The legacy demo XML confirms a batch; prepare every range explicitly.
        demo = self.env['ir.model.data'].search([
            ('module', '=', 'l10n_do_ncf'), ('model', '=', 'account.fiscal.sequence'),
        ])
        for sequence in self.env['account.fiscal.sequence'].browse(demo.mapped('res_id')).filtered(
                lambda record: record.state == 'draft'):
            sequence._action_confirm()
        self.fiscal_sequence_obj = self.env["account.fiscal.sequence"]
        self.fiscal_type_obj = self.env["account.fiscal.type"]
        self.fiscal_seq_credito_fiscal = self.ref(
            "l10n_do_ncf.credito_fiscal_demo"
        )
        self.fiscal_seq_unico = self.ref("l10n_do_ncf.unico_demo")
        self.fiscal_type_credito_fiscal = self.ref(
            "l10n_do_ncf.fiscal_type_credito_fiscal"
        )
        self.fiscal_type_consumo = self.ref("l10n_do_ncf.fiscal_type_consumo")
        self.fiscal_type_unico = self.ref("l10n_do_ncf.fiscal_type_unico")


class AccountMoveCommon(CommonSetup):
    def setUp(self):
        super(AccountMoveCommon, self).setUp()

        self.invoice_obj = self.env["account.move"]
        self.journal_obj = self.env["account.journal"]
        self.partner_obj = self.env["res.partner"]
        self.fiscal_type_obj = self.env["account.fiscal.type"]
        self.invoice_refund_obj = self.env["account.move.reversal"]

        self.sale_journal = False
        self.purchase_journal = False

        # Setup Fiscal Journals
        for journal in self.journal_obj.search([("company_id", "=", self.env.company.id), ("type", "in", ("sale", "purchase"))]):
            journal.l10n_do_fiscal_journal = True
            if journal.type == "sale":
                self.sale_journal = journal
            else:
                self.purchase_journal = journal

        # Demo partners
        self.partner_demo_1 = self.ref("l10n_do_ncf.res_partner_demo_1")
        self.partner_demo_2 = self.ref("l10n_do_ncf.res_partner_demo_2")
        self.partner_demo_3 = self.ref("l10n_do_ncf.res_partner_demo_3")
        self.partner_demo_4 = self.ref("l10n_do_ncf.res_partner_demo_4")
        self.partner_demo_5 = self.ref("l10n_do_ncf.res_partner_demo_5")

        # Demo fiscal sequence
        self.seq_fiscal = self.ref("l10n_do_ncf.credito_fiscal_demo")
        self.seq_consumo = self.ref("l10n_do_ncf.consumo_demo")
        self.seq_unico = self.ref("l10n_do_ncf.unico_demo")
        self.seq_informal = self.ref("l10n_do_ncf.informal_demo")
        self.seq_credit_note = self.ref("l10n_do_ncf.cn_demo")
        self.seq_debit_note = self.ref("l10n_do_ncf.dn_demo")

        # Demo fiscal type
        self.fiscal_type_fiscal = self.ref(
            "l10n_do_ncf.fiscal_type_credito_fiscal"
        )
        self.fiscal_type_consumo = self.ref("l10n_do_ncf.fiscal_type_consumo")
        self.fiscal_type_informal = self.ref("l10n_do_ncf.fiscal_type_informal")
        self.fiscal_type_cn = self.ref("l10n_do_ncf.fiscal_type_credit_note")
        self.fiscal_type_cn_purchase = self.ref(
            "l10n_do_ncf.fiscal_type_purchase_credit_note"
        )
        self.fiscal_type_dn = self.ref("l10n_do_ncf.fiscal_type_debit_note")
        self.fiscal_type_dn_purchase = self.ref(
            "l10n_do_ncf.fiscal_type_purchase_debit_note"
        )

        # Invoice lines
        account_id = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', self.env.company.id),
        ], limit=1).id
        self.assertTrue(account_id, 'The test company needs an income account')
        self.invoice_obj = self.invoice_obj.with_context(default_move_type='out_invoice', default_invoice_date=fields.Date.today())

        self.invoice_line_data = [
            (
                0,
                0,
                {
                    "product_id": self.env.ref("product.product_product_1").id,
                    "tax_ids": [(5, 0, 0)],
                    "quantity": 40.0,
                    "account_id": account_id,
                    "name": "product test 1",
                    "price_unit": 2.27,
                },
            ),
            (
                0,
                0,
                {
                    "product_id": self.env.ref("product.product_product_2").id,
                    "tax_ids": [(5, 0, 0)],
                    "quantity": 21.0,
                    "account_id": account_id,
                    "name": "product test 2",
                    "price_unit": 2.77,
                },
            ),
            (
                0,
                0,
                {
                    "product_id": self.env.ref("product.product_product_3").id,
                    "tax_ids": [(5, 0, 0)],
                    "quantity": 21.0,
                    "account_id": account_id,
                    "name": "product test 3",
                    "price_unit": 2.77,
                },
            ),
        ]
