# -*- coding: utf-8 -*-
import xlsxwriter

from odoo import models, fields, api
from datetime import timedelta
from lxml import etree
import re

CRON_EXPORT_HEADERS = {
    "Employés": {
        "headers": {
            "# Employé": "barcode",
            "Nom de l'employé": "name",
            "Division": "company_id.name",
            "Secteur": "sector_id.name",
            "Statut Actuel": "active",
            "Date Naissance": "birthday",
            "Date d'embauche": "date_embauche",
            "Date de départ": "departure_date",
            "Type # 2": "departure_reason_id.name",
            "Rôle": "job_id.name",
            "Département": "department_id.name",
            "Courriel": "work_email",
            "Sexe": "gender",
            "Grandeur": "grandeur_vetements",
            "Secteur d'activité": "sector_id.name",
            "Site": "company_id.name",
            "Supérieur hiérarchique": "parent_id.name",
            "BDRH ID": "bdrh_id",
        },
        "model": "hr.employee",
        "ids": lambda self: self.env["hr.employee"].search(["|", ("active", "=", True), ("active", "=", False)]).ids,
    },
    "Départements": {
        "headers": {
            "Nom du département": "name",
            "Code du Département": "code_dep",
        },
        "model": "hr.department",
        "ids": lambda self: self.env["hr.employee"].search([]).mapped("department_id").ids,

    },
    "Postes": {
        "headers": {
            "Nom": "name",
            "Code du métier": "code_metier",
        },
        "model": "hr.job",
        "ids": lambda self: self.env["hr.employee"].search([]).mapped("job_id").ids,
    },
}

