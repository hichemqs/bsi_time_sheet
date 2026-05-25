from odoo import models, api
from odoo.osv import expression

LOST_STAGES = ['perdu', 'abandonnee']


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model_create_multi
    def create(self, vals_list):
        lost_order_ids = set(
            self.env['sale.order'].search([
                ('stag_id', 'in', LOST_STAGES)
            ]).ids
        )

        if lost_order_ids:
            vals_list = [
                v for v in vals_list
                if not (
                    v.get('res_model') == 'sale.order'
                    and v.get('res_id') in lost_order_ids
                )
            ]

        if not vals_list:
            return self.browse()

        return super().create(vals_list)

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        soumission_order_ids = self.env['sale.order'].search([
            ('stag_id', '=', 'soumission')
        ]).ids
    
        exclude_domain = [
            '|',
                ('res_model', '!=', 'sale.order'),
            '&',
                ('res_model', '=', 'sale.order'),
                ('res_id', 'in', soumission_order_ids),
        ]
        domain = expression.AND([domain or [], exclude_domain])
    
        return super().search(domain, offset=offset, limit=limit, order=order)