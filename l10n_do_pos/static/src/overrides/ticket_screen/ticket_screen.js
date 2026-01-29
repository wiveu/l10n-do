/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(TicketScreen.prototype, {
    // Override refund handling for fiscal compliance
    async onDoRefund() {
        if (!this.pos.config.l10n_do_fiscal_journal) {
            return super.onDoRefund(...arguments);
        }

        const order = this.getSelectedOrder();

        if (!order) {
            this.state.ui.highlightHeaderNote = !this.state.ui.highlightHeaderNote;
            return;
        }

        // Check order has NCF
        if (!order.ncf) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("This order has no NCF"),
            });
            return;
        }

        // Check B04 (credit note) fiscal type exists
        const creditNoteFiscalType = this.pos.get_fiscal_type_by_prefix("B04");
        if (!creditNoteFiscalType) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("The fiscal type credit note does not exist. Please activate or configure it."),
            });
            return;
        }

        // Check credit note payment method exists
        const creditNotePaymentMethod = this.pos.get_credit_note_payment_method();
        if (!creditNotePaymentMethod) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("There are no credit note payment method configured."),
            });
            return;
        }

        // Call parent refund method
        await super.onDoRefund(...arguments);
    },

    // Override to set fiscal type and NCF origin after refund is created
    async _onCloseScreen() {
        if (!this.pos.config.l10n_do_fiscal_journal) {
            return super._onCloseScreen(...arguments);
        }

        const newOrder = this.pos.get_order();
        const originalOrder = this.getSelectedOrder();

        // Check if this is a refund order
        if (newOrder && originalOrder && newOrder._isRefundAndSaleOrder && newOrder._isRefundAndSaleOrder() && originalOrder.ncf) {
            try {
                // Set B04 fiscal type for credit notes
                const creditNoteFiscalType = this.pos.get_fiscal_type_by_prefix("B04");
                const creditNotePaymentMethod = this.pos.get_credit_note_payment_method();

                // Set fiscal type
                newOrder.set_fiscal_type(creditNoteFiscalType);

                // Set NCF origin (the original invoice being refunded)
                newOrder.set_ncf_origin_out(originalOrder);

                // Check if order is older than 30 days - may need tax removal
                const orderDate = new Date(originalOrder.date_order || originalOrder.validation_date);
                const currentDate = new Date();
                const timeDiffDays = (currentDate - orderDate) / (1000 * 60 * 60 * 24);

                if (timeDiffDays > 30) {
                    // For orders older than 30 days, ITBIS should be removed
                    // This is handled by setting a fiscal position that removes taxes
                    // or by clearing tax_ids on order lines
                    newOrder.lines.forEach(line => {
                        // Clear ITBIS taxes for old refunds
                        if (line.tax_ids) {
                            line.tax_ids = line.tax_ids.filter(tax => {
                                const taxRecord = this.pos.models["account.tax"]?.find(t => t.id === tax.id);
                                return !(taxRecord && taxRecord.tax_group_id && taxRecord.tax_group_id[1] === "ITBIS");
                            });
                        }
                    });
                }

                // Add credit note payment method
                if (creditNotePaymentMethod) {
                    newOrder.add_paymentline(creditNotePaymentMethod);
                }

                // Navigate to payment screen
                this.pos.showScreen("PaymentScreen");
                return;

            } catch (error) {
                // If error, clean up and rethrow
                this.pos.add_new_order();
                this.pos.removeOrder(newOrder);
                throw error;
            }
        }

        return super._onCloseScreen(...arguments);
    },

    // Get search fields - add NCF column
    _getSearchFields() {
        const fields = super._getSearchFields ? super._getSearchFields(...arguments) : {};

        if (this.pos.config.l10n_do_fiscal_journal) {
            fields.NCF = {
                repr: (order) => order.ncf || "",
                displayName: _t("NCF"),
                modelField: "ncf",
            };
        }

        return fields;
    },

    // Refund all products in the order
    async refundAllOrder() {
        const order = this.getSelectedOrder();

        if (!order) {
            return;
        }

        // Check NCF exists
        if (this.pos.config.l10n_do_fiscal_journal && !order.ncf) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("This order has no NCF"),
            });
            return;
        }

        // Select all lines for refund with maximum refundable quantity
        for (const line of order.lines) {
            const toRefundDetail = this._getToRefundDetail(line);
            if (toRefundDetail) {
                const refundableQty = toRefundDetail.line.qty - (toRefundDetail.line.refundedQty || 0);
                if (refundableQty > 0) {
                    toRefundDetail.qty = refundableQty;
                }
            }
        }

        // Trigger the refund
        await this.onDoRefund();
    },
});
