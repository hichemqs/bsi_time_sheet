from odoo import models, api
from odoo.addons.base.models.avatar_mixin import get_hsl_from_seed
from odoo.tools import html_escape
from base64 import b64encode
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def systray_get_activities(self):
        result = super().systray_get_activities()
        for activity in result:
            if activity.get("res_model") == "sale.order":
                activity["domain"] = [("stag_id", "not in", ["perdu", "abandonnee"])]
                break
        return result

    def _generate_svg_avatar(self, name):
        display_text = '?'

        if name.strip():
            parts = name.strip().split()
            if len(parts) >= 2:
                first_name = parts[0].capitalize()
                last_initial = parts[1][0].upper()
                display_text = f"{first_name}{' '}{last_initial}"
            else:
                display_text = parts[0].capitalize()

        display_text = html_escape(display_text)
        text_length = len(display_text)

        if text_length <= 5:
            font_size = 48
        elif text_length <= 7:
            font_size = 42
        elif text_length <= 9:
            font_size = 36
        else:
            font_size = 22

        bgcolor = get_hsl_from_seed(name)

        svg = (
            "<?xml version='1.0' encoding='UTF-8' ?>"
            "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
            f"<rect width='180' height='180' fill='{bgcolor}'/>"
            f"<text x='50%' y='55%' text-anchor='middle' "
            f"dominant-baseline='middle' "
            f"font-family='Arial, sans-serif' font-size='{font_size}' "
            f"fill='#ffffff'>{display_text}</text>"
            "</svg>"
        )

        _logger.info(f"🧩 Avatar generated text: '{display_text}' with font size: {font_size}")
        return b64encode(svg.encode())

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('image_1920'):
                name = vals.get('name', '')
                vals['image_1920'] = self._generate_svg_avatar(name)
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'name' in vals:
            for user in self:
                user.image_1920 = self._generate_svg_avatar(user.name)
        return res
