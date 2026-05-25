# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PartnerClosureReason(models.Model):
    _name = 'partner.closure.reason'
    _description = 'Partner close reason'

    name = fields.Char("Closure reason", required=True)
