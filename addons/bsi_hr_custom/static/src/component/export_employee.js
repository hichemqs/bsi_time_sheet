/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { Component } from  "@odoo/owl";

export async function ExportEmployees (ev, action){
    const params = action.params || {};
    await download({
        data: {
            data: JSON.stringify(params),
        },
        url: `/employee/export/xlsx`,
    });
}


registry.category("actions").add("bsi_hr_custom.export_employees", ExportEmployees);

