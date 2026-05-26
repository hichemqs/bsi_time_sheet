# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree
from PIL import Image, ImageDraw, ImageFont
from odoo.addons.base.models.avatar_mixin import get_hsl_from_seed
from odoo.tools import html_escape
from base64 import b64encode
import logging
import re
from datetime import datetime

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    oae_id = fields.Integer('oae')
    sales_director_id = fields.Many2one('hr.employee', 'Sales Director', compute='_compute_sales_director', store=True)
    sales_director_user_id = fields.Many2one(string='Sales director user', related='sales_director_id.user_id')
    customer_categ_id = fields.Many2one('res.partner.customer.category',string="Type de client",domain="[('type', '=', company_type)]",required=False, default=lambda self: self._default_customer_categ_id())
    potential_recurrence = fields.Boolean(string='Potential Recurrence', tracking=True)
    is_proportion_above_80 = fields.Boolean('Proportion allocated to Barrette > 80% ?', tracking=True)
    customer_category = fields.Selection([
        ('uncategorized', 'Uncategorized'),
        ('a1', 'A1'),
        ('a2', 'A2'),
        ('b1', 'B1'),
        ('b2', 'B2'),
        ('c', 'C')],
        string="Customer category",readonly=True,tracking=True,
        default=lambda self: 'uncategorized' if self.env.context.get('default_is_company') else 'c',)
    partner_type = fields.Selection([
        ('customer', 'Client'),
        ('contact', 'Contact')],
        string="Type du partenaire", default="customer")
    categ_history_ids = fields.One2many('contact.categorization.history', 'partner_id', string="Categorization history", readonly=True)
    reminder = fields.Selection([('qr', 'Quarter'), ('sm', 'Semester'), ('year', 'Year')], string="Reminder")
    is_closed = fields.Boolean('Client fermé')
    credit_blocked = fields.Boolean('Credit blocked')
    sale_blocked = fields.Boolean('Sale blocked')
    sap_number = fields.Char('Numéro SAP')
    user_id = fields.Many2one(string="Représentant FC", default=lambda self: self.env.user)
    date_de_creation = fields.Date(string="Date de création", readonly=False, default=fields.Date.today)

    preference_de_communication = fields.Selection([
            ('phone', 'Appel téléphonique'),
            ('email', 'Courriel'),
            ('sms', 'SMS'),
        ],
        string='Préférence de communication')
    is_prospect = fields.Boolean(string="Prospect", compute='_compute_is_prospect', store=True)
    contact_type = fields.Many2one('contact.type', string="Type de Contact")
    approval_required = fields.Boolean('Approval required')
    categ_last_update_date = fields.Date('Date of the last category update')
    closure_reason_id = fields.Many2one('partner.closure.reason', string="Closure reason")
    sync_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')],
        string="Customer status", default="active", readonly=True)
    soumission_count = fields.Integer(string="Toutes les soumissions", compute="_compute_soumissions")
    soumission_count_soumission = fields.Integer(string="Soumissions en cours", compute="_compute_soumissions")
    soumission_count_contrat = fields.Integer(string="Contrat", compute="_compute_soumissions")
    soumission_count_contrat_marchand = fields.Integer(string="Contrat via un marchand", compute="_compute_soumissions")
    soumission_count_a_configurer = fields.Integer(string="À configurer", compute="_compute_soumissions")
    soumission_count_demande = fields.Integer(string="Demande", compute="_compute_soumissions")

    is_officer = fields.Boolean(compute='_compute_is_officer')
    openings_per_year = fields.Integer("Openings This Year", readonly=True)
    sale_block_button_label = fields.Char(compute='_compute_sale_button_label')
    credit_block_button_label = fields.Char(compute='_compute_credit_button_label')
    is_merchant = fields.Boolean(related='customer_categ_id.client_marchand', store=True)
    is_account_manager = fields.Boolean('Is account manager', compute='_compute_is_account_manager')

    # def _get_default_payment_term(self):
    #     return self.env['account.payment.term'].search(
    #         [('name', '=', 'Payable avant fabrication')], limit=1
    #     )

    property_payment_term_id = fields.Many2one('account.payment.term',default=lambda self: self.env['account.payment.term'].search([('name', '=', 'Payable avant fabrication')], limit=1))
    role_du_contact = fields.Many2one("contact.role",string="Rôle du contact",compute="_compute_role_du_contact_from_sale_line",inverse="_inverse_role_du_contact",readonly=False)
    popup_contact_type_id = fields.Many2one("contact.role", string="Rôle du contact")

    def _compute_role_du_contact_from_sale_line(self):
        line_id = self.env.context.get("sale_order_contact_line_id")
        line = self.env["sale.order.contact"].browse(line_id) if line_id else False

        for rec in self:
            if line and line.exists() and line.contact_id.id == rec.id:
                rec.role_du_contact = line.role_du_contact
            else:
                rec.role_du_contact = False

    def _inverse_role_du_contact(self):
        line_id = self.env.context.get("sale_order_contact_line_id")
        if not line_id:
            return
        line = self.env["sale.order.contact"].browse(line_id)
        
        for rec in self:
            if line.exists() and line.contact_id.id == rec.id:
                line.role_du_contact = rec.role_du_contact

    @api.depends('sale_blocked')
    def _compute_sale_button_label(self):
        for rec in self:
            rec.sale_block_button_label = "Débloquer Vente" if rec.sale_blocked else "Bloqué Vente"

    @api.depends_context('uid')
    def _compute_is_account_manager(self):
        has_group_account_manager = self.env.user.has_group('account.group_account_manager')
        for partner in self:
            partner.is_account_manager = has_group_account_manager

    @api.depends('credit_blocked')
    def _compute_credit_button_label(self):
        for rec in self:
            rec.credit_block_button_label = "Débloquer Crédit" if rec.credit_blocked else "Bloqué Crédit"
    
    def action_apply(self):
        current_year_str = str(fields.Date.today().year)
    
        if self.last_update_year == current_year_str:
            raise UserError("La catégorisation a déjà été faite cette année pour ce contact.")
    
        customer_category = self._get_customer_category()
    
        if not customer_category:
            raise UserError("Impossible de déterminer la catégorie du client.")
    
        update_vals = {
            'customer_category': customer_category,
            'categ_last_update_date': fields.Date.today(),
        }

        if customer_category != 'c' and not self.partner_id.user_id:
            update_vals['user_id'] = self.user_id.id
    
        self.partner_id.write(update_vals)

    
    def action_categorize_contact(self):
        for wizard in self:
            partner = wizard.partner_id
            if partner and wizard.potential_recurrence == 'yes':
                partner.openings_per_year = wizard.openings_per_year

    show_openings_current_year = fields.Integer(
    compute="_compute_show_openings_current_year",
    string=" Le nombre de porte pour année en cours"
)

    @api.depends('customer_category', 'categ_last_update_date', 'openings_per_year')
    def _compute_show_openings_current_year(self):
        current_year = datetime.now().year
        for rec in self:
            if rec.customer_category in ('b1', 'b2','a1', 'a2') and rec.categ_last_update_date and rec.categ_last_update_date.year == current_year:
                rec.show_openings_current_year = rec.openings_per_year
            else:
                rec.show_openings_current_year = 0

    @api.depends('is_closed', 'sap_number')
    def _compute_is_prospect(self):
        for partner in self:
            partner.is_prospect = True if not partner.is_closed and not partner.sap_number else False

    def _format_phone(self, phone_num):
        digits = re.sub(r'\D', '', phone_num or '')
        m = re.match(r'(\d{3})(\d{3})(\d{4})(\d{0,5})', digits)
        if not m:
            return phone_num
        main = f"({m[1]}){m[2]}-{m[3]}"
        return f"{main} x{m[4]}" if m[4] else main

    # def _generate_svg_avatar(self, name):
    #     initials = '?'
    #
    #     if name.strip():
    #         parts = name.strip().split()
    #         if len(parts) >= 2:
    #             first_name = parts[0].capitalize()
    #             last_initial = parts[1][0].upper()
    #             initials = f"{first_name}{' '}{last_initial}"
    #         else:
    #             initials = name.strip().capitalize()
    #
    #     _logger.info(f"🖼️ Avatar initials generated: {initials}")
    #
    #     length = len(initials)
    #     if length <= 5:
    #         font_size = 48
    #     elif length <= 7:
    #         font_size = 42
    #     elif length <= 9:
    #         font_size = 36
    #     else:
    #         font_size = 22
    #
    #     bgcolor = get_hsl_from_seed(name)
    #
    #     svg = (
    #         "<?xml version='1.0' encoding='UTF-8' ?>"
    #         "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
    #         f"<rect width='180' height='180' fill='{bgcolor}'/>"
    #         f"<text x='50%' y='55%' text-anchor='middle' "
    #         f"dominant-baseline='middle' "
    #         f"font-family='Arial, sans-serif' font-size='{font_size}' "
    #         f"fill='#ffffff'>{html_escape(initials)}</text>"
    #         "</svg>"
    #     )
    #
    #     return b64encode(svg.encode())

    @api.model_create_multi
    def create(self, vals_list):
        partners_phone, partners_name = [], []
        for vals in vals_list:
            if vals.get('name'):
                partners_name.append(vals['name'])

            if vals.get('phone'):
                vals['phone'] = self._format_phone(vals['phone'])
                partners_phone.append(vals['phone'])

            if vals.get('company_type') == 'person':
                vals['customer_category'] = 'c'

        existing_partners = self._check_partner_duplicates(partners_name, partners_phone)
        if existing_partners:
            raise ValueError('Les contacts suivants existent déjà : %s' % ', '.join(existing_partners.mapped('name')))
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('company_type') == 'person':
            vals['customer_category'] = 'c'

        if vals.get('phone'):
            vals['phone'] = self._format_phone(vals['phone'])

        if 'potential_recurrence' in vals or 'is_proportion_above_80' in vals:
            vals['categ_last_update_date'] = fields.Datetime.today()

        return super().write(vals)

    def _check_partner_duplicates(self, partners_name, partners_phone=None):
        domain = [('name', 'in', partners_name), ('is_company', '=', True)]
        if partners_phone:
            domain.append(('phone', 'in', partners_phone))
        return self.env['res.partner'].sudo().search(domain, limit=1)

    def action_view_opportunity(self):
        action = super().action_view_opportunity()
        if 'views' in action:
            tree_view = [(self.env.ref('crm.crm_case_tree_view_oppor').id, 'tree')]
            action['views'] = tree_view + [(view_id,view_type) for view_id, view_type in action['views'] if view_type != 'tree']

        return action

    @api.depends_context('uid')
    def _compute_is_officer(self):
        self.is_officer = self.env.user.has_group("base.group_system")

    @api.depends('sale_order_ids', 'parent_id', 'parent_id.sale_order_ids')
    def _compute_soumissions(self):
        for partner in self:
            partner_ids = [partner.id]
            if partner.parent_id:
                partner_ids.append(partner.parent_id.id)

            orders = self.env['sale.order'].search([('partner_id', 'in', partner_ids)])

            partner.soumission_count = len(orders)
            partner.soumission_count_soumission = len(orders.filtered(lambda o: o.stag_id == 'soumission'))
            partner.soumission_count_contrat = len(orders.filtered(lambda o: o.stag_id == 'contrat'))
            partner.soumission_count_contrat_marchand = len(orders.filtered(lambda o: o.passe_par_marchand == 'oui'))
            partner.soumission_count_a_configurer = len(orders.filtered(lambda o: o.stag_id == 'a_configurer'))
            partner.soumission_count_demande = len(orders.filtered(lambda o: o.stag_id == 'demande'))

    # @api.onchange('company_type')
    # def onchange_company_type(self):
    #     res = super().onchange_company_type()
    #     self.customer_categ_id = False
    #     return res

    @api.depends('user_id')
    def _compute_sales_director(self):
        for record in self:
            if not record.user_id:
                record.sales_director_id = False
                continue
    
            employee = self.env['hr.employee'].sudo().search(
                [('user_id', '=', record.user_id.id)],
                limit=1)
            if employee:
                record.sales_director_id = (employee.parent_id.id if employee.parent_id else employee.id)
            else:
                record.sales_director_id = False

    def action_open_close_partner(self):
        if not self.is_closed:
            return {
                'name': _("Closure Reason"),
                'type': 'ir.actions.act_window',
                'views': [[False, 'form']],
                'view_mode': 'form',
                'res_model': 'partner.closure.reason.wizard',
                'context': {'default_partner_id': self.id},
                'target': 'new'
            }

        if self.env.user.has_group("sales_team.group_sale_manager"):
            self.write({
                'closure_reason_id': False,
                'is_closed': False
            })
        else:
            raise UserError(_("You do not have permission to reopen this record."))

    def action_update_category(self):
        return {
            'name': _('Update category'),
            'type': 'ir.actions.act_window',
            'res_model': 'contact.categorization.wizard',
            'views': [[False, 'form']],
            'view_mode': 'form',
            'context': {'default_partner_id': self.id},
            'target': 'new'
        }

    def _onchange_phone_validation(self):
        pass

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        arch = super().get_view(view_id, view_type, **options)
        doc = etree.XML(arch['arch'])

        if view_type == 'form' and not self.env.user.has_group('account.group_account_manager'):
            for node in doc.xpath("//field[@name='sap_number']"):
                node.set("readonly", "1")

        arch['arch'] = etree.tostring(doc, encoding='unicode')
        return arch

    def action_open_sale_block_wizard(self):
        if self.sale_blocked:
            self.sale_blocked = False
            self.message_post(
                body=f"<span style='color:green;'>Débloqué Vente</span> par {self.env.user.name}",
                subtype_xmlid='mail.mt_note',
                body_is_html=True
            )
        else:
            return {
                'name': _('Bloquer les ventes du partenaire'),
                'type': 'ir.actions.act_window',
                'res_model': 'partner.bloque.vente.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_partner_id': self.id,
                    'block_type': 'sale',
                }
            }

    def action_open_credit_block_wizard(self):
        if self.credit_blocked:
            self.credit_blocked = False
            self.message_post(
                body=f"<span style='color:green;'>Débloqué Crédit</span> par {self.env.user.name}",
                subtype_xmlid='mail.mt_note',
                body_is_html=True
            )
        else:
            return {
                'name': _('Bloquer le crédit du partenaire'),
                'type': 'ir.actions.act_window',
                'res_model': 'partner.bloque.vente.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_partner_id': self.id,
                    'block_type': 'credit',
                }
            }

    def action_view_all_soumissions(self):
        self.ensure_one()
        partner_ids = [self.id]
        if self.parent_id:
            partner_ids.append(self.parent_id.id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Toutes les soumissions',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('partner_id', 'in', partner_ids)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_soumission_stage(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Soumissions en cours',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id), ('stag_id', '=', 'soumission')],
            'context': {'default_partner_id': self.id},
        }
    
    def action_view_contrat_stage(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrat',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id), ('stag_id', '=', 'contrat')],
            'context': {'default_partner_id': self.id},
        }

    def action_view_contrat_marchand_stage(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrat via un marchand',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.id),
                ('passe_par_marchand', '=', 'oui')
            ],
            'context': {'default_partner_id': self.id},
        }

    def action_view_a_configurer_stage(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'À configurer',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id), ('stag_id', '=', 'a_configurer')],
            'context': {'default_partner_id': self.id},
        }
    
    def action_view_demande_stage(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Demande',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id), ('stag_id', '=', 'demande')],
            'context': {'default_partner_id': self.id},
        }

    def _default_customer_categ_id(self):
        partner_type = self.env.context.get('default_partner_type', 'person')
        return self.env['res.partner.customer.category'].search([
            ('is_default', '=', True),
            ('type', '=', partner_type),
        ], limit=1)


    @api.onchange('company_type')
    def onchange_company_type(self):
        res = super().onchange_company_type()
        # Set default category instead of resetting to False
        partner_type = 'company' if self.is_company else 'person'
        categ = self.env['res.partner.customer.category'].search([
            ('is_default', '=', True),
            ('type', '=', partner_type),
        ], limit=1)
        self.customer_categ_id = categ or False
        return res
