# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrSector(models.Model):
    _name = 'hr.sector'
    _description = 'Hr Sector'

    name = fields.Char('Nom du secteur',tracking=True)
    sector_no = fields.Char("Société Paie", required=True,tracking=True)
    company_ids = fields.Many2many('res.company', string='Companies', tracking=True ,default=lambda self: self.env.company.ids)
