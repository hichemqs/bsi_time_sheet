from odoo import models
import re

_FOOTER_REGEX = re.compile(
    r'<div style="margin-top:32px;">.*?<\/div>|'
    r'<div style="color:\s*#555555;\s*font-size:11px;">.*?<\/div>',
    re.DOTALL
)


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def action_open_related_document(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_notify(self):
        if self.res_model == 'sale.order':
            return
        super().action_notify()


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _personalize_outgoing_body(self, body, partner=False, recipients_follower_status=None):
        body = super()._personalize_outgoing_body(body, partner=partner, recipients_follower_status=recipients_follower_status)
        if self.model == 'sale.order':
            body = re.sub(_FOOTER_REGEX, '', body)
        return body
