# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEvent(models.Model):
    _name = "hr.event"
    _description = "Hr events"

    name = fields.Char(string="Description",tracking=True)
    event_type_id = fields.Many2one('hr.event.type', string="Type événement",tracking=True)
    date = fields.Date(string="Date",tracking=True)
    applicant_id = fields.Many2one('hr.employee', string="Demandeur",tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee",tracking=True)


class HrEventType(models.Model):
    _name = "hr.event.type"
    _description = "Hr event types"

    name = fields.Char(string="Nom",tracking=True)
