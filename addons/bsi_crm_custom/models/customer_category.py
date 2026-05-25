# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartnerCustomerCategory(models.Model):
    _name = 'res.partner.customer.category'
    _description = 'Customer category'

    name = fields.Char('Nom')
    type = fields.Selection([('person', 'Individual'), ('company', 'Company')], string="Type")
    client_marchand = fields.Boolean('Client Marchand')
    is_default = fields.Boolean('Par défault')
