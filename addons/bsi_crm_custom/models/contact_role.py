from odoo import models, fields, api

class ContactRole(models.Model):
    _name = 'contact.role'
    _description = 'Contact Role'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    
    parent_id = fields.Many2one('contact.role', string='Parent Role', index=True, ondelete='restrict')
    parent_path = fields.Char(index=True)
    
    child_ids = fields.One2many('contact.role', 'parent_id', string='Child Roles')
    
    complete_name = fields.Char(string='Full Name', compute='_compute_complete_name', store=True, recursive=True)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for role in self:
            if role.parent_id:
                role.complete_name = f"{role.parent_id.complete_name} / {role.name}"
            else:
                role.complete_name = role.name
