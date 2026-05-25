# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class ContactCategorizationWizard(models.TransientModel):
    _name = 'contact.categorization.wizard'
    _description = 'Contact categorization wizard'

    potential_recurrence = fields.Selection(
        selection=[('yes', 'Oui'), ('no', 'Non')],
        string='Récurrence potentielle',
        tracking=True,
        required=True
    )

    openings_per_year = fields.Integer(
        'Nombres de portes par année',
        tracking=True
    )

    is_proportion_above_80 = fields.Selection(
        selection=[('yes', 'Oui'), ('no', 'Non')],
        string='Proportion allouée à Barrette > 80 % ?',
        tracking=True
    )

    last_update_year = fields.Selection(
        selection=lambda self: self._get_year_selection(),
        string="Année de dernière mise à jour",
        required=True
    )


    partner_id = fields.Many2one(
        'res.partner',
        string="Partenaire",
        required=True
    )

    child_ids = fields.One2many(
        related='partner_id.child_ids',
        readonly=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
        required=True
    )

    customer_id = fields.Many2one(
        'res.partner',
        string='Client',
        domain="[('id', 'in', child_ids)]",
    )

    user_id = fields.Many2one(
        'res.users',
        string='Auteur de la catégorie',
        default=lambda self: self.env.user,
        domain="[('share', '=', False)]",
        check_company=True,
        required=True
    )
    show_recurrent_fields = fields.Boolean(compute='_compute_visibility_fields')
    show_non_recurrent_fields = fields.Boolean(compute='_compute_visibility_fields')
    ville_de_construction=fields.Char(string='Ville de Construction')

    @api.depends('potential_recurrence')
    def _compute_visibility_fields(self):
        for rec in self:
            rec.show_recurrent_fields = rec.potential_recurrence == 'yes'
            rec.show_non_recurrent_fields = rec.potential_recurrence == 'no'

    @api.onchange('potential_recurrence')
    def _onchange_potential_recurrence(self):
        if self.potential_recurrence == 'no':
            self.openings_per_year = False
            self.is_proportion_above_80 = False

    def _get_year_selection(self):
        current_year = datetime.now().year
        return [(str(y), str(y)) for y in range(current_year - 1, current_year + 3)]

    def action_apply(self):
        current_year_str = str(datetime.now().year)

        if self.potential_recurrence == 'no':
            customer_category = 'c'
        else:
            if not self.is_proportion_above_80:
                raise UserError(_("Tous les champs sont obligatoires pour une récurrence potentielle 'Oui'."))

            if self.openings_per_year > 15:
                customer_category = 'a1' if self.is_proportion_above_80 == 'yes' else 'a2'
            else:
                customer_category = 'b1' if self.is_proportion_above_80 == 'yes' else 'b2'

        if self.last_update_year == current_year_str:
            self.partner_id.write({
                'customer_category': customer_category,
                'categ_last_update_date': fields.Date.today(),
                'openings_per_year': self.openings_per_year if self.potential_recurrence == 'yes' else 0,
                # 'user_id': self.user_id.id,
            })

            if self.customer_id:
                self.customer_id.parent_id = self.partner_id.id

        self.env['contact.categorization.history'].create({
            'potential_recurrence': self.potential_recurrence,
            'openings_per_year': self.openings_per_year,
            'is_proportion_above_80': self.is_proportion_above_80,
            'last_update_year': self.last_update_year,
            'customer_id': self.customer_id.id,
            'partner_id': self.partner_id.id,
            'customer_category': customer_category,
            'updated_on': fields.Datetime.now(),
            'user_id': self.user_id.id
        })
