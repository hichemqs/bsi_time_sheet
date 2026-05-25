from odoo import models, api
from odoo.addons.base.models.avatar_mixin import get_hsl_from_seed
from odoo.tools import html_escape
from base64 import b64encode
import logging

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # def _check_inactive_employees(self):
    #     """Mark employees inactive if last login exceeds configured days."""
    #     param = self.env['ir.config_parameter'].sudo()
    #     days = int(param.get_param('bs_crm.nombre_jours_inactifs'))
    #     cutoff_date = fields.Datetime.now() - timedelta(days=days)

    #     users = self.env['res.users'].search([('login_date', '<', cutoff_date)])
    #     employees = users.mapped('employee_ids')

    #     for employee in employees:
    #         if employee.active:
    #             employee.write({'active': False})


    def _generate_svg_avatar(self, name):
        initials = '?'
        if name and name.strip():
            parts = name.strip().split()
            if len(parts) >= 2:
                initials = f"{parts[0].capitalize()} {parts[1][0].upper()}"
            else:
                initials = name.strip().capitalize()

        length = len(initials)
        if length <= 5:
            font_size = 48
        elif length <= 7:
            font_size = 42
        elif length <= 9:
            font_size = 36
        else:
            font_size = 22

        bgcolor = get_hsl_from_seed(name or '')
        svg = (
            "<?xml version='1.0' encoding='UTF-8' ?>"
            "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
            f"<rect width='180' height='180' fill='{bgcolor}'/>"
            f"<text x='50%' y='55%' text-anchor='middle' "
            f"dominant-baseline='middle' "
            f"font-family='Arial, sans-serif' font-size='{font_size}' "
            f"fill='#ffffff'>{html_escape(initials)}</text>"
            "</svg>"
        )
        return b64encode(svg.encode())

    def _apply_avatar(self, employee):
        avatar = self._generate_svg_avatar(employee.name or '')
        employee.sudo().write({'image_1920': avatar})

        if employee.user_id and employee.user_id.partner_id:
            employee.user_id.partner_id.sudo().write({'image_1920': avatar})

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for employee in employees:
            self._apply_avatar(employee)
        return employees

    def write(self, vals):
        result = super().write(vals)
        if 'name' in vals:
            for employee in self:
                self._apply_avatar(employee)
        return result