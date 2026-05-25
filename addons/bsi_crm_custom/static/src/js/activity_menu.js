/** @odoo-module **/

import { ActivityMenu } from "@mail/core/web/activity_menu";
import { patch } from "@web/core/utils/patch";
import { Domain } from "@web/core/domain";

patch(ActivityMenu.prototype, {

    availableViews(group) {
        if (group.model === "sale.order" && group.view_id) {
            return [
                [group.view_id, "list"],
                [false, "form"],
                [false, "kanban"],
                [false, "activity"],
            ];
        }
        return super.availableViews(group);
    },

    openActivityGroup(group, filter = "all") {
        if (group.model !== "sale.order") {
            return super.openActivityGroup(group, filter);
        }

        document.body.click();

        const context = {
            force_search_count: 1,
            create: false,
            no_create: true,
        };

        if (filter === "all") {
            context.search_default_activities_overdue = 1;
            context.search_default_activities_today = 1;
        } else if (filter === "overdue") {
            context.search_default_activities_overdue = 1;
        } else if (filter === "today") {
            context.search_default_activities_today = 1;
        } else if (filter === "upcoming_all") {
            context.search_default_activities_upcoming_all = 1;
        }

        let domain = [
            ["activity_user_id", "=", this.userId],
            ["stag_id", "not in", ["perdu", "abandonnee"]],
        ];

        if (group.domain) {
            domain = Domain.and([domain, group.domain]).toList();
        }

        this.action.doAction(
            {
                context,
                domain,
                name: "Soumissions",
                res_model: group.model,
                search_view_id: [false],
                type: "ir.actions.act_window",
                views: this.availableViews(group),
            },
            {
                clearBreadcrumbs: true,
                viewType: group.view_type,
            }
        );
    },
});