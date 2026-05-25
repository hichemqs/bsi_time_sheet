# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools, Command
from lxml import etree
from lxml.html import builder as html


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    allowed_partner_ids = fields.Many2many('res.partner', compute='_compute_allowed_partner_ids')
    partner_ids = fields.Many2many(domain="[('id', 'in', allowed_partner_ids)]")

    def _compute_attachment_ids(self):
        super(MailComposer, self)._compute_attachment_ids()
        if self._context.get('send_order_report'):
            active_model = self._context.get('active_model')
            order_id = self.env[active_model].browse(self._context.get('active_id'))
            # quotation_not_finalized = self.env.ref('bsi_crm_custom.quotation_not_finalized')
            quotation_finalized = self.env.ref('bsi_crm_custom.quotation_finalized')
            contract_finalized = self.env.ref('bsi_crm_custom.contract_finalized')

            field_mapping = {
                # quotation_not_finalized.id: ['soummision_non_finalise', order_id.snf_file_name],
                quotation_finalized.id: ['soummision_finalise', order_id.sf_file_name],
                contract_finalized.id: ['contrat_finalise', order_id.cf_file_name],
            }
            for composer in self:
                template_field = field_mapping.get(composer.template_id.id)
                if template_field:
                    attachment = self.env['ir.attachment'].search([
                        ('res_model', '=', active_model),
                        ('res_id', '=', order_id.id),
                        ('res_field', '=', template_field[0]),
                    ], limit=1)
                    if not attachment:
                        composer.attachment_ids = False
                        continue
                    attachment.write({'name': template_field[1]})
                    composer.attachment_ids = [(6, 0, [attachment.id])]

    @api.depends('model')
    def _compute_allowed_partner_ids(self):
        for record in self:
            if record.model == 'sale.order':
                order_id = self.env[self.model].browse(self._context.get('active_id'))
                contact_lines = order_id.contact_lines.mapped('contact_id')
                record.allowed_partner_ids = contact_lines
            else:
                record.allowed_partner_ids = self.env['res.partner'].search([])

    def _prepare_mail_values(self, res_ids):
        mail_values = super(MailComposer, self)._prepare_mail_values(res_ids)
        if self._context.get('send_order_report'):
            for mail_value in mail_values.values():
                mail_value.update({'author_id': self.env.user.partner_id.id})
        return mail_values

    def action_send_mail(self):
        res = super(MailComposer, self.with_context({**self.env.context, 'template_id': self.mapped('template_id').ids})).action_send_mail()
        quotation_finalized = self.env.ref('bsi_crm_custom.quotation_finalized')
        contract_finalized = self.env.ref('bsi_crm_custom.contract_finalized')
        for wizard in self:
            if wizard.model != 'sale.order':
                continue
            order_id = self.env[wizard.model].browse(self.env.context.get('active_id'))
            if not order_id:
                continue

            if wizard.template_id.id == quotation_finalized.id:
                order_id.soumission_envoye = True
            elif wizard.template_id.id == contract_finalized.id:
                order_id.contrat_envoye = True
        return res

# class Invite(models.TransientModel):
#     _inherit = 'mail.wizard.invite'
#
#     @api.model
#     def default_get(self, fields):
#         result = super(Invite, self).default_get(fields)
#         if 'message' not in fields:
#             return result
#
#         user_name = self.env.user.display_name
#         model = result.get('res_model')
#         res_id = result.get('res_id')
#         if model and res_id:
#             document = self.env['ir.model']._get(model).display_name
#             title = self.env[model].browse(res_id).display_name
#             msg_fmt = _('%(user_name)s invited you to follow %(document)s document: %(title)s')
#         else:
#             msg_fmt = _('%(user_name)s invited you to follow a new document.')
#
#         if model == 'sale.order' and res_id:
#             msg_fmt = '%(user_name)s Vous' % (user_name, )
#             message = html.DIV(
#                 html.P(_('Hello,')),
#                 html.P(text)
#             )
#         result['message'] = etree.tostring(message)
#         return result