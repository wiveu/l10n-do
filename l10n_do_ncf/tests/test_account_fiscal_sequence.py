from odoo import fields
from .common import CommonSetup
from odoo.exceptions import ValidationError


class AccountFiscalSequenceBaseTests(CommonSetup):

    """
    The following tests are executed in a post-install context.
    This means that all fiscal sequence demo data are pre-loaded
    and are considered as existing data as every tests cursor
    is instantiated.
    """

    def test_001_fiscal_sequence_queue(self):
        """
        Validates only one sequence per type can be queue
        """

        sequence_id = self.fiscal_sequence_obj.create(
            {
                "name": "7045195031",
                "fiscal_type_id": self.fiscal_type_credito_fiscal,
                "sequence_start": 300,
                "sequence_end": 310,
            }
        )

        # Because there is one demo credito fiscal sequence queued,
        # sequence can_be_queue must be False
        self.assertEqual(sequence_id.can_be_queue, False)

    def test_002_warning_gap(self):
        """
        Warning gap is a value used to evaluate when fiscal
        sequence deplete warning should be shown. This test
        ensure this value will be always computed right.
        """
        sequence_id = self.fiscal_sequence_obj.create(
            {
                "name": "7045195031",
                "fiscal_type_id": self.fiscal_type_credito_fiscal,
                "sequence_start": 141,
                "sequence_end": 732,
                "remaining_percentage": 12,
            }
        )

        # Warning gap formula:
        # sequence_end - (sequence_start -1)
        # ----------------------------------
        #     remaining_percentage/100
        self.assertEqual(sequence_id.warning_gap, 71)

    def test_003_sequence_start_default(self):
        """
        When on change fiscal_type_id, sequence start must be last active,
        depleted sequence end + 1
        """
        sequence_1_id = self.fiscal_sequence_obj.browse(self.fiscal_seq_credito_fiscal)

        sequence_2_id = self.fiscal_sequence_obj.create(
            {
                "name": "7045195031",
                "fiscal_type_id": self.fiscal_type_consumo,
                "sequence_start": 141,
                "sequence_end": 732,
            }
        )
        sequence_2_id.fiscal_type_id = self.fiscal_type_credito_fiscal
        sequence_2_id._onchange_fiscal_type_id()

        self.assertEqual(sequence_2_id.sequence_start, sequence_1_id.sequence_end + 1)

    def test_004_active_sequence_uniqueness(self):
        """
        There must be only one active fiscal sequence per type
        """
        sequence_id = self.fiscal_sequence_obj.create(
            {
                "name": "7045195031",
                "fiscal_type_id": self.fiscal_type_credito_fiscal,
                "sequence_start": 141,
                "sequence_end": 732,
                "remaining_percentage": 12,
            }
        )

        with self.assertRaises(ValidationError):
            sequence_id._action_confirm()

    def test_005_active_sequence_uniqueness(self):
        """
        Check fiscal sequence does not have range overlap
        """
        sequence_id = self.fiscal_sequence_obj.create(
            {
                "name": "7045195031",
                "fiscal_type_id": self.fiscal_type_credito_fiscal,
                "sequence_start": 101,
                "sequence_end": 150,
                "remaining_percentage": 12,
            }
        )

        # Check sequence_end > sequence_start
        with self.assertRaises(ValidationError):
            sequence_id.write({"sequence_start": 350, "sequence_end": 349})
            sequence_id._action_confirm()

        # Check no overlapping
        with self.assertRaises(ValidationError):
            sequence_id._action_confirm()

    def test_006_cancel_preserves_legacy_internal_sequence(self):
        legacy = self.env['ir.sequence'].create({'name': 'Legacy fiscal sequence'})
        sequence = self.fiscal_sequence_obj.browse(self.fiscal_seq_credito_fiscal)
        sequence.sequence_id = legacy
        sequence._action_cancel()
        self.assertEqual(sequence.state, 'cancelled')
        self.assertFalse(legacy.active)
        self.assertTrue(legacy.exists())

    def test_007_fiscal_sequence_auto_expire(self):
        """
        Fiscal Sequence must change its state to 'expired' when
        validated or a cron runs _expire_sequences()
        """

        sequence_id = self.fiscal_sequence_obj.create(
            {
                "name": "7045195031",
                "fiscal_type_id": self.fiscal_type_unico,
                "sequence_start": 101,
                "sequence_end": 150,
                "expiration_date": fields.Date.today(),
            }
        )
        sequence_id._action_confirm()

        # Check state = 'expired'
        self.assertEqual(sequence_id.state, "expired")

    def test_008_fiscal_sequence_counter_initialized(self):
        fiscal_type = self.fiscal_type_obj.browse(self.fiscal_type_unico).copy({
            'name': 'Synthetic range type', 'prefix': 'B98',
        })
        sequence = self.fiscal_sequence_obj.create({
            'name': 'Synthetic authorization', 'fiscal_type_id': fiscal_type.id,
            'sequence_start': 1, 'sequence_end': 10,
        })
        sequence._action_confirm()
        self.assertEqual(sequence.state, 'active')
        self.assertEqual(sequence.number_next_actual, 1)
        self.assertEqual(sequence.sequence_remaining, 10)
        self.assertEqual(sequence.next_fiscal_number, 'B9800000001')

    def test_009_fiscal_sequence_counter_initialized(self):
        fiscal_type = self.fiscal_type_obj.browse(self.fiscal_type_unico).copy({
            'name': 'Synthetic range type', 'prefix': 'B98',
        })
        sequence = self.fiscal_sequence_obj.create({
            'name': 'Synthetic authorization', 'fiscal_type_id': fiscal_type.id,
            'sequence_start': 21, 'sequence_end': 30,
        })
        sequence._action_confirm()
        self.assertEqual(sequence.state, 'active')
        self.assertEqual(sequence.number_next_actual, 21)
        self.assertEqual(sequence.sequence_remaining, 10)
        self.assertEqual(sequence.next_fiscal_number, 'B9800000021')


class AccountFiscalSequenceTransactionTests(CommonSetup):
    def test_010_sequence_transactions(self):
        company = self.env['res.company'].create({'name': 'Synthetic range company'})
        self.env.user.company_ids |= company
        ranges = self.fiscal_sequence_obj.with_company(company)
        sequence = ranges.create({
            'name': 'Synthetic authorization',
            'fiscal_type_id': self.fiscal_type_credito_fiscal,
            'sequence_start': 1, 'sequence_end': 10,
        })
        sequence._action_confirm()
        queued = ranges.create({
            'name': 'Synthetic queued authorization',
            'fiscal_type_id': self.fiscal_type_credito_fiscal,
            'sequence_start': 11, 'sequence_end': 20,
        })
        queued.action_queue()
        for index in range(1, 11):
            self.assertEqual(sequence.get_fiscal_number(), 'B01%08d' % index)
            self.assertEqual(sequence.sequence_remaining, 10 - index)
            self.assertEqual(sequence.next_fiscal_number, 'B01%08d' % (index + 1))
        self.assertEqual(sequence.state, 'depleted')
        self.assertEqual(queued.state, 'active')
        self.assertEqual(queued.number_next_actual, 11)
