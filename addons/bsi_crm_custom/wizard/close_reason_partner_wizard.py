# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PartnerClosureReasonWizard(models.TransientModel):
    _name = 'partner.closure.reason.wizard'
    _description = 'Partner close reason wizard'

    close_reason_id = fields.Many2one('partner.closure.reason', string="Closure reason", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    partner_ids = fields.Many2many('res.partner', string="Partners")

    def action_close_partner(self):
        partners = self.partner_ids | self.partner_id
        if not partners:
            raise UserError(_("No partners selected."))

        partners.write({
            'closure_reason_id': self.close_reason_id.id,
            'is_closed': True,
        })
        for partner in partners:
            partner.message_post(body=_('Client record closed. Reason: %s', self.close_reason_id.name))
