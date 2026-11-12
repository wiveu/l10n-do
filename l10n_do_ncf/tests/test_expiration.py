from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFiscalRangeExpiration(TransactionCase):
    def fiscal_type(self, prefix, kind='out_invoice'):
        model = self.env['account.fiscal.type']
        return model.search([('prefix', '=', prefix), ('type', '=', kind)], limit=1) or model.create({
            'name': 'Synthetic ' + prefix, 'prefix': prefix, 'type': kind,
            'padding': 10, 'assigned_sequence': True,
        })

    def test_e32_e34_form_clears_expiration_and_confirmed_ranges_never_expire(self):
        for prefix, kind in [('E32', 'out_invoice'), ('E34', 'out_refund')]:
            with self.subTest(prefix=prefix):
                with Form(self.env['account.fiscal.sequence']) as form:
                    form.name = 'Synthetic non-expiring authorization'
                    form.fiscal_type_id = self.fiscal_type(prefix, kind)
                    form.sequence_start = 1
                    form.sequence_end = 5
                    self.assertFalse(form.expiration_date)
                sequence = form.record
                action = sequence.action_confirm()
                self.env['account.fiscal.sequence.validate_wizard'].with_context(
                    **action['context']).create({}).confirm_cancel()
                self.assertEqual(sequence.state, 'active')
                self.assertEqual(sequence.number_next_actual, 1)
                # Legacy dates stay auditable but cannot expire E32/E34 authorizations.
                sequence.expiration_date = fields.Date.add(fields.Date.today(), days=-1)
                self.env['account.fiscal.sequence']._expire_sequences()
                self.assertEqual(sequence.state, 'active')
                self.assertEqual(sequence.number_next_actual, 1)

    def test_b_and_e31_authorizations_still_require_expiration(self):
        for prefix in ('B01', 'B02', 'E31'):
            with self.subTest(prefix=prefix), self.assertRaisesRegex(
                    ValidationError, 'requires an expiration date'), self.cr.savepoint():
                self.env['account.fiscal.sequence'].create({
                    'name': 'Synthetic missing expiration', 'fiscal_type_id': self.fiscal_type(prefix).id,
                    'sequence_start': 1, 'sequence_end': 5, 'expiration_date': False,
                })
