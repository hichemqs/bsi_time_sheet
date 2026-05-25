# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SituationEmploiPremierNiveau(models.Model):
    _name = 'situation.emploi.premier.niveau'
    _description = 'Situation Emploi 1er Niveau'

    name = fields.Char(string='Name', required=True, tracking=True)
    deuxieme_niveau_ids = fields.One2many('situation.emploi.deuxieme.niveau', 'premier_niveau_id',
                                          string='Deuxième Niveau Records', tracking=True)


class SituationEmploiDeuxiemeNiveau(models.Model):
    _name = 'situation.emploi.deuxieme.niveau'
    _description = 'Situation Emploi 2e Niveau'

    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    premier_niveau_id = fields.Many2one('situation.emploi.premier.niveau', string='Premier Niveau', tracking=True)
