import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import SQL
from odoo.osv.expression import AND
from datetime import timedelta


class PosOrder(models.Model):
    _inherit = 'pos.order'

    ncf = fields.Char(
        string='NCF',
        copy=False,
    )
    ncf_origin_out = fields.Char(
        string='Affects',
        copy=False,
    )
    ncf_expiration_date = fields.Date(
        string='NCF expiration date',
    )
    fiscal_type_id = fields.Many2one(
        string='Fiscal type',
        comodel_name='account.fiscal.type',
    )
    fiscal_sequence_id = fields.Many2one(
        string='Fiscal Sequence',
        comodel_name='account.fiscal.sequence',
        copy=False,
    )
    is_used_in_order = fields.Boolean(
        default=False
    )

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        
        result['ncf'] = order.ncf
        result['ncf_origin_out'] = order.ncf_origin_out
        result['ncf_expiration_date'] = order.ncf_expiration_date
        result['fiscal_type_id'] = order.fiscal_type_id.id if order.fiscal_type_id else False
        result['fiscal_sequence_id'] = order.fiscal_sequence_id.id if order.fiscal_sequence_id else False

        return result

    @api.model
    def _order_fields(self, ui_order):
        """
        Prepare the dict of values to create the new pos order.
        """
        fields = super(PosOrder, self)._order_fields(ui_order)

        fields['ncf'] = ui_order.get('ncf') or False
        fields['ncf_origin_out'] = ui_order.get('ncf_origin_out') or False
        fields['ncf_expiration_date'] = ui_order.get('ncf_expiration_date') or False
        fields['fiscal_type_id'] = ui_order.get('fiscal_type_id') or False
        fields['fiscal_sequence_id'] = ui_order.get('fiscal_sequence_id') or False

        return fields

    def _prepare_invoice_vals(self):
        """
        Prepare the dict of values to create the new invoice for a pos order.
        """
        invoice_vals = super(PosOrder, self)._prepare_invoice_vals()

        if self.config_id.invoice_journal_id.l10n_do_fiscal_journal:
            invoice_vals['ref'] = self.ncf
            invoice_vals['origin_out'] = self.ncf_origin_out
            invoice_vals['ncf_expiration_date'] = self.ncf_expiration_date
            invoice_vals['fiscal_type_id'] = self.fiscal_type_id.id
            invoice_vals['fiscal_sequence_id'] = self.fiscal_sequence_id.id

        return invoice_vals

    @api.model
    def _payment_fields(self, order, ui_paymentline):

        fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)

        fields.update({
            'name': ui_paymentline.get('credit_note_ncf'),
        })

        return fields

    # @api.model
    # def _process_order(self, order, draft, existing_order):
    #     """
    #     this part is using for eliminate cash return
    #     :param pos_order:
    #     :return pos_order:
    #     """
    #     if pos_order['amount_return'] > 0:

    #         pos_session_obj = self.env['pos.session'].browse(
    #             pos_order['pos_session_id']
    #         )
    #         cash_journal_id = pos_session_obj.cash_journal_id.id
    #         if not cash_journal_id:
    #             # If none, select for change one of the cash journals of the PO
    #             # This is used for example when a customer pays by credit card
    #             # an amount higher than total amount of the order and gets cash
    #             # back
    #             cash_journal = [statement.journal_id
    #                             for statement in pos_session_obj.statement_ids
    #                             if statement.journal_id.type == 'cash']
    #             if not cash_journal:
    #                 raise UserError(
    #                     _("No cash statement found for this session. "
    #                       "Unable to record returned cash."))

    #             cash_journal_id = cash_journal[0].id

    #         for index, statement in enumerate(pos_order['statement_ids']):

    #             if statement[2]['journal_id'] == cash_journal_id:
    #                 pos_order['statement_ids'][index][2]['amount'] = \
    #                     statement[2]['amount'] - pos_order['amount_return']

    #         pos_order['amount_return'] = 0

    #     return super(PosOrder, self)._process_order(pos_order)

    def _process_saved_order(self, draft):
        fiscal = (not draft and self.state != 'cancel' and self.amount_total
                  and self.config_id.invoice_journal_id.l10n_do_fiscal_journal)
        if fiscal:
            if not self.partner_id:
                self.partner_id = self.config_id.pos_partner_id
            if not self.partner_id:
                raise UserError(_('This point of sale not have default customer, please set default customer in config POS'))
            if not self.ncf:
                if not self.uuid:
                    raise UserError(_('A fiscal sale requires a stable order identifier. Reload the POS.'))
                if not self.fiscal_type_id or not self.fiscal_type_id.assigned_sequence:
                    raise UserError(_('Select a fiscal type before completing this sale.'))
                reservation = self._get_next_fiscal_sequence(
                    self.fiscal_type_id.id, self.company_id.id, [],
                    json.dumps({'uuid': self.uuid, 'session_id': self.session_id.id}))
                self.write({key: reservation[key] for key in
                            ('ncf', 'fiscal_sequence_id', 'ncf_expiration_date')})
        result = super()._process_saved_order(draft)
        if fiscal and self.state == 'paid':
            self._generate_pos_order_invoice()
        if fiscal and (self.state != 'invoiced' or self.account_move.state != 'posted'):
            raise UserError(_('The fiscal sale could not be invoiced. Retry the same order.'))
        return result


    def get_next_fiscal_sequence(self, fiscal_type_id, company_id, payments, order_json):
        raise UserError(_('Reload the POS. Fiscal numbers are assigned when the sale is saved.'))

    def _get_next_fiscal_sequence(
            self, 
            fiscal_type_id,
            company_id, 
            payments,
            order_json
        ):
        """
        search active fiscal sequence dependent with fiscal type
        :param order:[fiscal_type_id, company_id, mode, lines,]
        :return: {ncf, expiration date, fiscal sequence}
        """

        fiscal_type = self.env['account.fiscal.type'].browse(fiscal_type_id)

        fiscal_sequence = self.env['account.fiscal.sequence'].search([
            ('fiscal_type_id', '=', fiscal_type_id),
            ('state', '=', 'active'),
            ('company_id', '=', company_id)
        ], limit=1)

        if not fiscal_sequence:
            raise UserError(
                _(u"There is no current active NCF of {}, please create a new fiscal sequence of type {}.").format(
                    fiscal_type.name,
                    fiscal_type.name,
            ))

        # Allocation, order and invoice must commit or roll back together.
        fiscal_sequence.flush_recordset()
        self.env.cr.execute(SQL('SELECT id FROM account_fiscal_sequence WHERE id = %s FOR UPDATE', fiscal_sequence.id))
        fiscal_sequence.invalidate_recordset()
        new_ncf = fiscal_sequence.sudo().get_fiscal_number()
        
        # This is the better way to identify problems with fiscal sequences 
        ncf_log = self.env['pos.order.ncf.log'].sudo().create({
            'l10n_do_ncf': new_ncf,
            'order_json': order_json,
            'company_id': company_id
        })

        return {
            'ncf': new_ncf,
            'fiscal_sequence_id': fiscal_sequence.id,
            'ncf_expiration_date': fiscal_sequence.expiration_date,
            'ncf_log_id': ncf_log.id
        }

    def get_credit_note(self, ncf):
        """
        Get credit note
        :param ncf:
        :return:
        """
        credit_note = self.env['account.move'].search([
            ('ref', '=', ncf),
            ('move_type', '=', 'out_refund'),
            ('is_l10n_do_fiscal_invoice', '=', True),
            ('company_id', '=', self.env.company.id),
            ('state', '=', 'posted')
        ], limit=1)

        if not credit_note:
            raise UserError(_('Credit note not found'))

        return {
            'partner_id': credit_note.partner_id.id,
            'residual_amount': credit_note.amount_residual,
            'ncf': credit_note.ref,
        }

    def get_credit_notes(self, partner_id):
        """
        Get credit note
        :param partner_id:
        :return: credit notes from partner
        """
        credit_notes = self.env['account.move'].search([
            ('partner_id', '=', partner_id),
            ('move_type', '=', 'out_refund'),
            ('is_l10n_do_fiscal_invoice', '=', True),
            ('amount_residual', '>', 0.0),
            ('company_id', '=', self.env.company.id),
            ('state', '=', 'posted')
        ])

        if not credit_notes:
            raise UserError(_('This customer does not have credit notes'))

        return[{
            'id': credit_note.id,
            'label': "%s - %s %s" % (credit_note.ref, credit_note.currency_id.name, credit_note.amount_residual),
            'item':{
                'partner_id': credit_note.partner_id.id,
                'residual_amount': credit_note.amount_residual,
                'ncf': credit_note.ref,
            }} for credit_note in credit_notes]

    @api.model
    def search_paid_order_ids(self, config_id, domain, limit, offset):
        """Search for 'paid' orders that satisfy the given domain, limit and offset."""
        pos_config = self.env['pos.config'].browse(config_id)
        
        if pos_config.invoice_journal_id.l10n_do_fiscal_journal:
            electronic = getattr(pos_config, 'l10n_do_ecf_enabled', False)
            config_domain = [('invoice_journal_id.l10n_do_fiscal_journal', '=', True)]
            if electronic:
                config_domain += [('l10n_do_ecf_enabled', '=', True),
                                  ('company_id', '=', pos_config.company_id.id)]
            config_ids = self.env['pos.config'].search(config_domain).ids

            default_domain = [
                '&', '&', '&',
                ('config_id', 'in', config_ids), 
                ('ncf', '!=', False),
                ('amount_total', '!=', 0) if electronic else ('amount_total', '>', 0),
                '!', '|', 
                ('state', '=', 'draft'), 
                ('state', '=', 'cancelled')
            ]
            
            if pos_config.l10n_do_type_limit_order_history == 'days':
                default_domain.insert(3, '&')
                default_domain.insert(4, 
                    ('create_date', '>=', fields.Datetime.to_string(fields.Datetime.now() - timedelta(days=pos_config.l10n_do_type_limit_order_history_days))))

            real_domain = AND([domain, default_domain])
            ids = self.search(AND([domain, default_domain]), limit=limit, offset=offset).ids
            totalCount = self.search_count(real_domain)
            
            return {'ids': ids, 'totalCount': totalCount}

        return super(PosOrder, self).search_paid_order_ids(config_id, domain, limit, offset)


class PosOrderNcfLog(models.Model):
    _name = 'pos.order.ncf.log'
    _description = 'Each time an NCF is generated, it is necessary to log the order in JSON so that the client can continue in case of an error.'
    _rec_name = 'l10n_do_ncf'
    
    l10n_do_ncf = fields.Char(
        string='NCF', 
        required=True
    )
    order_json = fields.Text(
        string='Order in JSON', 
        required=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company', 
        string='Company', 
        required=True, 
        default=lambda self: self.env.company
    )

    # TODO: CREATE METHOD create order FROM order_json
