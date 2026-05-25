# -*- coding: utf-8 -*-

import io

import xlsxwriter
import json

from odoo import _, fields
from odoo.http import Controller, request, route, content_disposition
from datetime import datetime, date


class EmployeesExport(Controller):

    @route('/employee/export/xlsx', type='http', auth='user')
    def export_employees(self, data):
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        params = json.loads(data)
        for key, value in params.items():
            if not value.get('ids'):
                continue
            worksheet = workbook.add_worksheet(key)
            headers = value.get('headers')
            records = request.env[value.get('model')].sudo().browse(value.get('ids'))
            export_data = records.export_data(value.get('fields')).get('datas', [])
            worksheet.write_row(0, 0, headers)
            column_widths = [len(header) for header in headers]
            for row_idx, row in enumerate(export_data, start=1):
                row = [fields.Date.to_string(data) if isinstance(data, (datetime, date)) else data for data in row]
                worksheet.write_row(row_idx, 0, row)
                for col_idx, cell_value in enumerate(row):
                    column_widths[col_idx] = max(column_widths[col_idx], len(str(cell_value)))

            for col_idx, width in enumerate(column_widths):
                worksheet.set_column(col_idx, col_idx, width)

        workbook.close()
        content = buffer.getvalue()
        buffer.close()
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition('Employés.xlsx'))
        ]
        return request.make_response(content, headers)
