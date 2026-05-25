# -*- coding: utf-8 -*-
{
    'name': "bsi_hr_custom",
    'summary': """""",
    'description': """
    """,
    'author': "Amine Trifi",
    'website': "https://barrettestructural.com/",

    'category': '',
    'version': '17.0',
    'depends': ['hr_skills', 'hr_gamification', 'hr_recruitment', 'hr_holidays', 'hr_hourly_cost'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/hr_departure_wizard_views.xml',
        'views/hr_employee_views.xml',
        'views/res_users_views.xml',
        'views/hr_department_views.xml',
        'views/hr_job_views.xml',
        'views/hr_sector_views.xml',
        'views/hr_holidays_views.xml',
        'views/hr_event_views.xml',
        'views/situation_emploi_views.xml',
        'data/sequence_data.xml',
        'data/ir_cron.xml',
        'data/server_actions.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'bsi_hr_custom/static/src/component/*'
        ],
    },
    'installable': True,
    'auto_install': False,
}
