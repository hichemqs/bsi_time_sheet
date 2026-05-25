# -*- coding: utf-8 -*-

import base64
import binascii
from odoo import fields, http, _
from odoo.http import request, content_disposition
from odoo.exceptions import AccessError, MissingError
from odoo.addons.sale.controllers import portal as sale_portal
from odoo.addons.portal.controllers.mail import _message_post_helper


class SalePortal(sale_portal.CustomerPortal):
    @http.route(['/my/orders/<int:order_id>/report'], type='http', auth="public", website=True)
    def portal_show_contract_report(self, order_id, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
            if not order_sudo.contrat_finalise:
                raise MissingError(_("This document does not exist."))
        except (AccessError, MissingError):
            return request.redirect('/my')

        report = base64.b64decode(order_sudo.contrat_finalise)
        headers = {
            'Content-Type': 'application/pdf',
            'Content-Length': len(report),
        }

        return request.make_response(report, headers=list(headers.items()))

    @http.route(['/my/orders/<int:order_id>/accept'], type='json', auth="public", website=True)
    def portal_quote_accept(self, order_id, access_token=None, name=None, signature=None):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not order_sudo._has_to_be_signed():
            return {'error': _('The order is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            order_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}

        if not order_sudo._has_to_be_paid():
            order_sudo.with_context(send_email=True).action_confirm()

        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf('sale.action_report_saleorder', [order_sudo.id])[0]

        _message_post_helper(
            'sale.order',
            order_sudo.id,
            _('Contrat signé par %s', name),
            attachments=[('%s.pdf' % order_sudo.name, pdf)],
            token=access_token,
        )

        query_string = '&message=sign_ok'
        if order_sudo._has_to_be_paid():
            query_string += '#allow_payment=yes'
        return {
            'force_refresh': True,
            'redirect_url': order_sudo.get_portal_url(query_string=query_string),
        }