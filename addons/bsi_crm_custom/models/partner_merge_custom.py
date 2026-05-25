from odoo import api, models, _
from odoo.exceptions import UserError


class MergePartnerAutomatic(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    @api.model
    def _update_values(self, src_partners, dst_partner):
        all_partners = src_partners + dst_partner

        oae_values = set(
            p.oae_id.id if hasattr(p.oae_id, 'id') else p.oae_id
            for p in all_partners
            if p.oae_id
        )

        if len(oae_values) > 1:
            raise UserError(
                _("Cannot merge: the selected contacts have different OAE IDs. "
                  "Please resolve this conflict manually before merging.")
            )

        return super()._update_values(src_partners, dst_partner)
