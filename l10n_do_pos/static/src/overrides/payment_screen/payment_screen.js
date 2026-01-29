/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },

    // Fiscal type selection popup
    async selectFiscalType() {
        if (!this.pos.config.l10n_do_fiscal_journal) {
            return;
        }

        const fiscalTypes = this.pos.fiscal_types.filter(ft => ft.type === "out_invoice");
        const currentFiscalType = this.currentOrder.fiscal_type;

        const list = fiscalTypes.map(ft => ({
            id: ft.id,
            label: `${ft.prefix} - ${ft.name}`,
            item: ft,
            isSelected: currentFiscalType ? ft.id === currentFiscalType.id : false,
        }));

        const selectedFiscalType = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Select Fiscal Type"),
            list: list,
        });

        if (selectedFiscalType) {
            // If requires_document and no partner VAT, prompt for RNC
            if (selectedFiscalType.requires_document) {
                const partner = this.currentOrder.partner_id;
                if (!partner || !partner.vat) {
                    await this.promptForRnc(selectedFiscalType);
                    return;
                }
            }
            this.currentOrder.set_fiscal_type(selectedFiscalType);
        }
    },

    // Prompt for RNC/Cedula input
    async promptForRnc(fiscalType) {
        const rnc = await makeAwaitable(this.dialog, TextInputPopup, {
            title: _t("RNC or Cedula"),
            placeholder: _t("Enter 9 digits for RNC or 11 for Cedula"),
        });

        if (!rnc) {
            return;
        }

        const cleanRnc = rnc.replace(/[-\s]/g, "");

        // Validate format
        if (!/^\d+$/.test(cleanRnc) || (cleanRnc.length !== 9 && cleanRnc.length !== 11)) {
            this.dialog.add(AlertDialog, {
                title: _t("This not RNC or Cedula"),
                body: _t("Please ensure the RNC has exactly 9 digits or the Cedula has 11 digits"),
            });
            return;
        }

        // Try to find existing partner with this VAT
        const existingPartner = this.pos.models["res.partner"].find(
            p => p.vat && p.vat.replace(/[-\s]/g, "") === cleanRnc
        );

        if (existingPartner) {
            this.currentOrder.set_partner(existingPartner);
            this.currentOrder.set_fiscal_type(fiscalType);
        } else {
            // Open partner list to create new partner
            const { confirmed, payload: newPartner } = await this.pos.showTempScreen(
                "PartnerListScreen",
                { partner: null }
            );
            if (confirmed && newPartner) {
                this.currentOrder.set_partner(newPartner);
                this.currentOrder.set_fiscal_type(fiscalType);
            }
        }
    },

    // Override validateOrder to add fiscal validations
    async validateOrder(isForceValidate) {
        if (!this.pos.config.l10n_do_fiscal_journal) {
            return super.validateOrder(...arguments);
        }

        const order = this.currentOrder;
        const total = order.get_total_with_tax();
        const fiscalType = order.fiscal_type;
        const partner = order.partner_id;

        // Validation: No zero sales
        if (total === 0) {
            this.dialog.add(AlertDialog, {
                title: _t("Sale in"),
                body: _t("You cannot make sales in 0, please add a product with value"),
            });
            return;
        }

        // Validation: Check for zero quantity products
        const zeroQtyProducts = order.lines.filter(line => line.qty === 0);
        if (zeroQtyProducts.length > 0) {
            const productNames = zeroQtyProducts.map(l => l.product_id.display_name).join(", ");
            this.dialog.add(AlertDialog, {
                title: _t("Zero Quantity Products"),
                body: _t("The following products have zero quantity in the order: %s. Please remove them or set a valid quantity.", productNames),
            });
            return;
        }

        // Validation: Fiscal type is required
        if (!fiscalType) {
            this.dialog.add(AlertDialog, {
                title: _t("Required fiscal type"),
                body: _t("Please select a fiscal type"),
            });
            return;
        }

        // Validation: Partner required for fiscal types that require document
        if (fiscalType.requires_document && !partner) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("For invoice fiscal type %s its necessary customer, please select customer", fiscalType.name),
            });
            return;
        }

        // Validation: VAT required for fiscal types that require document
        if (fiscalType.requires_document && partner && !partner.vat) {
            this.dialog.add(AlertDialog, {
                title: _t("Required document (RNC/Cedula)"),
                body: _t("For invoice fiscal type %s it is necessary for the customer have RNC or Cedula", fiscalType.name),
            });
            return;
        }

        // Validation: VAT format
        if (fiscalType.requires_document && partner && partner.vat) {
            const vat = partner.vat.replace(/[-\s]/g, "");
            if (!/^\d+$/.test(vat) || (vat.length !== 9 && vat.length !== 11)) {
                this.dialog.add(AlertDialog, {
                    title: _t("Incorrect document (RNC/Cedula)"),
                    body: _t("For invoice fiscal type %s it is necessary for the customer have correct RNC or Cedula without dashes or spaces", fiscalType.name),
                });
                return;
            }
        }

        // Validation: Sales > 250,000 DOP require customer ID
        if (total > 250000 && !partner) {
            this.dialog.add(AlertDialog, {
                title: _t("Sale greater than RD$ 250,000.00"),
                body: _t("For this sale it is necessary for the customer have ID"),
            });
            return;
        }

        // Analyze payment methods for restrictions
        if (!await this.analyzePaymentMethods()) {
            return;
        }

        // Generate NCF before completing the order
        if (!order.ncf) {
            try {
                await this.getFiscalData();
            } catch (error) {
                this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: error.message || _t("Error generating NCF"),
                });
                return;
            }
        }

        return super.validateOrder(...arguments);
    },

    // Analyze payment method combinations
    async analyzePaymentMethods() {
        const order = this.currentOrder;
        const paymentLines = order.payment_ids;
        const total = order.get_total_with_tax();

        const hasCard = paymentLines.some(pl => pl.payment_method_id.type === "bank");
        const hasCash = paymentLines.some(pl => pl.payment_method_id.type === "cash");
        const hasPayLater = paymentLines.some(pl => pl.payment_method_id.type === "pay_later");

        const cardAmount = paymentLines
            .filter(pl => pl.payment_method_id.type === "bank")
            .reduce((sum, pl) => sum + pl.amount, 0);

        const payLaterAmount = paymentLines
            .filter(pl => pl.payment_method_id.type === "pay_later")
            .reduce((sum, pl) => sum + pl.amount, 0);

        // Validation: Card payment cannot exceed total
        if (hasCard && cardAmount > total) {
            this.dialog.add(AlertDialog, {
                title: _t("Card payment"),
                body: _t("Card payments cannot exceed the total order"),
            });
            return false;
        }

        // Validation: Pay later cannot exceed total
        if (hasPayLater && payLaterAmount > total) {
            this.dialog.add(AlertDialog, {
                title: _t("Pay later payment"),
                body: _t("Pay later payment cannot exceed the total order"),
            });
            return false;
        }

        // Validation: Card + Pay later sum cannot exceed total
        if (hasCard && hasPayLater && (cardAmount + payLaterAmount) > total) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("The sum for Card and Pay Later payment cannot exceed the total order."),
            });
            return false;
        }

        // Validation: Card covers total but cash also present
        if (hasCard && hasCash && cardAmount >= total) {
            this.dialog.add(AlertDialog, {
                title: _t("Card and cash payment"),
                body: _t("The total payment with the card is sufficient to pay the order, please eliminate the payment in cash or reduce the amount to be paid by card"),
            });
            return false;
        }

        // Validation: Pay later covers total but cash also present
        if (hasPayLater && hasCash && payLaterAmount >= total) {
            this.dialog.add(AlertDialog, {
                title: _t("Pay later and cash payment"),
                body: _t("The total payment with the pay later is sufficient to pay the order, please eliminate the payment in cash or reduce the amount to be paid by pay later"),
            });
            return false;
        }

        return true;
    },

    // Get fiscal data (NCF) from server
    async getFiscalData() {
        const order = this.currentOrder;

        const fiscalData = await this.orm.call(
            "pos.order",
            "get_next_fiscal_sequence",
            [
                false,
                order.fiscal_type.id,
                this.pos.company.id,
                [],
                JSON.stringify(order.serialize())
            ]
        );

        order.set_l10n_do_fiscal_data(fiscalData);
    },

    // Override addNewPaymentLine for credit note handling
    async addNewPaymentLine(paymentMethod) {
        if (!this.pos.config.l10n_do_fiscal_journal) {
            return super.addNewPaymentLine(...arguments);
        }

        // Check if this is a credit note payment method
        if (paymentMethod.is_credit_note) {
            await this.handleCreditNotePayment(paymentMethod);
            return;
        }

        return super.addNewPaymentLine(...arguments);
    },

    // Handle credit note payment
    async handleCreditNotePayment(paymentMethod) {
        const order = this.currentOrder;
        const partner = order.partner_id;

        if (!partner) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Please select a customer first"),
            });
            return;
        }

        // Prompt for NCF or show list of credit notes
        const ncfInput = await makeAwaitable(this.dialog, TextInputPopup, {
            title: _t("Select Credit Note"),
            placeholder: _t("Please enter the NCF"),
        });

        if (!ncfInput) {
            return;
        }

        try {
            // Validate credit note
            const creditNote = await this.orm.call(
                "pos.order",
                "get_credit_note",
                [false, ncfInput]
            );

            if (!creditNote) {
                this.dialog.add(AlertDialog, {
                    title: _t("Error in credit note"),
                    body: _t("Credit note not found"),
                });
                return;
            }

            if (creditNote.residual_amount <= 0) {
                this.dialog.add(AlertDialog, {
                    title: _t("Error in credit note"),
                    body: _t("Credit note %s has no available amount.", ncfInput),
                });
                return;
            }

            // Check partner matches
            if (creditNote.partner_id !== partner.id) {
                this.dialog.add(AlertDialog, {
                    title: _t("Credit Note Partner Mismatch"),
                    body: _t("The customer associated with the credit note does not match the customer on the order. Please select the correct customer."),
                });
                return;
            }

            // Add credit note payment line
            const paymentLine = order.add_paymentline(paymentMethod);
            const amount = Math.min(creditNote.residual_amount, order.get_due());
            paymentLine.set_amount(amount);
            paymentLine.credit_note_ncf = ncfInput;
            paymentLine.credit_note_partner_id = creditNote.partner_id;

        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: error.message || _t("There is an error with the payment of credit note, please delete the payment of the credit note and enter it again."),
            });
        }
    },

    // Prevent editing credit note payment lines
    selectPaymentLine(paymentLine) {
        if (paymentLine.payment_method_id.is_credit_note) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("You cannot edit a credit note payment line"),
            });
            return;
        }
        return super.selectPaymentLine(...arguments);
    },
});
