/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this._creditNoteMode = false;
    },

    // Check if POS is in credit note refund mode
    isCreditNoteMode() {
        if (!this.config.l10n_do_fiscal_journal) {
            return false;
        }

        const currentOrder = this.get_order();
        return currentOrder && currentOrder._isRefundAndSaleOrder && currentOrder._isRefundAndSaleOrder();
    },

    // Get credit note payment method
    get_credit_note_payment_method() {
        if (!this.config.l10n_do_fiscal_journal) {
            return null;
        }

        return this.models["pos.payment.method"]?.find(
            pm => pm.is_credit_note && this.config.payment_method_ids.some(m => m.id === pm.id)
        );
    },

    postSyncAllOrders(orders) {
        super.postSyncAllOrders(...arguments);
        for (const order of orders) {
            if (order.config.l10n_do_fiscal_journal) {
                order.set_l10n_do_fiscal_data(order.raw);
            }
        }
    },

    // Get credit note by NCF
    async get_credit_note(ncf) {
        return this.data.call(
            "pos.order",
            "get_credit_note",
            [false, ncf]
        );
    },

    // Get all credit notes for a partner
    async get_credit_notes(partnerId) {
        return this.data.call(
            "pos.order",
            "get_credit_notes",
            [false, partnerId]
        );
    },
});
