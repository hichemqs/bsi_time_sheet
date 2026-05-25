# -*- coding: utf-8 -*-

from odoo import models, fields


class HrJob(models.Model):
    _inherit = "hr.job"

    is_critical_position = fields.Boolean(string="Poste critique",tracking=True)
    is_key_position = fields.Boolean(string="Poste clé",tracking=True)
    is_external_position = fields.Boolean(string="Poste à combler externe",tracking=True)
    is_functional_supervisor = fields.Boolean('Rôle de supérieur fonctionnel',tracking=True)
    is_manager = fields.Boolean('Rôle de gestionnaire',tracking=True)
    sector_id = fields.Many2one('hr.sector', string='Secteur',tracking=True)
    type_main_oeuvre = fields.Selection([('moi_sop', 'MOI-SOP'), ('mod', 'MOD')], string="Type de Main - d'œuvre",tracking=True)
    code_metier = fields.Char('Code du métier',tracking=True)
