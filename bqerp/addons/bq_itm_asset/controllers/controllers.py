# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


def ensure_db():
    db = request.params.get('db') and request.params.get('db').strip()

    # Ensure db is legit
    if db and db not in http.db_filter([db]):
        db = None

    if db and not request.session.db:
        # User asked a specific database on a new session.
        request.session.db = db
        return

    # if db not provided, use the session one
    if not db and request.session.db and http.db_filter([request.session.db]):
        db = request.session.db

    # if no database provided and no database in session, use monodb
    if not db:
        db = http.db_monodb(request.httprequest)

    # always switch the session to the computed db
    if db != request.session.db:
        request.session.logout()

    request.session.db = db


class BqItm(http.Controller):

    @http.route('/bq_itm/interface/get_asset', type='json', auth="public", methods=["POST"])
    def get_asset(self, ita_no, **kw):
        ensure_db()
        assets = request.env['bq.itm.asset.asset'].sudo().search([('asset_no', '=', ita_no)])
        if assets is not None and len(assets)>0:
            asset = assets[0]
            return {
                'code': 0,
                'message': 'ok',
                'asset': {
                'asset_no': asset.asset_no if asset.asset_no else '',
                'brand_name': asset.brand_id.name if asset.brand_id and asset.brand_id is not None else '',
                'model_name': asset.model_no if asset.model_no else '',
                'category_name': asset.category_id.name if asset.category_id and asset.category_id is not None else '',
                'serial_no': asset.serial_no if asset.serial_no else '',
                'mac_addresses': asset.mac_addresses if asset.mac_addresses else '',
                'ip': asset.ip if asset.ip else '',
                'pin': asset.pin if asset.pin else '',
                'location': asset.location_id.complete_name if asset.location_id and asset.location_id is not None else '',
                'employee': asset.employee_id.complete_name if asset.employee_id and asset.employee_id is not None else '',
                'buy_date': asset.buy_date if asset.buy_date else '',
                'original_warranty_years': asset.original_warranty_years,
                'original_warranty_months': asset.original_warranty_months,
                'original_warranty_start_date': asset.original_warranty_start_date if asset.original_warranty_start_date else '',
                'original_warranty_end_date': asset.original_warranty_end_date if asset.original_warranty_end_date else '',
                'original_warranty_number': asset.original_warranty_number if asset.original_warranty_number else '',
                'supplier_warranty_years': asset.supplier_warranty_years,
                'supplier_warranty_months': asset.supplier_warranty_months,
                'supplier_warranty_start_date': asset.supplier_warranty_start_date if asset.supplier_warranty_start_date else '',
                'supplier_warranty_end_date': asset.supplier_warranty_end_date if asset.supplier_warranty_end_date else '',
                'renewal_method': asset.renewal_method_id.name if asset.renewal_method_id and asset.renewal_method_id is not None else '',
                'supplier': asset.supplier_id.name if asset.supplier_id and asset.supplier_id is not None else '',
                'supplier_contact': asset.contact_id.complete_name if asset.contact_id and asset.contact_id is not None else '',
                'contract_no': asset.contract_no if asset.contract_no else '',
                'supplier_number': asset.supplier_number if asset.supplier_number else '',
                'remark': asset.description if asset.description else '',
                }
            }
        else:
            return {
                'code': -1,
                'message': 'Not found!'
            }
