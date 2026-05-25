# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCity(models.Model):
    _inherit = "res.city"

    nom_mrc = fields.Char('Nom MRC')
    region_administrative = fields.Char('Région administrative')
    oae_id = fields.Integer('oae id')
