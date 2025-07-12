/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { Component, markup } from "@odoo/owl";

export class UrlDgiiReportsWidget extends CharField {
    
    get displayedValue() {
        const value = this.props.record.data[this.props.name];
        if (!value) {
            return "";
        }
        
        if (this.props.readonly) {
            const href = `dgii_reports/${value}`;
            const linkHtml = `<a href="${href}" target="_blank" class="o_form_uri o_text_overflow">${value}</a>`;
            return markup(linkHtml);
        }
        
        return value;
    }
}

registry.category("fields").add("dgii_reports_url", UrlDgiiReportsWidget);
