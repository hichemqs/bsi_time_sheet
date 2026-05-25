# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ContactCategorizationHistory(models.Model):
    _name = 'contact.categorization.history'
    _description = 'Contact categorization history'
    _order = "last_update_year desc"

    potential_recurrence = fields.Selection(
        selection=[('yes', 'Oui'), ('no', 'Non')],
        string='Potential Recurrence',
        tracking=True
    )
    openings_per_year = fields.Integer('Number of openings per year', tracking=True)
    is_proportion_above_80 = fields.Selection(
        selection=[('yes', 'Oui'), ('no', 'Non')],
        string='Proportion allocated to Barrette > 80% ?',
        tracking=True
    )
    last_update_year = fields.Char(string="Year")
    customer_id = fields.Many2one('res.partner', string='Customer')
    updated_on = fields.Datetime(string="Updated on", default=lambda self: fields.Datetime.now())
    partner_id = fields.Many2one('res.partner', string='Partner')
    user_id = fields.Many2one('res.users', string='User')

    customer_category = fields.Selection([
        ('uncategorized', 'Uncategorized'),
        ('a1', 'A1'),
        ('a2', 'A2'),
        ('b1', 'B1'),
        ('b2', 'B2'),
        ('c', 'C')],
        string="Customer Category",
        readonly=True)