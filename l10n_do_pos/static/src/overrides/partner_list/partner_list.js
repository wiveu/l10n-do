/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";

patch(PartnerList.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },

    // Override saveChanges to handle RNC auto-lookup
    async saveChanges(props) {
        if (!this.pos.config.l10n_do_fiscal_journal) {
            return super.saveChanges(...arguments);
        }

        const processedChanges = props.changes || props;

        // Check if the name field looks like an RNC or Cedula
        const nameOrRnc = (processedChanges.name || "").replace(/[-\s]/g, "");

        if (/^\d{9}$|^\d{11}$/.test(nameOrRnc)) {
            // This looks like an RNC (9 digits) or Cedula (11 digits)
            try {
                // Set the VAT field
                processedChanges.vat = nameOrRnc;

                // Set country to Dominican Republic if company is Dominican
                if (this.pos.company.country_id) {
                    processedChanges.country_id = this.pos.company.country_id.id;
                }

                // The backend create_from_ui method will handle the DGII lookup
                // and auto-populate the name field

            } catch (error) {
                this.dialog.add(AlertDialog, {
                    title: _t("Offline"),
                    body: _t("Unable to save changes."),
                });
                return false;
            }
        }

        return super.saveChanges(props);
    },

    // Get placeholder text for search
    get searchBarConfig() {
        const config = super.searchBarConfig;

        if (this.pos.config.l10n_do_fiscal_journal) {
            config.placeholder = _t("Name or RNC / Cedula");
        }

        return config;
    },
});
