# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    validity = fields.Date('Validity')
    consultation_date = fields.Date('Consultation scheduled for')
    ue_mur = fields.Integer('UE Mur')
    ue_planchers = fields.Integer('UE Planchers')
    ue_toitures = fields.Integer('UE Toitures')
    ue_total = fields.Integer('UE', compute='_compute_ue_total', store=True)
    project_age = fields.Integer(string='Project Age (days)', compute='_compute_project_age', store=True)
    version_age = fields.Integer('Age of the version')
    coord_rep_id = fields.Many2one('res.users', string="Coordinator representative")
    coord_rep_merchant_id = fields.Many2one('res.users', string="Merchant coordinator representative")
    record_rep_id = fields.Many2one('res.users', string="Client representative", related='partner_id.user_id')
    stage_group_id = fields.Many2one(related='stage_id.stage_group_id', string="Groupe", store=True)
    lead_state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked')
    ], default='in_progress', copy=False)

    oae_id = fields.Integer('oae')
    status = fields.Selection([
        ('demande', 'Demande'),
        ('estimation', 'Estimation'),
        ('soumission', 'Soumission'),
        ('soumission_envoye', 'Soumission envoyé'),
        ('contrat', 'Contrat'),
        ('contrat_signe', 'Contrat signé'),
        ('perdu', 'Perdu'), 
    ], string='Statut de l\'étape', group_expand='_group_expand_status', default='demande')

    last_quotation = fields.Many2one('sale.order', string="Dern. soumission")
    last_contract = fields.Many2one('sale.order', string="Dern. Contrat")

    nb_soumission = fields.Integer(string="Nombre de soumissions",compute='_compute_nb_soumission')

    nb_revision = fields.Integer(string="Nombre de révisions",compute='_compute_nb_revision')
    ville_construction = fields.Many2one('res.country.state',string="Ville de construction",domain="[('country_id.code', '=', 'CA')]")
    assigned_ids = fields.Many2many('res.users', string="Assignés", compute='_compute_assigned_ids', store=True)
    contrat_count = fields.Integer(
        string="Contrats",
        compute="_compute_contrat_count"
    )

    def _compute_contrat_count(self):
        SaleOrder = self.env['sale.order']
        for lead in self:
            lead.contrat_count = SaleOrder.search_count([
                ('opportunity_id', '=', lead.id),
                ('stag_id', '=', 'contrat')
            ])

    @api.depends('order_ids.user_id')
    def _compute_assigned_ids(self):
        for record in self:
            record.assigned_ids = record.order_ids.mapped('user_id')

    def _compute_nb_soumission(self):
        SaleOrder = self.env['sale.order']
        for lead in self:
            lead.nb_soumission = SaleOrder.search_count([('opportunity_id', '=', lead.id)])

    def action_view_contrat_sale_orders(self):
        self.ensure_one()
    
        return {
            'name': 'Contrats liés',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [
                ('opportunity_id', '=', self.id),
                ('stag_id', '=', 'contrat')
            ],
            'context': {},
        }

    def _compute_nb_revision(self):
        SaleOrder = self.env['sale.order']
        for lead in self:
            lead.nb_revision = SaleOrder.search_count([('opportunity_id', '=', lead.id)])

    @api.depends('ue_mur', 'ue_planchers', 'ue_toitures')
    def _compute_ue_total(self):
        for record in self:
            record.ue_total = (record.ue_mur or 0) + (record.ue_planchers or 0) + (record.ue_toitures or 0)

    @api.depends('create_date')
    def _compute_project_age(self):
        for record in self:
            if record.create_date:
                record.project_age = (fields.Date.today() - record.create_date.date()).days
            else:
                record.project_age = 0

    def _group_expand_status(self, states, domain, order):
        return [key for key, val in self._fields['status'].selection]

    def _update_status_from_soumissions(self):
        for lead in self:
            soumissions = self.env['sale.order'].search([('opportunity_id', '=', lead.id)])
            if not soumissions:
                continue
    
            stag_ids = soumissions.mapped('stag_id')
    
            if any(stag == 'contrat_signe' for stag in stag_ids):
                lead.status = 'contrat_signe'
            elif all(stag in ['estimation','planification'] for stag in stag_ids):
                lead.status = 'estimation'
            elif any(stag in ['contrat', 'contrat_envoye'] for stag in stag_ids):
                lead.status = 'contrat'
            elif any(stag == 'soumission_envoye' for stag in stag_ids):
                lead.status = 'soumission'
            elif all(stag == 'demande' for stag in stag_ids):
                lead.status = 'demande'
            elif all(stag in ['perdu', 'abandonnee'] for stag in stag_ids):
                lead.status = 'perdu'


class CrmStageGroup(models.Model):
    _name = 'crm.stage.group'
    _description = 'Groups for Crm stages'

    name = fields.Char('Group name')


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    stage_group_id = fields.Many2one('crm.stage.group', string="Group")
