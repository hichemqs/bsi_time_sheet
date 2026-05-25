from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    allowed_sector_ids = fields.Many2many('hr.sector', string="Secteurs autorisés", domain="[('company_ids', 'in', company_ids)]")

    def write(self, vals):
        if 'allowed_sector_ids' in vals:
            self.env.registry.clear_cache()
        return super().write(vals)

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['allowed_sector_ids']

    @property
    def SELF_WRITABLE_FIELDS(self):
        return super().SELF_WRITABLE_FIELDS + ['allowed_sector_ids']
