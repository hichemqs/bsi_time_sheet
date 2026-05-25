# -*- coding: utf-8 -*-
from odoo import models, fields


class HrJob(models.Model):
    _inherit = "hr.job"

    is_critical_position = fields.Boolean(string="Poste critique")
    is_key_position = fields.Boolean(string="Poste clé")
    is_external_position = fields.Boolean(string="Poste à combler externe")
    is_functional_supervisor = fields.Boolean('Rôle de supérieur fonctionnel')
    is_manager = fields.Boolean('Rôle de gestionnaire')
    sector_id = fields.Many2one('hr.sector', string='Secteur')
    type_main_oeuvre = fields.Selection([('moi_sop', 'MOI-SOP'), ('mod', 'MOD')], string="Type de Main - d'œuvre")
    code_metier = fields.Char('Code du métier')