EXPORT_ALL_HEADERS = {
    "Employés": {
        "headers": {
            "# d'employé": "barcode",
            "Nom de l'employé": "name",
            "Date d'embauche": "date_embauche",
            "Date de naissance": "birthday",
            "Localisation": "company_id/name",
            "Secteur": "sector_id/name",
            "Département/Code du Département": "department_id/code_dep",
            "Département/Nom du département": "department_id/name",
            "Centre de coût": "code_centre_cout",
            "Poste de travail": "job_id/name",
            "Code du métier": "code_metier",
            "Rôle de gestionnaire": "is_manager",
            "Rôle de supérieur fonctionnel": "is_functional_supervisor",
            "Type d’emploi": "type_emploi",
            "Type d’employé": "employee_type",
            "Supérieur immédiat": "parent_id/name",
            "Supérieur fonctionnel": "coach_id/name",
            "Courriel personnel": "private_email",
            "# de cellulaire personnel": "mobile",
            "# de téléphone personnel": "private_phone",
            "Nom du contact": "emergency_contact",
            "# de téléphone du contact d’urgence": "emergency_phone",
            "Rue privée": "private_street",
            "Ville privée": "private_city",
            "État privé": "private_state_id/name",
            "Code postal privé": "private_zip",
            "Pays privé": "private_country_id/name",
            "Genre": "gender",
            "Grandeur de vêtements": "grandeur_vetements",
            "Raison du départ": "departure_reason_id/display_name",
            "Date de départ": "departure_date",
            "Informations supplémentaires": "departure_description",
        },
        "model": "hr.employee",
        "ids": lambda self: self.ids,
    }
}


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'CA')], limit=1)
        return country.id if country else False

    @api.model
    def _get_employee_type_selection(self):
        return [
            ('student', 'Étudiant'),
            ('trainee', 'Stagiaire'),
            ('regulier', 'Régulier'),
            ('temps_partiel', 'Temps partiel'),
            ('temporaire', 'Temporaire'),
            ('sur_appel', 'Sur appel'),
            ('preretraite', 'Préretraite'),
            ('tet', 'Travailleur étranger temporaire (TET)')
        ]

    private_country_id = fields.Many2one('res.country', default=_get_default_country, tracking=True)

    lang = fields.Selection(default='fr_CA',tracking=True)
    private_street = fields.Char(tracking=True)
    private_street2 = fields.Char(tracking=True)
    private_city = fields.Char(tracking=True)
    private_state_id = fields.Many2one(tracking=True)
    private_zip = fields.Char(tracking=True)
    private_country_id = fields.Many2one(tracking=True)
    private_email = fields.Char(tracking=True)
    bdrh_id = fields.Integer('BDRH ID')

    date_embauche = fields.Date("Date d'embauche",tracking=True)
    date_anciennete = fields.Date("Date ancienneté",tracking=True)
    grandeur_vetements = fields.Selection(
        [('nd', 'ND'), ('xs', 'XS'), ('s', 'S'), ('m', 'M'), ('l', 'L'), ('xl', 'XL'), ('xxl', 'XXL'), ('xxxl', 'XXXL'), ('xxxxl', 'XXXXL'), ('xxxxxl', 'XXXXXL')], string="Grandeur de vêtements",tracking=True)
    type_emploi = fields.Selection([('syndique', 'Syndiqué'), ('non_syndique_usine', 'Non syndiqué - Usine'),
                                    ('non_syndique_bureau', 'Non syndiqué - Bureau')], string="Type d'emploi",tracking=True)
    mobile = fields.Char("Mobile",tracking=True)
    outil_collecte_heures = fields.Selection(
        [('chonos', 'Chonos'), ('atlas', 'Atlas'), ('excel', 'Excel')], string="Outil de collecte d'heures",tracking=True)

    salaire = fields.Selection(
        [('horaire', 'Horaire'), ('fix', 'Fix')], string="Salaire",tracking=True)
    # termination_date = fields.Date(string="Date de terminaison")
    contraintes_physiques = fields.Char("Contraintes Physiques ou autres",tracking=True)
    poste_vacants_budgete = fields.Boolean("Poste vacants budgété",tracking=True)
    probation = fields.Selection(
        [('en_cours', 'en cours'), ('n_a', 'N/A ou intégration'), ('completee', 'Complétée')], string="Probation")
    tele_travail = fields.Selection([('oui', 'Oui'), ('non', 'Non'),
                                     ('hybride', 'Hybride')], default="non", string="Télétravail",tracking=True)

    is_functional_supervisor = fields.Boolean('Rôle de supérieur fonctionnel', related='job_id.is_functional_supervisor')
    is_manager = fields.Boolean('Rôle de gestionnaire', related='job_id.is_manager',tracking=True)
    work_phone = fields.Char(compute=None,tracking=True)
    justification_anciennete = fields.Char("Justification d'ancienneté",tracking=True)
    # employee_type = fields.Selection(string="Statut employé", selection_add=[('regulier', 'Régulier'), ('temps_partiel', 'Temps partiel'),
    # ('temporaire', 'Temporaire'), ('sur_appel', 'Sur appel'), ('preretraite', 'Préretraite'), ('agence_de_placement', 'Agence de placement'), ('tet', 'Travailleur étranger temporaire (TET)'), ('consultant', 'Consultant')],
    #                                  ondelete={'regulier': 'cascade', 'temps_partiel': 'cascade', 'temporaire': 'cascade', 'agence_de_placement': 'cascade', 'tet': 'cascade', 'consultant': 'cascade'})

    employee_type = fields.Selection(selection='_get_employee_type_selection', tracking=True,string="Statut employé", default='regulier', required=True, groups="hr.group_hr_user",
        help="The employee type. Although the primary purpose may seem to categorize employees, this field has also an impact in the Contract History. Only Employee type is supposed to be under contract and will have a Contract History.")

    # The sequence number, used for the barcode
    sequence_no = fields.Integer("Sequence No", copy=False, readonly=True,tracking=True)
    barcode = fields.Char('No Employé', copy=False, readonly=True, default='????',tracking=True)

    code_metier = fields.Char('Code du métier', related='job_id.code_metier', tracking=True)
    se_premier_niveau_id = fields.Many2one('situation.emploi.premier.niveau', string="Situation d'emploi premier niveau",tracking=True)
    se_deuxieme_niveau_id = fields.Many2one('situation.emploi.deuxieme.niveau', tracking=True, string="Situation d'emploi deuxième niveau", domain="[('premier_niveau_id', '=', se_premier_niveau_id)]")
    coach_id = fields.Many2one(compute=None , tracking=True)
    parent_id = fields.Many2one(domain=[('is_manager', '=', True)], check_company=False, tracking=True)
    deuxieme_niveau = fields.Boolean(string='Deuxième Niveau', compute='_compute_deuxieme_niveau', store=True,tracking=True)
    type_main_oeuvre = fields.Selection(related='job_id.type_main_oeuvre', string="Type de Main - d'œuvre", tracking=True)
    is_replacement_needed = fields.Boolean(string="Besoin remplacement", tracking=True)
    replacement_date = fields.Date(string="Date de remplacement",tracking=True)
    hr_event_ids = fields.One2many('hr.event', 'employee_id', string="Événement",tracking=True)
    department_id = fields.Many2one('hr.department', string='Département', check_company=False, tracking=True)
    sector_id = fields.Many2one('hr.sector', string='Secteur',tracking=True ,required=False)
    job_id = fields.Many2one(check_company=False, tracking=True)
    note = fields.Html(string='Note', translate=True,tracking=True)
    work_email = fields.Char(tracking=True)
    mobile_phone = fields.Char(tracking=True)
    work_email = fields.Char(tracking=True)
    private_phone = fields.Char(tracking=True)
    private_telephone = fields.Char(tracking=True)
    allowed_sector_ids = fields.Many2many('hr.sector', compute='_compute_allowed_sector_ids')
    code_centre_cout = fields.Char('Centre de coût', related="department_id.code_centre_cout")
    # description_centre_cout = fields.Text('Description centre de coût', related="department_id.description_centre_cout")

    @api.onchange('private_zip')
    def _onchange_private_zip(self):
        if self.private_zip:
            code = self.private_zip.upper().replace(" ", "")
            if len(code) == 6:
                self.private_zip = code[:3] + " " + code[3:]
            else:
                self.private_zip = code

    def _compute_allowed_sector_ids(self):
        for record in self:
            record.allowed_sector_ids = self.env.user.allowed_sector_ids

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        arch = super().get_view(view_id, view_type, **options)
        doc = etree.XML(arch['arch'])
        user_allowed_sectors = self.env.user.allowed_sector_ids

        if view_type == 'form':
            for node in doc.xpath("//field[@name='sector_id']"):
                node.set("domain", "[('id', 'in', %s)]" % user_allowed_sectors.ids)

        arch['arch'] = etree.tostring(doc, encoding='unicode')
        return arch

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'sector_id' in vals:
                barcode, sequence_no = self.pick_next_noemploye(vals['sector_id'])
                vals['sequence_no'] = sequence_no
                vals['barcode'] = barcode

            vals['bdrh_id'] = self.pick_next_nobdrh_id()

            # Retrieve the sector_no for the given sector_id
            # sector = self.env['hr.sector'].browse(vals['sector_id'])
            # sector_no = sector.sector_no if sector else '00'
            # max_sequence_no = 6000  # init to make sure it exist
            # sector_number = 00  # init to make sur it exist

            # if sector_no:
            #    self.env.cr.execute(
            #        "SELECT MAX(sequence_no) FROM hr_employee AS emp inner join hr_Sector AS sec on emp.sector_id = sec.id WHERE sec.sector_no = %s",
            #        (sector_no,)
            #    )
            #    max_sequence_no = self.env.cr.fetchone()[0] or 6000
            #    sector_number = sector_no

            # vals['sequence_no'] = max_sequence_no + 1
            # vals['barcode'] = sector_number + "-" + str(vals['sequence_no'])

        # Create the employee records with the modified vals_list
        res = super(HrEmployee, self).create(vals_list)
        for employee in res:
            employee.resume_line_ids.write({
                'name': employee.job_id.name or '',
                'description': employee.company_id.name or ''
            })
        return res

    def write(self, vals):
        if 'active' in vals:
            user_vals = {}
            for employee in self:
                name = employee.name or ''
                display_name = employee.display_name or ''

                if not vals['active']:
                    if '[INACTIF]' not in name:
                        vals['name'] = '[INACTIF] ' + name
                    if '[INACTIF]' not in display_name:
                        vals['display_name'] = '[INACTIF] ' + display_name
                else:
                    if '[INACTIF]' in name:
                        vals['name'] = name.replace('[INACTIF] ', '')
                    if '[INACTIF]' in display_name:
                        vals['display_name'] = display_name.replace('[INACTIF] ', '')

                if employee.user_id:
                    user_name = employee.user_id.name or ''
                    if not vals['active']:
                        if '[INACTIF]' not in user_name:
                            user_vals.setdefault(employee.user_id.id, {})['name'] = '[INACTIF] ' + user_name
                    else:
                        if '[INACTIF]' in user_name:
                            user_vals.setdefault(employee.user_id.id, {})['name'] = user_name.replace('[INACTIF] ', '')

        res = super(HrEmployee, self).write(vals)

        if not any(field in vals for field in ['job_id', 'active']):
            return res

        employees = self.filtered(lambda e: vals.get('active', e.active))

        if not employees:
            return res

        line_type = self.env.ref('hr_skills.resume_type_experience', raise_if_not_found=False)
        today = fields.Datetime.today()
        resume_lines_vals = []

        for emp in employees:
            if 'job_id' in vals:
                last_resume = emp.resume_line_ids.filtered(lambda r: not r.date_end).sorted('date_start', reverse=True)[:1]
                if last_resume:

                    last_resume.write({
                        'name': "%s (# d'employé: %s)" % (last_resume.name, emp.barcode) if "# d'employé" not in last_resume.name and emp.barcode else last_resume.name,
                        'date_end': today
                    })

                if vals['job_id']:
                    resume_lines_vals.append({
                        'employee_id': emp.id,
                        'name': emp.job_id.name or '',
                        'description': emp.company_id.name or '',
                        'date_start': today,
                        'line_type_id': line_type and line_type.id,
                    })

                    if resume_lines_vals:
                        self.env['hr.resume.line'].create(resume_lines_vals)

        if 'active' in vals and user_vals:
            users = self.env['res.users'].browse(user_vals.keys())
            for user in users:
                user.write(user_vals[user.id])

        return res

    def generate_noemploye(self):
        for employee in self:
            if employee.sector_id:
                barcode, sequence_no = self.pick_next_noemploye(employee.sector_id.id)
                employee.sequence_no = sequence_no
                employee.barcode = barcode

    def pick_next_noemploye(self, sector_id):
        """
        Helper function to generate a new barcode and sequence_no.
        :param sector_id: The sector_id for which the barcode is generated.
        :return: A tuple (barcode, sequence_no)
        """
        sector = self.env['hr.sector'].browse(sector_id)
        sector_no = sector.sector_no if sector else '00'
        curr_employee_id = self.id

        # Default values in case no data is found
        max_sequence_no = 6000
        sector_number = '00'

        # Build correct SQL
        #sql_toexecute = "SELECT MAX(sequence_no) FROM hr_employee AS emp inner join hr_Sector AS sec on emp.sector_id = sec.id WHERE sec.sector_no = %s"
        #if curr_employee_id:
        #    sql_toexecute += " and emp.id != " + str(curr_employee_id)
        sql_toexecute = "SELECT MAX(sequence_no) FROM hr_employee AS emp where active is True"

        if sector_no:
            self.env.cr.execute(
                sql_toexecute
            )

            max_sequence_no = self.env.cr.fetchone()[0] or 6000
            sector_number = sector_no

        sequence_no = max_sequence_no + 1
        barcode = f"{sector_number}-{sequence_no}"
        return barcode, sequence_no

    def pick_next_nobdrh_id(self):
        self.env.cr.execute("SELECT MAX(bdrh_id)+1 FROM hr_employee AS emp")
        return self.env.cr.fetchone()[0] or 0 + 1

    @api.onchange('sector_id')
    def _onchange_sector_id(self):
        for employee in self:
            if employee.sector_id:
                if not employee._origin.id:
                    barcode, sequence_no = employee.pick_next_noemploye(employee.sector_id.id)
                    employee.barcode = barcode
                else:
                    employee.barcode = f"{employee.sector_id.sector_no}-{employee.sequence_no}"

    @api.onchange('company_id')
    def _onchange_company_id(self):
        # Reset the sector_id if company changes
        self.sector_id = False

    @api.onchange('work_phone')
    def _onchange_work_phone(self):
        if self.work_phone:
            self.work_phone = self._format_phone(self.work_phone, ext=True)

    @api.onchange('mobile_phone', 'country_id', 'company_id')
    def _onchange_mobile_phone_validation(self):
        if self.mobile_phone:
            self.mobile_phone = self._format_phone(self.mobile_phone)

    @api.onchange('private_phone', 'country_id', 'company_id')
    def _onchange_private_phone_validation(self):
        if self.private_phone:
            self.private_phone = self._format_phone(self.private_phone)

    @api.onchange('private_telephone')
    def _onchange_private_telephone_validation(self):
        if self.private_telephone:
            self.private_telephone = self._format_phone(self.private_telephone)

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self._format_phone(self.mobile)

    @api.onchange('emergency_phone', 'country_id', 'company_id')
    def _onchange_emergency_phone_validation(self):
        if self.emergency_phone:
            self.emergency_phone = self._format_phone(self.emergency_phone)

    def _format_phone(self, phone, ext=None):
            phone_digits = re.sub(r'\D', '', phone)

            if len(phone_digits) < 10:
                return phone

            if ext:
                formatted_phone = re.sub(
                    r'^(\d{3})(\d{3})(\d{4})(.*)$',
                    r'(\1) \2-\3 #\4',
                    phone_digits
                ).strip()

                if formatted_phone.endswith('#'):
                    formatted_phone = formatted_phone.replace("#", "#0000")

            else:
                formatted_phone = re.sub(
                    r'^(\d{3})(\d{3})(\d{4})$',
                    r'(\1) \2-\3',
                    phone_digits
                )

            return formatted_phone

    @api.depends('se_premier_niveau_id')
    def _compute_deuxieme_niveau(self):
        for record in self:
            if record.se_premier_niveau_id and record.se_premier_niveau_id.deuxieme_niveau_ids:
                record.deuxieme_niveau = True
            else:
                record.deuxieme_niveau = False

    def _prepare_export_data(self, headers):
        """Return the structured export data (pure Python dict)."""
        export_data = {}
        for label, config in headers.items():
            ids = config["ids"](self) if callable(config["ids"]) else config["ids"]
            export_data[label] = {
                'headers': list(config["headers"].keys()),
                'fields': list(config["headers"].values()),
                'model': config["model"],
                'ids': ids or [],
            }
        return export_data

    def action_export_employees(self):
        """Button action (returns client action for UI)."""
        return {
            'type': 'ir.actions.client',
            'tag': 'bsi_hr_custom.export_employees',
            'params': self._prepare_export_data(EXPORT_ALL_HEADERS),
        }

    def _get_field_value(self, record, field_path):
        value = record
        for part in field_path.split("."):
            value = getattr(value, part, False)
            if not value:
                return ""
        return value if not hasattr(value, "name") else (value.name if hasattr(value, "name") else value)

    @api.model
    def cron_export_employees(self):
        export_data = self._prepare_export_data(CRON_EXPORT_HEADERS)

        import os, io, xlsxwriter
        module_path = os.path.dirname(os.path.abspath(__file__))
        export_dir = os.path.abspath(os.path.join(module_path, "..", "exports"))
        os.makedirs(export_dir, exist_ok=True)

        file_path = os.path.join(export_dir, "data-odoo rh.xlsx")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        for label, cfg in export_data.items():
            sheet = workbook.add_worksheet(label[:31])
    
            for col, header in enumerate(cfg['headers']):
                sheet.write(0, col, header)
        
            records = self.env[cfg['model']].browse(cfg['ids'])
            row = 1
            for rec in records:
                for col, field in enumerate(cfg['fields']):
                    sheet.write(row, col, self._get_field_value(rec, field))
                row += 1

        workbook.close()

        with open(file_path, "wb") as f:
            f.write(output.getvalue())

        return True

    @api.model
    def cron_mark_inactive_employees(self):
        """Mark employees inactive if last login exceeds configured days."""
        param = self.env['ir.config_parameter'].sudo()
        days = int(param.get_param('bs_crm.nombre_jours_inactifs'))
        cutoff_date = fields.Datetime.now() - timedelta(days=days)

        users = self.env['res.users'].search([('login_date', '<', cutoff_date)])
        employees = users.mapped('employee_ids')

        for employee in employees:
            if employee.active:
                employee.write({'active': False})
