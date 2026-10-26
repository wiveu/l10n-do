from datetime import timedelta as td

from odoo import fields
from odoo.exceptions import UserError
from .common import AccountMoveCommon


class AccountMoveTests(AccountMoveCommon):

    def test_001_invoice_fiscal_sequence_id(self):
        """
        Checks invoices gets the right fiscal_sequence_id
        when created
        """

        # Customer invoice (out_invoice)
        invoice_1_id = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_1,
                "fiscal_type_id": self.fiscal_type_fiscal,
            }
        )
        self.assertEqual(invoice_1_id.fiscal_sequence_id.id, self.seq_fiscal)

        # Vendor bill (in_invoice)
        invoice_2_id = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_2,
                "fiscal_type_id": self.fiscal_type_informal,
                "move_type": "in_invoice",
            }
        )
        self.assertEqual(invoice_2_id.fiscal_sequence_id.id, self.seq_informal)

        # Customer refund
        invoice_3_id = self.invoice_obj.create(
            {"partner_id": self.partner_demo_3, "move_type": "out_refund"}
        )
        self.assertEqual(invoice_3_id.fiscal_sequence_id.id, self.seq_credit_note)

        # Customer debit note
        invoice_4_id = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_4,
                "move_type": "out_invoice",
                "is_debit_note": True,
            }
        )
        self.assertEqual(invoice_4_id.fiscal_sequence_id.id, self.seq_debit_note)

    def test_002_invoice_date_expired_sequence(self):
        """
        Check that an invoice which date is >= fiscal sequence expiration
        date does not get any fiscal sequence
        """

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_1,
                "fiscal_type_id": self.fiscal_type_fiscal,
                "invoice_date": fields.Date.today() + td(weeks=156),
            }
        )
        self.assertFalse(invoice_id.fiscal_sequence_id)

    def test_003_onchange_journal_id(self):
        """
        After create a new fiscal invoice, if journal is changed to a
        non fiscal one, fiscal_type_id and fiscal_sequence_id must be
        removed
        """

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_1,
                "fiscal_type_id": self.fiscal_type_fiscal,
            }
        )

        no_fiscal_journal_id = self.journal_obj.create(
            {"name": "No fiscal Sale journal", "type": "sale", "code": "NFSJ"}
        )
        invoice_id.journal_id = no_fiscal_journal_id.id
        invoice_id._onchange_journal_id()

        self.assertFalse(invoice_id.fiscal_type_id)
        self.assertFalse(invoice_id.fiscal_sequence_id)

    def test_004_onchange_partner_id(self):
        """
        When creating a new one or changing invoice partner_id,
        if not fiscal_type_id, invoice fiscal_type_id must be
        partner_id sale_fiscal_type_id
        """

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_1,
                "fiscal_type_id": self.fiscal_type_fiscal,
            }
        )
        invoice_id.write({"fiscal_type_id": False, "partner_id": self.partner_demo_4})
        invoice_id._onchange_partner_id()

        partner_id = self.partner_obj.browse(self.partner_demo_4)
        self.assertEqual(
            invoice_id.fiscal_type_id.id, partner_id.sale_fiscal_type_id.id
        )

    def test_005_fiscal_type_journal(self):
        """
        When changing a draft invoice fiscal type to a one which
        have a journal, invoice journal must me fiscal type journal
        """

        consumo_journal_id = self.journal_obj.create(
            {"name": "Consumo Sale journal", "type": "sale", "code": "CSJ"}
        )
        fiscal_type_consumo = self.fiscal_type_obj.browse(self.fiscal_type_consumo)
        fiscal_type_consumo.journal_id = consumo_journal_id.id

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_1,
                "fiscal_type_id": self.fiscal_type_fiscal,
            }
        )
        invoice_id.fiscal_type_id = self.fiscal_type_consumo
        invoice_id._onchange_fiscal_type()

        self.assertEqual(invoice_id.journal_id.id, fiscal_type_consumo.journal_id.id)

    def test_006_invoice_fiscal_type_expense_type(self):
        """
        When creating a new vendor bill or changing the partner
        to an existing one, fiscal_type_id and expense_type must
        come from the partner
        """

        invoice_id = self.invoice_obj.create(
            {"partner_id": self.partner_demo_4, "move_type": "in_invoice"}
        )
        invoice_id.partner_id = self.partner_demo_5
        invoice_id._onchange_partner_id()

        partner_id = self.partner_obj.browse(self.partner_demo_5)

        self.assertEqual(
            invoice_id.fiscal_type_id.id, partner_id.purchase_fiscal_type_id.id
        )
        self.assertEqual(invoice_id.expense_type, partner_id.expense_type)

    def test_007_invoice_fiscal_sequence_status(self):
        """
        Check invoice fiscal_sequence_status 'fiscal_ok'
        when it should
        """

        invoice_1 = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_1,
                "fiscal_type_id": self.fiscal_type_fiscal,
                "invoice_line_ids": self.invoice_line_data,
            }
        )

        self.assertEqual(invoice_1.fiscal_sequence_status, "fiscal_ok")

    def test_008_invoice_fiscal_sequence_status(self):
        """
        Check invoice fiscal_sequence_status 'almost_no_sequence'
        when it should
        """

        sequence = self.env['account.fiscal.sequence'].browse(self.seq_fiscal)
        sequence.number_next_actual = sequence.sequence_end - int(sequence.warning_gap) + 2
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'fiscal_type_id': self.fiscal_type_fiscal,
            'invoice_line_ids': self.invoice_line_data,
        })
        self.assertEqual(invoice.fiscal_sequence_status, 'almost_no_sequence')

    def test_009_invoice_partner_sale_fiscal_type(self):
        """
        Check when out_invoice validate, if not partner_id.sale_fiscal_type_id,
        partner_id.sale_fiscal_type_id =  invoice.fiscal_type_id
        """

        partner_id = self.partner_obj.create({"name": "Test Partner", "sale_fiscal_type_id": False})
        self.assertFalse(partner_id.sale_fiscal_type_id)

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": partner_id.id,
                "fiscal_type_id": self.fiscal_type_consumo,
                "invoice_line_ids": self.invoice_line_data,
            }
        )
        invoice_id.action_post()

        self.assertEqual(partner_id.sale_fiscal_type_id.id, self.fiscal_type_consumo)

    def test_010_invoice_partner_purchase_fiscal_type_expense_type(self):
        """
        Check when in_invoice validate, if not partner_id.purchase_fiscal_type,
        partner_id.purchase_fiscal_type_id = invoice.fiscal_type_id and if not
        partner_id.expense_type, partner_id.expense_type = invoice.expense_type
        """

        partner_id = self.partner_obj.create(
            {"name": "Test Partner", "vat": "22400559607"}
        )
        assert not partner_id.purchase_fiscal_type_id
        assert not partner_id.expense_type

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": partner_id.id,
                "fiscal_type_id": self.fiscal_type_informal,
                "expense_type": "02",
                "invoice_line_ids": self.invoice_line_data,
                "move_type": "in_invoice",
            }
        )
        invoice_id.action_post()

        self.assertEqual(
            partner_id.purchase_fiscal_type_id.id, self.fiscal_type_informal
        )
        self.assertEqual(partner_id.expense_type, "02")

    def test_011_requires_document_error(self):
        """
        Check when invoice validate, if fiscal_type_id.requires_document and
        not partner_id.vat, raise UserError
        """

        partner_id = self.partner_obj.create({"name": "Test Partner"})

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": partner_id.id,
                "fiscal_type_id": self.fiscal_type_fiscal,
                "invoice_line_ids": self.invoice_line_data,
            }
        )

        with self.assertRaises(UserError):
            invoice_id.action_post()

    def test_012_no_vat_partner_amount_total_limit(self):

        partner_id = self.partner_obj.create({"name": "Test Partner"})

        account_id = self.invoice_line_data[0][2]['account_id']
        invoice_line_data = [
            (
                0,
                0,
                {
                    "product_id": self.env.ref("product.product_product_1").id,
                    "quantity": 1.00,
                    "account_id": account_id,
                    "name": "product test 1",
                    "price_unit": 250000,
                },
            )
        ]

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": partner_id.id,
                "fiscal_type_id": self.fiscal_type_consumo,
                "invoice_line_ids": invoice_line_data,
            }
        )

        with self.assertRaises(UserError):
            invoice_id.action_post()

        out_invoice_id = self.invoice_obj.create(
            {
                "partner_id": partner_id.id,
                "fiscal_type_id": self.fiscal_type_consumo,
                "invoice_line_ids": invoice_line_data,
            }
        )

        with self.assertRaises(UserError):
            out_invoice_id.action_post()

    def _adjustment(self, invoice, *, debit=False, percentage=None, amount=None):
        if debit:
            note = invoice.copy({
                'is_debit_note': True, 'origin_out': invoice.ref,
                'ref': 'B0300000001' if invoice.move_type == 'in_invoice' else False,
                'fiscal_type_id': False, 'invoice_date': fields.Date.today(),
            })
        else:
            wizard = self.invoice_refund_obj.with_context(
                active_model='account.move', active_ids=invoice.ids,
            ).create({
                'reason': 'Synthetic refund', 'date': fields.Date.today(),
                'journal_id': invoice.journal_id.id,
                'refund_ref': 'B0400000001' if invoice.move_type == 'in_invoice' else False,
            })
            self.assertTrue(wizard.is_fiscal_refund)
            wizard.reverse_moves()
            note = wizard.new_move_ids
        # Odoo 18 edits partial amounts on the draft note, not removed wizard fields.
        if percentage is not None:
            for line in note.invoice_line_ids:
                line.quantity *= percentage / 100
        if amount is not None:
            account = invoice.invoice_line_ids[0].account_id
            note.invoice_line_ids = [(5, 0, 0), (0, 0, {
                'name': 'Synthetic adjustment', 'account_id': account.id,
                'quantity': 1, 'price_unit': amount, 'tax_ids': [(5, 0, 0)],
            })]
        if debit and invoice.move_type == 'in_invoice':
            note.ref = 'B0300000001'
        note.action_post()
        self.assertEqual(note.origin_out, invoice.ref)
        return note

    def test_013_fiscal_customer_refund_percentage(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'move_type': 'out_invoice',
            'fiscal_type_id': self.fiscal_type_fiscal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice, debit=False, percentage=10)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_cn)
        self.assertEqual(note.move_type, 'out_refund')
        self.assertEqual(note.ref[:3], 'B04')
        self.assertEqual(note.amount_total, 20.72)

    def test_014_fiscal_customer_refund_amount(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'move_type': 'out_invoice',
            'fiscal_type_id': self.fiscal_type_fiscal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice, debit=False, amount=100)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_cn)
        self.assertEqual(note.move_type, 'out_refund')
        self.assertEqual(note.ref[:3], 'B04')
        self.assertEqual(note.amount_total, 100)

    def test_015_fiscal_vendor_refund_percentage(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_2,
            'move_type': 'in_invoice',
            'fiscal_type_id': self.fiscal_type_informal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice, debit=False, percentage=10)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_cn_purchase)
        self.assertEqual(note.move_type, 'in_refund')
        self.assertEqual(note.ref[:3], 'B04')
        self.assertEqual(note.amount_total, 20.72)

    def test_016_fiscal_vendor_refund_amount(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_2,
            'move_type': 'in_invoice',
            'fiscal_type_id': self.fiscal_type_informal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice, debit=False, amount=100)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_cn_purchase)
        self.assertEqual(note.move_type, 'in_refund')
        self.assertEqual(note.ref[:3], 'B04')
        self.assertEqual(note.amount_total, 100)

    def test_017_fiscal_customer_debit_note_percentage(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'move_type': 'out_invoice',
            'fiscal_type_id': self.fiscal_type_fiscal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice, debit=True, percentage=10)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_dn)
        self.assertEqual(note.move_type, 'out_invoice')
        self.assertEqual(note.ref[:3], 'B03')
        self.assertEqual(note.amount_total, 20.72)

    def test_018_fiscal_customer_debit_note_amount(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'move_type': 'out_invoice',
            'fiscal_type_id': self.fiscal_type_fiscal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice, debit=True, amount=100)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_dn)
        self.assertEqual(note.move_type, 'out_invoice')
        self.assertEqual(note.ref[:3], 'B03')
        self.assertEqual(note.amount_total, 100)

    def test_019_fiscal_vendor_debit_note_percentage(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_2,
            'move_type': 'in_invoice',
            'fiscal_type_id': self.fiscal_type_informal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice, debit=True, percentage=10)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_dn_purchase)
        self.assertEqual(note.move_type, 'in_invoice')
        self.assertEqual(note.ref[:3], 'B03')
        self.assertEqual(note.amount_total, 20.72)

    def test_020_fiscal_vendor_debit_note_amount(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_2,
            'move_type': 'in_invoice',
            'fiscal_type_id': self.fiscal_type_informal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice, debit=True, amount=100)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_dn_purchase)
        self.assertEqual(note.move_type, 'in_invoice')
        self.assertEqual(note.ref[:3], 'B03')
        self.assertEqual(note.amount_total, 100)

    def test_021_fiscal_vendor_full_refund(self):
        invoice = self.invoice_obj.create({
            'partner_id': self.partner_demo_2, 'move_type': 'in_invoice',
            'fiscal_type_id': self.fiscal_type_informal,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice.action_post()
        note = self._adjustment(invoice)
        self.assertEqual(note.ref, 'B0400000001')
        self.assertEqual(note.amount_total, invoice.amount_total)
        self.assertEqual(note.fiscal_type_id.id, self.fiscal_type_cn_purchase)

    def test_022_invoice_ncf_expiration_date(self):
        """
        Check ncf_expiration_date is kept after invoice validation
        """

        invoice_id = self.invoice_obj.create(
            {
                "partner_id": self.partner_demo_1,
                "fiscal_type_id": self.fiscal_type_fiscal,
                "invoice_line_ids": self.invoice_line_data,
            }
        )
        invoice_id.action_post()

        assert invoice_id.ncf_expiration_date
