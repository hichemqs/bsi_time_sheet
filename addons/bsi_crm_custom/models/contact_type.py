from odoo import models, fields

class ContactType(models.Model):
    _name = 'contact.type'
    _description = 'Contact Type'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')