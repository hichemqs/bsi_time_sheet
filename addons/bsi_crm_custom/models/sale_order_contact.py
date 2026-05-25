from odoo import models, fields, api, _


class SaleOrderContact(models.Model):
    _name = 'sale.order.contact'
    _order = 'is_merchant, id'

    order_id = fields.Many2one('sale.order', string="Order", ondelete='cascade', required=True)
    company_id = fields.Many2one('res.partner', string="Société")
    contact_id = fields.Many2one('res.partner', string="Contact", ondelete='restrict')
    role_du_contact = fields.Many2one('contact.role', string="Rôle du contact")
    phone = fields.Char(string="Téléphone", related='contact_id.phone', store=True)
    email = fields.Char(string="E-mail", related='contact_id.email')
    is_delivery = fields.Boolean("Contact livraison")
    is_merchant = fields.Boolean(string="Est un marchand",compute="_compute_is_merchant",store=True)
    
    @api.depends("contact_id","contact_id.parent_id","contact_id.parent_id.customer_categ_id","contact_id.parent_id.customer_categ_id.client_marchand","contact_id.customer_categ_id","contact_id.customer_categ_id.client_marchand")
    def _compute_is_merchant(self):
        for rec in self:
            partner_to_check = rec.contact_id.parent_id or rec.contact_id
            rec.is_merchant = bool(partner_to_check.customer_categ_id
                and partner_to_check.customer_categ_id.client_marchand
            )
            
    @api.onchange("contact_id")
    def _onchange_contact_id(self):
        for line in self:
            if not line.contact_id:
                line.role_du_contact = False
                line.phone = False
                line.email = False
                continue
    
            line.phone = line.contact_id.phone
            line.email = line.contact_id.email
            line.role_du_contact = line.contact_id.popup_contact_type_id or False

    # @api.onchange('contact_id')
    # def _onchange_contact_id_set_company(self):
    #     for rec in self:
    #         if rec.contact_id:
    #             rec.company_id = rec.contact_id.parent_id.id
    #         else:
    #             rec.company_id = False
