# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    no_contract = fields.Char('No contrat')
    request_via = fields.Selection([('email', 'Email'), ('phone', 'Téléphone'), ('in_person', 'En personne')], 'Demandé via')
    requester_title = fields.Char(
        string="Titre du demandeur",
    )

    requester_phone = fields.Char(
        string="Téléphone du demandeur"
    )

    product_service_type = fields.Selection(
        [
            ("trusses", "Fermes"),
            ("walls", "Murs"),
            ("joists", "Solives"),
            ("transport_delay", "Transport (retard)"),
            ("transport_equipment", "Transport (équipement)"),
            ("invoice", "Facturation"),
            ("personnel_barrette", "Personnel Barrette"),
            ("information_guide", "Information sur guide"),
            ("other", "Autre"),
        ],
        string="Type de produit ou service en cause",
    )

    contact_person = fields.Many2one('res.partner', string="Personne à contacter")

    contact_person_title = fields.Char(
        string="Titre (personne à contacter)"
    )

    contact_person_email = fields.Char(
        string="Courriel (personne à contacter)"
    )

    site_stage = fields.Selection(
        [
            ("na", "NA"),
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("roof", "Toiture"),
        ],
        string="Étape au chantier",
    )

    problem_type = fields.Selection(
        [
            ("missing_material", "Manque de matériel"),
            ("wrong_material", "Mauvais matériel"),
            ("damaged_material", "Matériel endommagé"),
            ("other", "Autres"),
        ],
        string="Type de problème",
    )

    # analyse page

    preliminary_cause = fields.Char(
        string="Cause préliminaire"
    )

    cost_responsibility = fields.Selection(
        [
            ("barrette", "Barrette"),
            ("client", "Client"),
        ],
        string="Responsabilité des coûts",
    )

    billing_to = fields.Selection(
        [
            ("client", "Client"),
            ("carpenter", "Menuisier"),
            ("merchant", "Marchand"),
            ("other", "Autre"),
        ],
        string="Facturation à qui",
    )

    solution = fields.Text(
        string="Solution"
    )

    solution_department = fields.Selection(
        [
            ("design_only", "Dessin technique seulement"),
            ("engineering_only", "Ingénierie seulement"),
            ("design_engineering", "Dessin technique & ingénierie"),
            ("operation", "Opération"),
        ],
        string="Département impliqué pour la solution",
    )

    repair_cost_estimate = fields.Float(
        string="Estimé des coûts de réparation"
    )

    repair_cost_justification = fields.Text(
        string="Justification des coûts de réparation"
    )
