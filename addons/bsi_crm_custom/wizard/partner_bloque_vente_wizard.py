# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import escape as html_escape


class PartnerBloqueWizard(models.TransientModel):
    _name = 'partner.bloque.vente.wizard'
    _description = 'Partner Sales Block Wizard'

    reason = fields.Text(string="Raison de Blocage", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)

    def confirm_block(self):
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_("Only Sales Managers can perform this action."))

        block_type = self.env.context.get('block_type')
        # if not self.partner_id.is_closed:
        #     raise UserError("The partner must be closed to perform this action.")

        if block_type == 'credit':
            self.partner_id.credit_blocked = not self.partner_id.credit_blocked
            title = "<span style='background-color:red;'>Bloqué Crédit</span>"
        elif block_type == 'sale':
            self.partner_id.sale_blocked = not self.partner_id.sale_blocked
            title = "<span style='background-color:red;'>Bloqué Vente</span>"
        else:
            raise UserError("Unknown block type.")

        reason_html = html_escape(self.reason) if self.reason else ''

        self.partner_id.message_post(
            body=f"""
                <span>{title}. <strong>Raison :</strong>{reason_html}</span>
            """,
            subtype_xmlid='mail.mt_note',
            body_is_html=True
        )

        return {'type': 'ir.actions.act_window_close'}