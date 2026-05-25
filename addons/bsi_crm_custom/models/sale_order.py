# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
from lxml import etree
import requests
import logging
from odoo.exceptions import UserError
import base64
import re

_logger = logging.getLogger(__name__)
LOST_STAGES = ['perdu', 'abandonnee']
DONE_STAGES = ['contrat']
#BASE_URL = 'http://10.50.153.35:8000/api'
# SET_STATUS_URL = 'http://10.50.153.35:8000/api/setstatus_tosoum/%s/%s'
# REMOVE_LOST_URL = 'http://10.50.153.35:8000/api/%s/%s'


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # def _get_default_order_stage_id(self):
    #     return self.env['sale.order.stage'].search([], limit=1)

    # Existing fields
    # user_id = fields.Many2one(string="Représentant FC")
    name = fields.Char(string="Numéro de soumission")
    oae_id = fields.Integer(string='oae')
    parent_id = fields.Many2one('sale.order', string='Parent')
    order_child_ids = fields.One2many('sale.order', 'parent_id')
    paying_customer_id = fields.Many2one('res.partner', string="Client payeur")
    user_image_128 = fields.Binary(related='user_id.image_128', string="User Avatar", readonly=True)
    company_id = fields.Many2one(string='Location', readonly=True, invisible=True)
    date_order = fields.Datetime(string="Date de soumission")
   # order_stage_id = fields.Many2one('sale.order.stage', string="Stage", default=_get_default_order_stage_id)
    validity = fields.Date('Validity')
    validity_date = fields.Date(string="Date de la soumission")
    consultation_date = fields.Date('Consultation scheduled for')
    ue_mur = fields.Integer('UE Mur')
    ue_planchers = fields.Integer('UE Planchers')
    ue_toitures = fields.Integer('UE Toitures')
    expected_revenue = fields.Monetary('UEs', currency_field='currency_id')
    probability = fields.Float("Probability")
    opportunity_id = fields.Many2one(string="Projet client")
    montant_soumissionne = fields.Float(string="Montant Soumissionné")
    ue_total = fields.Integer('UE', compute='_compute_ue_total', store=True)
    project_age = fields.Integer(string='Project Age (days)', compute='_compute_project_age', store=True)
    version_age = fields.Integer('Age of the version')
    coord_rep_id = fields.Many2one('res.users', string="Représentant FC", compute='_compute_coord_rep_id', store=True)
    coord_rep_merchant_id = fields.Many2one('res.users', string="Représentant coordo Marchant")
    record_rep_id = fields.Many2one('res.users', string="Client representative", related='partner_id.user_id', store=True)
    original_create_date = fields.Datetime(string="Date de Création Original", readonly=True)
    create_date = fields.Datetime(string="Date de Création Original", readonly=True)
    write_date = fields.Datetime(readonly=True)
    relance_week = fields.Selection([
        ('last', 'Last Week'),
        ('current', 'This Week'),
        ('next', 'Next Week'),
        ('none', 'Not in 3 Weeks')
    ], compute='_compute_relance_week',store=True, index=True)

    request_date = fields.Date(string="Date de la demande")
    required_validated_date = fields.Date(string="Date Requise Validée")
    estimation_finalization_date = fields.Date(string="Date finalisation de l’estimation")
    closing_date = fields.Date(string="Date de fermeture")
    guaranteed_price_date = fields.Date(string="Date de Prix Garantie")
    contract_date = fields.Date(string="Date de Contrat")

    stag_id = fields.Selection([
        # ('qualifie', 'Qualifié'),
        # ('nouveau', 'Nouveau'),
        ('demande', 'Demande'),
        ('planification', 'Planification'),
        ("missing_info ", "Manque d'info"),
        ('estimation', 'Estimation'),
        ('a_configurer', 'A configurer'),
        ('soumission', 'Soumission'),
        ('contrat', 'Contrat'),
        ('perdu', 'Perdu'),
        ('abandonnee', 'Abandonnée'),    
    ], string='Statut de l\'étape', default='demande')

    classification = fields.Selection([
        ('partie9', 'Partie 9'),
        ('partie4', 'Partie 4'),
        ('Agricole', 'Agricole'),
    ], string='Classification')

    large_scale_project = fields.Selection([
        ('oui', 'Oui'),
        ('non', 'Non'),
    ], string="Projet d'envergure")
    contrat = fields.Char(string="Contrat")
    customer_category = fields.Selection(related='partner_id.customer_category', store=True, string='Catégorie')
    customer_categ_id = fields.Many2one('res.partner.customer.category', related='partner_id.customer_categ_id', 
                                  store=True, string="Type de client")
    passe_par_marchand = fields.Selection([
        ('oui', 'Oui'),
        ('non', 'Non'),
    ], string="Passé par un marchands", compute='_compute_passe_par_marchand', store=True)
    price_type = fields.Selection([
        ('fixe', 'Fixe'),
        ('cost', 'Forfaitaire'),
        ('mixte', 'Mixte'),
        ('budget', 'Budget'),
    ], string="Type de prix")
    fait_par_estimation = fields.Selection([
        ('oui', 'Oui'),
        ('non', 'Non'),
    ], string="Fait par l'estimation")
    date_de_relance = fields.Date('Date de relance')
    date_de_construction = fields.Date('Date de construction prévu')
    contact_id = fields.Many2one(
    'res.partner', 
    string="Contact principale",
    domain="[('id', 'in', allowed_contacts)]"
)
    # available_contact_ids = fields.Many2many('res.partner',string="Available Contacts",compute='_compute_available_contacts')
    charge_de_projets = fields.Many2one('res.users', string="Chargé de Projets")
    estimateur = fields.Many2one('res.users', string="Estimateur")
    unity_number = fields.Integer(string="Nombre d'unités")
    sales_director_id = fields.Many2one('hr.employee', 'Directeur de ventes', compute='_compute_sales_director', store=True, readonly=False)
    client_followup = fields.Html(string="Suivi Client")
    lost_reason = fields.Selection([
        ('prix', 'Prix'),
        ('livraison', 'Délai de livraison'),
    ], string="Raison de la perte")
    total_oae = fields.Monetary(string="Total Oae")
    total_with_taxes_oae = fields.Monetary(string="Total avec tax Oae", compute='_compute_total_with_taxes_oae', store=True)
    total_tax_oae = fields.Monetary(string="Total tax Oae")
    role_du_contact = fields.Many2one('contact.role',string="Rôle du contact", compute='_compute_contact_role', store=True)
    annex_reason = fields.Char(string="Raison de l'annexe")
    revision_reason = fields.Selection([
        ('new_plan', 'Nouveau plan'),
        ('modif_murs', 'Modification(s) murs préfabriqués'),
        ('plancher_changement', 'Plancher: changement du type de produit'),
        ('fermes_modif', 'Fermes: modification(s)'),
        ('acier_modif', 'Acier: modification(s)'),
        ('option_fermes', 'Option fermes de toit'),
        ('option_plancher', 'Option plancher'),
        ('option_murs', 'Option murs préfabriqués'),
        ('option_multiples', 'Option multiples'),
        ('modif_spec', 'Modification des spécification(s)'),
    ], string="Raison de la révision")

    contact_lines = fields.One2many('sale.order.contact', 'order_id', string="Contacts")
    allowed_contacts = fields.Many2many('res.partner', compute='_compute_allowed_contacts')

    # TODO: remove this field
    create_date_date = fields.Date(
    string="Date de création",
    compute="_compute_dates_only",
    store=False
    )
    create_date_oae = fields.Date(
        string="Date de création OAE",
        default=fields.Date.today
    )
    write_date_date = fields.Date(
        string="Date de dernière modification",
        compute="_compute_dates_only",
        store=False
    )
    date_order_date = fields.Date(
        string="Date de soumission",
        compute="_compute_dates_only",
        store=False
    )
    original_create_date_date = fields.Date(
        string="Date de création originale",
        compute="_compute_dates_only",
        store=False
    )
    commitment_date_date = fields.Date(
        string="Date d'engagement",
        compute="_compute_dates_only",
        store=False
    )
    partner_categorie_id = fields.Selection(
        related='partner_id.customer_category',
        string="Catégorie",
        store=True,
        readonly=True,
    )
    partner_contact_id = fields.Many2one(
        'res.partner',
        string='Contact',
        compute='_compute_partner_contact_id',
        store=True
    )
    sync_status = fields.Selection(
        string="Customer status",
        related='partner_id.sync_status',
        store=True,
        readonly=True
    )

    soumission_envoye = fields.Boolean(string='Soumission envoyé')
    contrat_envoye = fields.Boolean(string='Contrat envoyé')
    contrat_signe = fields.Boolean(string='Contrat signé')
    contract_exp_date = fields.Date("Date d'expiration de contrat", tracking=True)
    is_internet_request = fields.Selection([
        ('oui', 'Oui'),
        ('non', 'Non'),
    ], string="Demande via le site internet")
    note_estimateur = fields.Text(string="Note à l'estimateur")
    soummision_non_finalise = fields.Binary('Soummision non finalisé', attachement=True)
    soummision_finalise = fields.Binary('Soummision finalisé', attachement=True)
    soummision_finalise_oae = fields.Integer('Soummision finalisé OAE')
    sf_file_name = fields.Char(compute='_compute_sf_file_name', store=True)
    contrat_finalise = fields.Binary('Contrat finalisé', attachement=True)
    contrat_finalise_oae = fields.Integer('Contrat finalisé OAE')
    cf_file_name = fields.Char(compute='_compute_cf_file_name', store=True)
    mfiles_auth_token = fields.Char(string='M-Files Token', readonly=True, copy=False)
    last_synchronization = fields.Datetime(string="Dernière synchonisation")
    phone_mobile_search = fields.Char(string="Téléphone contact",store=False,search="_search_phone_mobile_search")

    def _search_phone_mobile_search(self, operator, value):
        clean_value = re.sub(r"\D", "", value or "")

        if not clean_value:
            return [("id", "=", False)]
            
        self.env.cr.execute("""
            SELECT order_id
            FROM sale_order_contact
            WHERE regexp_replace(phone, '[^0-9]', '', 'g')
              ILIKE %s
        """, (f"%{clean_value}%",))

        order_ids = [row[0] for row in self.env.cr.fetchall()]
        return [("id", "in", order_ids)]


    @property
    def BASE_URL(self):
        return self.env['ir.config_parameter'].sudo().get_param('crm.connexion_oae_baseurl')
        
    def action_toggle_soumission_envoye(self):
        for record in self:
            if record.soumission_envoye:
                record.state = 'sent'
                record.signature = False
                record.signed_by = False
                record.signed_on = False

            record.soumission_envoye = not record.soumission_envoye

    def action_toggle_contrat_envoye(self):
        for record in self:
            if record.contrat_envoye:
                record.state = 'sent'
                record.signature = False
                record.signed_by = False
                record.signed_on = False

            record.contrat_envoye = not record.contrat_envoye

    def action_toggle_contrat_signe(self):
        for record in self:
            if record.contrat_signe:
                record.state = 'sent'
                record.signature = False
                record.signed_by = False
                record.signed_on = False

            record.contrat_signe = not record.contrat_signe

    def _compute_partner_contact_id(self):
        for order in self:
            contact = order.partner_id.child_ids.filtered(lambda c: c.type == 'contact')[:1]
            order.partner_contact_id = contact if contact else False

    @api.depends('name')
    def _compute_sf_file_name(self):
        for order in self:
            order.sf_file_name = '%s.pdf' % order.name

    @api.depends('contrat')
    def _compute_cf_file_name(self):
        for order in self:
            order.cf_file_name = '%s.pdf' % (order.contrat or 'Contrat')

    @api.depends('create_date', 'write_date', 'date_order', 'original_create_date', 'commitment_date')
    def _compute_dates_only(self):
        for rec in self:
            rec.create_date_date = rec.create_date.date() if rec.create_date else False
            rec.write_date_date = rec.write_date.date() if rec.write_date else False
            rec.date_order_date = rec.date_order.date() if rec.date_order else False
            rec.original_create_date_date = rec.original_create_date.date() if rec.original_create_date else False
            rec.commitment_date_date = rec.commitment_date.date() if rec.commitment_date else False

    @api.depends('total_oae', 'total_tax_oae')
    def _compute_total_with_taxes_oae(self):
        for order in self:
            order.total_with_taxes_oae = order.total_oae + order.total_tax_oae

    @api.depends('partner_id')
    def _compute_coord_rep_id(self):
        for order in self:
            order.coord_rep_id = order.partner_id.user_id if order.partner_id else False

    @api.depends('paying_customer_id', 'paying_customer_id.customer_categ_id')
    def _compute_passe_par_marchand(self):
        for order in self:
            order.passe_par_marchand = "oui" if order.paying_customer_id.is_merchant else "non"

    @api.depends('contact_lines.contact_id')
    def _compute_allowed_contacts(self):
        for order in self:
            order.allowed_contacts = order.contact_lines.mapped('contact_id')

    @api.depends('contact_id')
    def _compute_contact_role(self):
        for order in self:
            contact_line = order.contact_lines.filtered(lambda c: c.contact_id.id == order.contact_id.id)
            order.role_du_contact = contact_line.role_du_contact.id if contact_line.role_du_contact else False

    def _create_validity_reminders(self):
        today = fields.Date.today()
        start_date = today + timedelta(days=15)

        orders = self.search([
            ('stag_id', '=', 'soumission_envoye'),
            ('validity_date', '=', start_date),
        ])

        for order in orders:
            self.env['mail.activity'].create({
                'res_model_id': self.env.ref('sale.model_sale_order').id,
                'res_id': order.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'user_id': order.user_id.id or self.env.uid,
                'summary': f"Rappel : la soumission {order.name} expire le {order.validity_date}",
                'date_deadline': today,
            })

    def _message_auto_subscribe_notify(self, partner_ids, template):
        return super(SaleOrder, self.with_context(mail_auto_subscribe_no_notify=True))._message_auto_subscribe_notify(
            partner_ids, template)

    def get_contract_report_url(self):
        self.ensure_one()
        return self.access_url + '/report?access_token=%s' % self._portal_ensure_token()

    def _has_to_be_signed(self):
        self.ensure_one()
        return (
                not self.is_expired
                and self.require_signature
                and not self.signature
                and not self.contrat_signe
        )

    def _compute_is_expired(self):
        today = fields.Date.today()
        for order in self:
            order.is_expired = (
                order.contract_exp_date
                and order.contract_exp_date < today
            )

    # @api.depends('partner_id', 'paying_customer_id')
    # def _compute_available_contacts(self):
    #     for order in self:
    #         contacts = self.env['res.partner']
    #         if order.partner_id:
    #             contacts |= order.partner_id.child_ids.filtered(lambda p: p.type == 'contact')
    #         if order.paying_customer_id:
    #             contacts |= order.paying_customer_id.child_ids.filtered(lambda p: p.type == 'contact')
    #         order.available_contact_ids = contacts

    # @api.onchange('partner_id', 'paying_customer_id')
    # def _onchange_customers(self):
    #     if self.contact_id not in self.available_contact_ids:
    #         self.contact_id = False

    @api.depends('date_de_relance')
    def _compute_relance_week(self):
        today = fields.Date.today()
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(days=7)
        next_monday = this_monday + timedelta(days=7)
        last_sunday = last_monday + timedelta(days=6)
        this_sunday = this_monday + timedelta(days=6)
        next_sunday = next_monday + timedelta(days=6)

        for rec in self:
            date = rec.date_de_relance
            if date:
                if last_monday <= date <= last_sunday:
                    rec.relance_week = 'last'
                elif this_monday <= date <= this_sunday:
                    rec.relance_week = 'current'
                elif next_monday <= date <= next_sunday:
                    rec.relance_week = 'next'
                else:
                    rec.relance_week = 'none'
            else:
                rec.relance_week = 'none'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        arch = super().get_view(view_id, view_type, **options)
        doc = etree.XML(arch['arch'])
        if view_type == 'tree':
            for node in doc.xpath("//field[not(@name='tag_ids')]"):
                node.set("readonly", "1")

        arch['arch'] = etree.tostring(doc, encoding='unicode')
        return arch


    @api.depends('user_id.employee_ids.parent_id')
    def _compute_sales_director(self):
        for record in self:
            employee = self.env['hr.employee'].sudo().search([
                ("user_id", "=", record.user_id.id)
            ], limit=1)
            if employee:
                parent = employee.sudo().parent_id
                if parent:
                    record.sales_director_id = parent.id
                else:
                    record.sales_director_id = False
            else:
                record.sales_director_id = False


             
            # if record.coord_rep_id:
            #     employee = record.coord_rep_id.sudo().employee_ids
            #     if employee:
            #         parent = employee[0].sudo().parent_id
            #         if parent:
            #             record.sales_director_id = parent.id
            #         else:
            #             record.sales_director_id = False
            #     else:
            #         record.sales_director_id = False
            # else:
            #     record.sales_director_id = False

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

    def action_quotation_send(self):
        res = super().action_quotation_send()
        template_id = self.env.ref('bsi_crm_custom.quotation_finalized')
        res['context'] = {**(res.get('context', {})), 'default_template_id': template_id.id}
        return res

    def action_confirm(self):
        return super(SaleOrder, self.with_context(send_email=False)).action_confirm()

    # def _get_sales_director_id(self, coord_rep_id):
    #     if not coord_rep_id:
    #         return False
    #     partner = self.env['res.partner'].browse(coord_rep_id)
    #     employees = partner.employee_ids
    #     if employees and employees[0].parent_id:
    #         return employees[0].parent_id.id
    #     return False

    @api.model_create_multi
    def create(self, vals_list):
        # for vals in vals_list:
        #     if 'sales_director_id' not in vals and vals.get('coord_rep_id'):
        #         vals['sales_director_id'] = self._get_sales_director_id(vals['coord_rep_id'])

        orders = super().create(vals_list)
        for order in orders:
            if order.opportunity_id:
                order.opportunity_id._update_status_from_soumissions()
            if order.contact_id:
                order.message_subscribe(partner_ids=[order.contact_id.id])
            if order.stag_id == 'soumission':
                order._create_mail_activity()
            if order.contract_date and not order.contract_exp_date:
                order.contract_exp_date = order.contract_date + timedelta(days=7)
        return orders

    def write(self, vals):
        if vals.get('signature'):
            vals['contrat_signe'] = True

        if 'contract_date' in vals and vals.get('contract_date') and not vals.get('contract_exp_date'):
            contract_date = fields.Date.to_date(vals['contract_date'])
            vals['contract_exp_date'] = contract_date + timedelta(days=7)

        # if 'coord_rep_id' in vals and 'sales_director_id' not in vals:
        #     # raise Warning(f"The employee {self.coord_rep_id.id} ")
        #     vals['sales_director_id'] = self._get_sales_director_id(vals.get('coord_rep_id'))

        res = super().write(vals)
        if 'stag_id' in vals or 'opportunity_id' in vals:
            self.mapped('opportunity_id')._update_status_from_soumissions()

        if vals.get('stag_id') == 'soumission':
            self._create_mail_activity()

        if vals.get('stag_id') in DONE_STAGES:
            activities = self.env['mail.activity'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', 'in', self.ids),
            ])
            if activities:
                activities._action_done()

        # KILL (done) activities when moving to a lost stage
        if vals.get('stag_id') in LOST_STAGES:
            activities = self.env['mail.activity'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', 'in', self.ids),
            ]).unlink()
            
        return res

    def unlink(self):
        leads = self.mapped('opportunity_id')
        res = super().unlink()
        for lead in leads:
            lead._update_status_from_soumissions()
        return res

    def action_lost(self):
        for record in self:
            record.set_state_oae('perdu', 'setstatus_tosoum/{}/perdu')

    def action_remove_lost(self):
        if self.stag_id not in ['perdu', 'abandonnee']:
            return
        self.set_state_oae('soumission', 'removelost/{}')

    def action_abandoned(self):
        for record in self:
            record.set_state_oae('abandonnee', 'setstatus_tosoum/{}/Abandonne')

    def set_state_oae(self, state, path):
        self.ensure_one()
        if not self.oae_id:
            return
        try:
            endpoint = f"{self.BASE_URL}/{path.format(self.oae_id)}"
            response = requests.patch(endpoint, timeout=10)
            response.raise_for_status()
            self.stag_id = state
        except Exception as e:
            _logger.error('HTTP error: %s', e)

    def _create_mail_activity(self):
        todo_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mail_activity_data_todo', raise_if_not_found=False)
        activity_vals = [{
            'activity_type_id': todo_id,
            'summary': 'Relance soumission',
            'user_id': order.user_id.id,
            'res_id': order.id,
            'date_deadline': order.closing_date,
            'res_model_id': order.env.ref('sale.model_sale_order').id,
        } for order in self if (order.closing_date and order.user_id)]

        if activity_vals:
            self.env['mail.activity'].create(activity_vals)

    def _notify_get_recipients_groups_fillup(self, groups, model_description, msg_vals=None):
        groups = super()._notify_get_recipients_groups_fillup(groups, model_description, msg_vals)
        contract_finalized = self.env.ref('bsi_crm_custom.contract_finalized')
        try:
            if 'template_id' not in self._context:
                if msg_vals and "Contrat signé par" in msg_vals.get('body', ''):
                    for group_tuple in groups:
                        group_tuple[2]['has_button_access'] = False
                else:
                    for group_tuple in groups:
                        group_tuple[2]['button_access']['title'] = "Voir la soumission"
                return groups

            if contract_finalized.id not in self._context.get('template_id', []):
                for group_tuple in groups:
                    group_tuple[2]['has_button_access'] = False
            else:
                title = 'Voir le contrat signer' if self.contrat_signe else 'Accepter et signer le contrat'
                for group_tuple in groups:
                    group_tuple[2]['button_access']['title'] = title
        except:
            pass
        return groups

    def _notify_by_email_prepare_rendering_context(
            self, message, msg_vals, model_description=False,
            force_email_company=False, force_email_lang=False):

        render_context = super()._notify_by_email_prepare_rendering_context(
            message, msg_vals,
            model_description=model_description,
            force_email_company=force_email_company,
            force_email_lang=force_email_lang,
        )
        subtitles = render_context.get('subtitles')
        if not subtitles:
            return render_context

        if msg_vals and "Contrat signé par" in msg_vals.get('body'):
            render_context['subtitles'] = [
                (
                    "Numéro de Contrat : %s" % (self.contrat or '')
                    if subtitle == self.name
                    else subtitle
                )
                for subtitle in subtitles
            ]
            msg_vals['email_layout_xmlid'] = 'bsi_crm_custom.mail_notification_layout_without_responsible_signature'
            return render_context

        template_id = self._context.get('template_id')

        if not template_id:
            render_context['subtitles'] = [
                line for line in subtitles if _("Expires on") not in line
            ]
            return render_context

        contract_finalized = self.env.ref('bsi_crm_custom.contract_finalized')
        quotation_finalized = self.env.ref('bsi_crm_custom.quotation_finalized')

        expiry_text = None
        is_contract = contract_finalized.id in template_id
        is_quotation = quotation_finalized.id in template_id

        if is_contract and self.contract_exp_date:
            expiry_text = "Expire le %s" % self.contract_exp_date

        elif is_quotation and self.guaranteed_price_date:
            expiry_text = "Prix valide jusqu'au %s" % self.guaranteed_price_date

        render_context['subtitles'] = [
            (
                self.contrat
                if subtitle == self.name and is_contract
                else expiry_text
                if _("Expires on") in subtitle and expiry_text
                else subtitle
            )
            for subtitle in subtitles
            if not (_("Expires on") in subtitle and not expiry_text)
        ]
        return render_context

    @api.model
    def _mail_get_partner_fields(self, introspect_fields=False):
        if self._context.get('send_order_report'):
            return ['contact_id']
        return super()._mail_get_partner_fields(introspect_fields)

    
    def action_mfiles_apercu(self):
        self.ensure_one()

        numero_soumission = self.name
        
        ICP = self.env['ir.config_parameter'].sudo()
        mfiles_username = ICP.get_param('crm.mfiles_username')
        mfiles_password = ICP.get_param('crm.mfiles_password')
        mfiles_baseurl = ICP.get_param('crm.mfiles_baseurl')
        mfiles_vaultguid = ICP.get_param('crm.mfiles_vaultguid')
        
        if not all([mfiles_username, mfiles_password, mfiles_baseurl, mfiles_vaultguid]):
            raise UserError("Configuration M-Files incomplète.")
        
        auth_url = f"{mfiles_baseurl.rstrip('/')}/server/authenticationtokens"
        
        payload = {
            "Username": mfiles_username,
            "Password": mfiles_password,
            "VaultGuid": mfiles_vaultguid
        }

        try:
            response = requests.post(
                auth_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                token = response.json().get('Value')
                
                if not token:
                    raise UserError("Token non reçu.")
                
                self.mfiles_auth_token = token
                
            else:
                raise UserError(f"Échec authentification: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur connexion M-Files: {str(e)}")

        endpoint_search = f"/objects?q={numero_soumission}&o=111"
        obj_data = self._mfiles_api_call(endpoint_search)

        items = obj_data.get('Items', [])
        main_obj_id = None
        for item in items:
            if item.get('Title') == numero_soumission:
                main_obj_id = item.get('ObjVer', {}).get('ID')
                break

        if not main_obj_id:
            raise UserError("Objet principal non trouvé.")

        endpoint_rel = f"/objects/111/{main_obj_id}/latest/relationships"
        relationships = self._mfiles_api_call(endpoint_rel)

        soummision_finalise_oae = None
        for rel in relationships:
            if f"{numero_soumission} - Soumission" in rel.get('Title', ''):
                soummision_finalise_oae = rel.get('ObjVer', {}).get('ID')
                break

        if not soummision_finalise_oae:
            raise UserError("Soumission non trouvé.")

        endpoint = f"/objects/0/{soummision_finalise_oae}/files"
        files_data = self._mfiles_api_call(endpoint)
        
        if not files_data:
            raise UserError("Aucun fichier trouvé.")
        
        first_file = files_data[0] if isinstance(files_data, list) else files_data
        file_id = first_file.get('ID')
        if not file_id:
            raise UserError("fichier non trouvé.")
        
        content_endpoint = f"/objects/0/{soummision_finalise_oae}/files/{file_id}/content"
        file_content = self._mfiles_download_file(content_endpoint)
        
        file_base64 = base64.b64encode(file_content).decode('utf-8')

        return {
            'type': 'ir.actions.client',
            'tag': 'preview_binary_pdf',
            'context': {
                'binary_data': file_base64,
            },
        }

    def action_mfiles_contrat_apercu(self):
        self.ensure_one()

        numero_soumission = self.name

        ICP = self.env['ir.config_parameter'].sudo()
        mfiles_username = ICP.get_param('crm.mfiles_username')
        mfiles_password = ICP.get_param('crm.mfiles_password')
        mfiles_baseurl = ICP.get_param('crm.mfiles_baseurl')
        mfiles_vaultguid = ICP.get_param('crm.mfiles_vaultguid')
        
        if not all([mfiles_username, mfiles_password, mfiles_baseurl, mfiles_vaultguid]):
            raise UserError("Configuration M-Files incomplète.")
        
        auth_url = f"{mfiles_baseurl.rstrip('/')}/server/authenticationtokens"
        
        payload = {
            "Username": mfiles_username,
            "Password": mfiles_password,
            "VaultGuid": mfiles_vaultguid
        }

        try:
            response = requests.post(auth_url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
            if response.status_code == 200:
                token = response.json().get('Value')
                if not token:
                    raise UserError("Token non reçu.")
                self.mfiles_auth_token = token
            else:
                raise UserError(f"Échec authentification: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur connexion M-Files: {str(e)}")

        endpoint_search = f"/objects?q={numero_soumission}&o=111"
        obj_data = self._mfiles_api_call(endpoint_search)

        items = obj_data.get('Items', [])
        main_obj_id = None
        for item in items:
            if item.get('Title') == numero_soumission:
                main_obj_id = item.get('ObjVer', {}).get('ID')
                break

        if not main_obj_id:
            raise UserError("Objet principal non trouvé.")

        endpoint_rel = f"/objects/111/{main_obj_id}/latest/relationships"
        relationships = self._mfiles_api_call(endpoint_rel)

        contrat_finalise_oae = None
        for rel in relationships:
            if " - Contrat" in rel.get('Title', ''):
                contrat_finalise_oae = rel.get('ObjVer', {}).get('ID')
                break

        if not contrat_finalise_oae:
            raise UserError("Contrat non trouvé.")

        endpoint = f"/objects/0/{contrat_finalise_oae}/files"
        files_data = self._mfiles_api_call(endpoint)
        
        if not files_data:
            raise UserError("Aucun fichier trouvé.")
        
        first_file = files_data[0] if isinstance(files_data, list) else files_data
        file_id = first_file.get('ID')
        if not file_id:
            raise UserError("fichier non trouvé.")
        
        content_endpoint = f"/objects/0/{contrat_finalise_oae}/files/{file_id}/content"
        file_content = self._mfiles_download_file(content_endpoint)
        
        contrat_file_base64 = base64.b64encode(file_content).decode('utf-8')

        return {
            'type': 'ir.actions.client',
            'tag': 'preview_binary_pdf',
            'context': {
                'binary_data': contrat_file_base64,
            },
        }

    def _mfiles_api_call(self, endpoint):
        self.ensure_one()
        
        if not self.mfiles_auth_token:
            raise UserError("Aucun token M-Files.")
        
        baseurl = self.env['ir.config_parameter'].sudo().get_param('crm.mfiles_baseurl')
        url = f"{baseurl.rstrip('/')}{endpoint}"
        
        headers = {
            'X-Authentication': self.mfiles_auth_token,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur API M-Files: {str(e)}")

    def _mfiles_download_file(self, endpoint):
        self.ensure_one()

        if not self.mfiles_auth_token:
            raise UserError("Aucun token M-Files.")

        baseurl = self.env['ir.config_parameter'].sudo().get_param('crm.mfiles_baseurl')
        url = f"{baseurl.rstrip('/')}{endpoint}"

        headers = {
            'X-Authentication': self.mfiles_auth_token,
        }

        try:
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            return response.content

        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur téléchargement M-Files: {str(e)}")
