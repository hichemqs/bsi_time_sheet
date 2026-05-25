# -*- coding: utf-8 -*-

from odoo import fields, models


class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    def action_register_departure(self):
        super().action_register_departure()
        employee = self.employee_id
        resume_ids = employee.resume_line_ids.filtered(lambda r: not r.date_end).sorted('date_start', reverse=True)
        if resume_ids and not resume_ids[0].date_end:
            resume_ids[0].write({
                'date_end': self.departure_date,
                'name': "%s (# d'employé: %s)" % (resume_ids[0].name, employee.barcode) if "# d'employé" not in resume_ids[0].name and employee.barcode else resume_ids[0].name

            })
