/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { companyService } from "@web/webclient/company_service";
import { cookie } from "@web/core/browser/cookie";
import { session } from "@web/session";

patch(companyService, {
    start(env, deps) {
        const hash = deps.router.current.hash;
        const cidsCookie = cookie.get("cids");
        if (!("cids" in hash) && !cidsCookie) {
            

            const allCompanyIds = Object.keys(session.user_companies.allowed_companies);

            cookie.set("cids", allCompanyIds.join(","));
        }

        return super.start(...arguments);
    }
});