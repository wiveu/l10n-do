/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

// Patch PosStore to load fiscal types
patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.fiscal_types = [];
    },

    async _processData(loadedData) {
        await super._processData(...arguments);
        if (loadedData["account.fiscal.type"]) {
            this.fiscal_types = loadedData["account.fiscal.type"];
        }
    },

    get_fiscal_type_by_id(id) {
        const fiscal_type = this.fiscal_types.find((ft) => ft.id === id);
        if (!fiscal_type) {
            return this.get_fiscal_type_by_prefix("B02");
        }
        return fiscal_type;
    },

    get_fiscal_type_by_prefix(prefix) {
        const fiscal_type = this.fiscal_types.find((ft) => ft.prefix === prefix);
        if (!fiscal_type) {
            console.warn(_t("Fiscal type not found: %s"), prefix);
            return false;
        }
        return fiscal_type;
    },
});

// Patch PosOrder for fiscal data
patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);

        // Initialize fiscal fields
        if (this.config?.l10n_do_fiscal_journal) {
            this.ncf = vals.ncf || "";
            this.ncf_origin_out = vals.ncf_origin_out || "";
            this.ncf_expiration_date = vals.ncf_expiration_date || "";
            this.fiscal_type_id = vals.fiscal_type_id || false;
            this.fiscal_sequence_id = vals.fiscal_sequence_id || false;
            this.fiscal_type = vals.fiscal_type || null;

            // Set fiscal type from partner or default to B02 (with safety check)
            const pos = this.models?.pos;
            if (pos?.get_fiscal_type_by_prefix) {
                const partner = this.partner_id;
                if (partner && partner.sale_fiscal_type_id) {
                    this.set_fiscal_type(pos.get_fiscal_type_by_id(partner.sale_fiscal_type_id[0]));
                } else {
                    this.set_fiscal_type(pos.get_fiscal_type_by_prefix("B02"));
                }
            }
        }
    },

    set_fiscal_type(fiscal_type) {
        if (!fiscal_type) return;
        this.fiscal_type = fiscal_type;
        this.fiscal_type_id = fiscal_type.id;

        // Set fiscal position if available
        if (fiscal_type.fiscal_position_id) {
            const fp = this.models["account.fiscal.position"]?.find(
                (p) => p.id === fiscal_type.fiscal_position_id[0]
            );
            if (fp) {
                this.fiscal_position_id = fp;
                // Recompute prices for all lines
                this.lines.forEach((line) => line.setLinePrice());
            }
        }
    },

    get_fiscal_type() {
        return this.fiscal_type;
    },

    set_partner(partner) {
        super.set_partner(...arguments);

        if (this.config?.l10n_do_fiscal_journal) {
            const pos = this.models?.pos;
            if (pos?.get_fiscal_type_by_prefix) {
                if (partner && partner.sale_fiscal_type_id) {
                    this.set_fiscal_type(pos.get_fiscal_type_by_id(partner.sale_fiscal_type_id[0]));
                } else {
                    this.set_fiscal_type(pos.get_fiscal_type_by_prefix("B02"));
                }
            }
        }
    },

    set_l10n_do_fiscal_data(fiscal_data) {
        this.ncf = fiscal_data.ncf;
        this.ncf_expiration_date = fiscal_data.ncf_expiration_date;
        this.fiscal_sequence_id = fiscal_data.fiscal_sequence_id;
    },

    set_ncf_origin_out(origin_order) {
        this.ncf_origin_out = origin_order.ncf;
    },

    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);

        // Add fiscal journal flag
        result.l10n_do_fiscal_journal = this.config?.l10n_do_fiscal_journal || false;

        // Add fiscal data if fiscal journal is enabled
        if (this.config?.l10n_do_fiscal_journal) {
            result.ncf = this.ncf || "";
            result.ncf_origin_out = this.ncf_origin_out || "";
            result.ncf_expiration_date = this.ncf_expiration_date || "";
            result.fiscal_type = this.fiscal_type || null;
            result.partner = this.partner_id
                ? {
                      name: this.partner_id.name,
                      vat: this.partner_id.vat,
                      street: this.partner_id.street,
                      street2: this.partner_id.street2,
                      city: this.partner_id.city,
                      state_id: this.partner_id.state_id,
                      zip: this.partner_id.zip,
                      country_id: this.partner_id.country_id,
                  }
                : null;
        }

        return result;
    },

    serialize(options) {
        const json = super.serialize(...arguments);
        if (this.config?.l10n_do_fiscal_journal) {
            json.ncf = this.ncf;
            json.ncf_origin_out = this.ncf_origin_out;
            json.ncf_expiration_date = this.ncf_expiration_date;
            json.fiscal_type_id = this.fiscal_type_id;
            json.fiscal_sequence_id = this.fiscal_sequence_id;
        }
        return json;
    },
});

// Patch PosOrderline for ITBIS calculation
patch(PosOrderline.prototype, {
    getDisplayData() {
        const result = super.getDisplayData(...arguments);

        // Add ITBIS (Dominican VAT) amount
        if (this.order_id?.config?.l10n_do_fiscal_journal) {
            result.l10n_do_itbis = this.get_itbis();
        }

        return result;
    },

    get_itbis() {
        let itbis = 0;
        const tax_details = this.get_tax_details();

        for (const tax_id in tax_details) {
            const tax = this.models["account.tax"]?.find((t) => t.id === parseInt(tax_id));
            if (tax && tax.tax_group_id && tax.tax_group_id[1] === "ITBIS") {
                itbis += tax_details[tax_id].amount;
            }
        }

        return itbis;
    },
});
