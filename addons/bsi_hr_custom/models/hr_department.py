# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = "hr.department"

    responsible_id = fields.Many2one('hr.employee', 'Responsable de paie', tracking=True)
    code_dep = fields.Char(string='Code du Département', tracking=True)
    sector_id = fields.Many2one('hr.sector', string='Secteur', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', compute='_compute_company_id', store=True, tracking=True)
    code_centre_cout = fields.Char('Centre de coût')
    description_centre_cout = fields.Text('Description centre de coût')

    @api.depends('sector_id')
    def _compute_company_id(self):
        for department in self:
            department.company_id = department.sector_id.company_ids[0] if department.sector_id and department.sector_id.company_ids else False

    @api.depends('code_dep')
    @api.depends_context('show_dep_code')
    def _compute_display_name(self):
        if not self.env.context.get('show_dep_code'):
            return super()._compute_display_name()

        for department in self:
            department.display_name = department.code_dep
