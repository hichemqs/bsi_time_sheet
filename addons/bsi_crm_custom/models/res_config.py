from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nombre_jours_inactifs = fields.Integer(
        string='Nombre jours inactifs',
        config_parameter='bsi_crm_custom.nombre_jours_inactifs'
    )
    mfiles_username = fields.Char(string='M-Files Username',config_parameter='crm.mfiles_username')
    mfiles_password = fields.Char(string='M-Files Password',config_parameter='crm.mfiles_password')
    mfiles_baseurl = fields.Char(string='M-Files Base URL',config_parameter='crm.mfiles_baseurl')
    mfiles_vaultguid = fields.Char(string='Vault GUID',config_parameter='crm.mfiles_vaultguid')
    connexion_oae_baseurl = fields.Char(string='Connexion OAE Base URL',config_parameter='crm.connexion_oae_baseurl')

    @api.model
    def get_values(self):
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo()
        res['nombre_jours_inactifs'] = int(param.get_param('bs_crm.nombre_jours_inactifs'))
        return res

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'bs_crm.nombre_jours_inactifs', self.nombre_jours_inactifs
        )
