# -*- coding: utf-8 -*-

import hashlib

from odoo import models, fields, api, tools, exceptions, _
from odoo.exceptions import UserError, ValidationError
import datetime
import dateutil

LOCATION_COMPLETE_NAME_SEPARATOR = ' / '


class Location(models.Model):
    _name = 'bq.itm.asset.location'
    _description = 'Location'
    _rec_name = 'complete_name'
    _order = 'parent_id, complete_name'

    name = fields.Char('Name', required=True)
    complete_name = fields.Char(string='Complete Name', compute='_compute_complete_name', store=True)
    parent_id = fields.Many2one('bq.itm.asset.location', string='Parent Location', ondelete='restrict', index=True)
    child_ids = fields.One2many('bq.itm.asset.location', 'parent_id', string='Sub Locations')
    asset_qty = fields.Integer(string="Asset Qty", compute='_compute_asset_qty')
    asset_ids = fields.One2many('bq.itm.asset.asset', 'location_id', string='Assets')
    description = fields.Text('Description')
    sequence = fields.Integer(string="Sequence", default=0)
    active = fields.Boolean('Active?', default=True)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive locations.'))

    @api.multi
    @api.depends('name', 'parent_id')
    def _compute_complete_name(self):
        for record in self:
            if record.name:
                name = record.name
                current = record
                while current.parent_id:
                    current = current.parent_id
                    name = LOCATION_COMPLETE_NAME_SEPARATOR.join((current.name, name))
                record.complete_name = name
            else:
                record.complete_name = False

    @api.multi
    def _compute_asset_qty(self):
        asset_data = self.env['bq.itm.asset.asset'].read_group([('location_id', 'in', self.ids)], ['location_id'],
                                                               ['location_id'])
        mapped_data = dict([(m['location_id'][0], m['location_id_count']) for m in asset_data])
        for location in self:
            location.asset_qty = mapped_data.get(location.id, 0)

    @api.multi
    def unlink(self):
        for location in self:
            if location.asset_ids:
                raise UserError(_("You cannot delete a location containing assets."))
        return super(Location, self).unlink()

    @api.multi
    def write(self, vals):
        result = super(Location, self).write(vals)
        if not self.env.context.get('set_sub_complete_names'):
            if 'parent_id' in vals or 'name' in vals:
                self = self.with_context(set_sub_complete_names=True)
                for record in self:
                    self._set_sub_complete_names(record, LOCATION_COMPLETE_NAME_SEPARATOR)
        return result

    def _set_sub_complete_names(self, record, separator):
        for child in record.child_ids:
            child.complete_name = separator.join((record.complete_name, child.name))
            self._set_sub_complete_names(child, separator)


class Category(models.Model):
    _name = 'bq.itm.asset.category'
    _description = 'Category'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    asset_ids = fields.One2many('bq.itm.asset.asset', 'category_id', string='Assets')
    attribute_ids = fields.One2many('bq.itm.asset.attribute', 'category_id', string='Attributes')
    asset_qty = fields.Integer(string="Asset Qty", compute='_compute_asset_qty')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another category already exists with this name!"),
    ]

    @api.multi
    def _compute_asset_qty(self):
        asset_data = self.env['bq.itm.asset.asset'].read_group([('category_id', 'in', self.ids)], ['category_id'],
                                                               ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in asset_data])
        for category in self:
            category.asset_qty = mapped_data.get(category.id, 0)

    @api.multi
    def unlink(self):
        for category in self:
            if category.asset_ids:
                raise UserError(_("You cannot delete a category containing assets."))
        return super(Category, self).unlink()


class Attribute(models.Model):
    _name = 'bq.itm.asset.attribute'
    _description = 'Attribute'
    _order = 'category_id, sequence, name'

    name = fields.Char('Name', required=True)
    value = fields.Char('Value', required=True)
    category_id = fields.Many2one('bq.itm.asset.category', string='Category', ondelete='restrict', index=True)
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    @api.multi
    def name_get(self):
        return [(record.id, ''.join((record.name, ': ', record.value))) for record in self]


class Brand(models.Model):
    _name = 'bq.itm.asset.brand'
    _description = 'Brand'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    asset_ids = fields.One2many('bq.itm.asset.asset', 'brand_id', string='Assets')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another brand already exists with this name!"),
    ]


class RenewalMethod(models.Model):
    _name = 'bq.itm.asset.renewal.method'
    _description = 'Renewal Method'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another method already exists with this name!"),
    ]


class Supplier(models.Model):
    _name = 'bq.itm.asset.supplier'
    _description = 'Supplier'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    # contact = fields.Char('Contact', required=True)
    # contact_number = fields.Char('Contact Number', required=True)
    supplier_number = fields.Char('Supplier Number')
    # contact_complete_name = fields.Char(compute='_compute_complete_name', string='Complete Name', store=True)
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    contact_ids = fields.One2many(comodel_name="bq.itm.asset.supplier.contact",
                                  inverse_name="supplier_id", string="Contact", required=False, )

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another supplier already exists with this name!"),
    ]


class SupplierContact(models.Model):
    _name = 'bq.itm.asset.supplier.contact'
    _rec_name = 'complete_name'
    _description = 'Contact of supplier'

    name = fields.Char('Name', required=True)
    supplier_id = fields.Many2one(comodel_name="bq.itm.asset.supplier", string="Supplier", required=False, )
    contact_number = fields.Char('Contact Number', required=True)
    complete_name = fields.Char(compute='_compute_complete_name', string='Complete Name', store=True)

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super(SupplierContact, self).default_get(fields_list)
        supplier_id = self.env.context.get('supplier_id')
        if supplier_id:
            defaults.update({
                'supplier_id': supplier_id
            })
        return defaults

    @api.depends('name', 'contact_number')
    def _compute_complete_name(self):
        for contact in self:
            if contact and contact is not None:
                names = [contact.name, contact.contact_number]
                contact.complete_name = ' / '.join(filter(None, names))


class Asset(models.Model):
    _name = 'bq.itm.asset.asset'
    _inherit = ['mail.thread']
    _rec_name = 'asset_no'
    _description = 'Asset'
    _order = 'asset_no'

    asset_no = fields.Char('Asset No.', required=True, default='ITA000000', track_visibility='onchange')
    employee_id = fields.Many2one('bq.base.employee', string='Keeper', ondelete='restrict', index=True,
                                  track_visibility='onchange')
    department_id = fields.Many2one('bq.base.department', string='Department', ondelete='restrict', index=True,
                                    track_visibility='onchange')
    category_id = fields.Many2one('bq.itm.asset.category', string='Category', ondelete='restrict', index=True,
                                  track_visibility='onchange')
    brand_id = fields.Many2one('bq.itm.asset.brand', string='Brand', ondelete='restrict', index=True,
                               track_visibility='onchange')
    model_no = fields.Char('Model No.', track_visibility='onchange')
    serial_no = fields.Char('Serial No.', track_visibility='onchange')
    attribute_ids = fields.Many2many('bq.itm.asset.attribute', string='Attributes', track_visibility='onchange')
    assign_date = fields.Date('Assigned Date', track_visibility='onchange')
    use = fields.Selection(
        [('personal office', 'Personal Office'), ('shared office', 'Shared Office'),
         ('it infrastructure', 'IT Infrastructure'), ('production equipment', 'Production Equipment'),
         ('national confidential', 'National Confidential')],
        string='Use', track_visibility='onchange')
    network = fields.Selection(
        [('office', 'Office'), ('production', 'Production'), ('equipment', 'Equipment')],
        string='Network', track_visibility='onchange')
    mac_addresses = fields.Text('Mac Addresses')
    cost = fields.Float('Cost', track_visibility='onchange')
    description = fields.Text('Description', track_visibility='onchange')
    warranty = fields.Date('Warranty', track_visibility='onchange')
    image = fields.Binary('Asset Image', attachment=True,
                          help="This field holds the image used as picture for the asset.")
    location_id = fields.Many2one('bq.itm.asset.location', string='Location', ondelete='restrict', index=True,
                                  track_visibility='onchange')
    finance_asset_no = fields.Char('Finance Asset No.', track_visibility='onchange')
    po_no = fields.Char('PO Number', track_visibility='onchange')
    start_date = fields.Date('Start Date', track_visibility='onchange')
    idle = fields.Boolean('Idle?', default=False, track_visibility='onchange')
    repair_place = fields.Selection([('field', 'Field'), ('supplier', 'Supplier'), ('IT', 'IT')],
                                    string='Repair Place', track_visibility='onchange')
    active = fields.Boolean('Active?', default=True, track_visibility='onchange')
    count_item_ids = fields.One2many('bq.itm.asset.count.item', 'asset_id', string='Count Records')
    cancel_date = fields.Date('Cancel Date', track_visibility='onchange')
    cancel_type = fields.Selection([('retired', 'Retired'), ('damaged', 'Damaged'), ('lost', 'Lost'),
                                    ('sold', 'Sold'), ('other', 'Other')], string='Cancel Type',
                                   track_visibility='onchange')
    cancel_description = fields.Text('Cancel Description', track_visibility='onchange')

    ip = fields.Char('IP', track_visibility='onchange')
    pin = fields.Char('P/N', track_visibility='onchange')
    buy_date = fields.Date('Buy Date', track_visibility='onchange')
    original_warranty_years = fields.Integer('Original Warranty Years', track_visibility='onchange', default=2)
    original_warranty_months = fields.Integer('Original Warranty Months', track_visibility='onchange', default=36)
    original_warranty_start_date = fields.Date('Original Warranty Start Date', track_visibility='onchange')
    original_warranty_end_date = fields.Date('Original Warranty End Date',
                                             compute='_compute_original_warranty_end_date', store=True)
    original_warranty_number = fields.Char('Original Warranty Number')
    supplier_warranty_years = fields.Integer('Supplier Warranty Years', track_visibility='onchange', default=2)
    supplier_warranty_months = fields.Integer('Supplier Warranty Month', track_visibility='onchange', default=36)
    supplier_warranty_start_date = fields.Date('Supplier Warranty Start Date', track_visibility='onchange')
    supplier_warranty_end_date = fields.Date('Supplier Warranty End Date',
                                             compute='_compute_supplier_warranty_end_date', store=True)
    supplier_id = fields.Many2one('bq.itm.asset.supplier', string='Supplier', ondelete='restrict', index=True,
                               track_visibility='onchange')
    contract_no = fields.Char('Contract No', track_visibility='onchange')
    # supplier_number = fields.Char('Contact Number', related='supplier_id.supplier_number', store=True)
    supplier_number = fields.Char('Contact Number')
    # contact_complete_name = fields.Char('Contact Complete Name', compute='_compute_contact_complete_name',
    #                                     store=True)
    contact_id = fields.Many2one('bq.itm.asset.supplier.contact', string='Contact',
                                 # domain=lambda self: self._get_possible_model_domain(),
                                 # default=lambda self: self.supplier_id.contact_ids[0],
                                 # domain=lambda self: [('supplier_id', '=', self.supplier_id.id)]
                                 )
    renewal_method_id = fields.Many2one('bq.itm.asset.renewal.method', string='Renewal Method', ondelete='restrict',
                                        index=True, track_visibility='onchange')

    def _get_possible_model_domain(self):
        sid = self.supplier_id.id
        return [('supplier_id', '=', self.supplier_id.id)]

    @api.onchange('supplier_id')
    def _compute_contact_complete_name(self):
        value = dict()
        self.contact_id = False
        if self.supplier_id and self.supplier_id is not None:
            self.supplier_number = self.supplier_id.supplier_number
            domain = [('supplier_id', '=', self.supplier_id.id)]
        else:
            domain = [('supplier_id', '=', None)]
        value['domain'] = dict()
        value['domain']['contact_id'] = domain
        return value

    @api.depends('original_warranty_months', 'original_warranty_start_date')
    def _compute_original_warranty_end_date(self):
        for asset in self:
            if asset.original_warranty_months > 0 and asset.original_warranty_start_date:
                asset.original_warranty_end_date = \
                    datetime.datetime.strptime(asset.original_warranty_start_date,'%Y-%m-%d') + \
                    dateutil.relativedelta.relativedelta(months=asset.original_warranty_months)

    @api.depends('supplier_warranty_months', 'supplier_warranty_start_date')
    def _compute_supplier_warranty_end_date(self):
        for asset in self:
            if asset.supplier_warranty_months > 0 and asset.supplier_warranty_start_date:
                asset.supplier_warranty_end_date = \
                    datetime.datetime.strptime(asset.supplier_warranty_start_date, '%Y-%m-%d') + \
                    dateutil.relativedelta.relativedelta(months=asset.supplier_warranty_months)

    @api.one
    @api.constrains('asset_no')
    def _check_asset_no_size(self):
        if len(self.asset_no) < 9:
            raise exceptions.ValidationError(_('Asset Number must have 9 chars!'))

    _sql_constraints = [
        ('asset_no_unique', 'unique(asset_no)',
         "Another asset already exists with this Asset No.!"),
    ]

    @api.model
    def create(self, vals):
        asset = super(Asset, self).create(vals)
        # subscribe employee or department manager when equipment assign to him.
        user_ids = []
        if asset.employee_id and asset.employee_id.user_id:
            user_ids.append(asset.employee_id.user_id.id)
        if asset.department_id and asset.department_id.manager_id and asset.department_id.manager_id.user_id:
            user_ids.append(asset.department_id.manager_id.user_id.id)
        if user_ids:
            asset.message_subscribe_users(user_ids=user_ids)
        return asset

    @api.multi
    def write(self, vals):
        user_ids = []
        # subscribe employee or department manager when equipment assign to employee or department.
        if vals.get('employee_id'):
            user_id = self.env['bq.base.employee'].browse(vals['employee_id'])['user_id']
            if user_id:
                user_ids.append(user_id.id)
        if vals.get('department_id'):
            department = self.env['bq.base.department'].browse(vals['department_id'])
            if department and department.manager_id and department.manager_id.user_id:
                user_ids.append(department.manager_id.user_id.id)
        if user_ids:
            self.message_subscribe_users(user_ids=user_ids)
        return super(Asset, self).write(vals)


class Employee(models.Model):
    _inherit = ['bq.base.employee']

    bq_itm_asset_asset_ids = fields.One2many('bq.itm.asset.asset', 'employee_id', string='IT Assets')
    bq_itm_asset_asset_qty = fields.Integer(string='Asset Qty', compute='_compute_asset_qty')
    bq_itm_asset_keeping_code = fields.Char(string='Keeping Code', compute='_compute_keeping_code', store=True)
    bq_itm_asset_signed_keeping_code = fields.Char(string='Signed Keeping Code', track_visibility='onchange')
    bq_itm_asset_keeping_sign_needed = fields.Boolean(string='Keeping Sign Needed',
                                                      compute='_compute_keeping_sign_needed', store=True)

    @api.multi
    def _compute_asset_qty(self):
        asset_data = self.env['bq.itm.asset.asset'].read_group([('employee_id', 'in', self.ids)], ['employee_id'],
                                                               ['employee_id'])
        mapped_data = dict([(m['employee_id'][0], m['employee_id_count']) for m in asset_data])
        for employee in self:
            employee.bq_itm_asset_asset_qty = mapped_data.get(employee.id, 0)

    @api.depends('bq_itm_asset_asset_ids')
    def _compute_keeping_code(self):
        for employee in self:
            if len(employee.bq_itm_asset_asset_ids) > 0:
                asset_no_list_string = ''.join(sorted(employee.bq_itm_asset_asset_ids.mapped('asset_no')))
                employee.bq_itm_asset_keeping_code = \
                    employee.employee_no + '-' \
                    + hashlib.md5(asset_no_list_string.upper().encode('utf-8')).hexdigest()[:6]
            else:
                employee.bq_itm_asset_keeping_code = None

    @api.depends('bq_itm_asset_keeping_code', 'bq_itm_asset_signed_keeping_code')
    def _compute_keeping_sign_needed(self):
        for employee in self:
            employee.bq_itm_asset_keeping_sign_needed = None
            if employee.bq_itm_asset_keeping_code is not None:
                if employee.bq_itm_asset_keeping_code != employee.bq_itm_asset_signed_keeping_code:
                    employee.bq_itm_asset_keeping_sign_needed = True
                else:
                    employee.bq_itm_asset_keeping_sign_needed = False


class Count(models.Model):
    _name = 'bq.itm.asset.count'
    _description = 'Count'
    _order = 'plan_date desc'

    name = fields.Char('Subject', required=True)
    plan_date = fields.Date('Plan Date', required=True)
    item_ids = fields.One2many('bq.itm.asset.count.item', 'count_id', string='Count Items')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('done', 'Done'), ('cancelled', 'Cancelled')],
                             string='State', default='draft', required=True)
    description = fields.Text('Description')
    item_qty = fields.Integer(string="Item Qty", compute='_compute_item_qty')

    @api.multi
    def _compute_item_qty(self):
        item_data = self.env['bq.itm.asset.count.item'].read_group([('count_id', 'in', self.ids)],
                                                                   ['count_id'], ['count_id'])
        mapped_data = dict([(m['count_id'][0], m['count_id_count']) for m in item_data])
        for count in self:
            count.item_qty = mapped_data.get(count.id, 0)


class CountItem(models.Model):
    _name = 'bq.itm.asset.count.item'
    _description = 'Count Item'
    _rec_name = 'asset_id'
    _order = 'asset_id'

    count_id = fields.Many2one('bq.itm.asset.count', string='Count', ondelete='cascade', auto_join=True, index=True)
    asset_id = fields.Many2one('bq.itm.asset.asset', string='Asset', required=True, index=True)
    state = fields.Selection([('unknown', 'Unknown'), ('ok', 'OK'), ('missed', 'Missed'), ('damaged', 'Damaged')],
                             string='Result', default='unknown', required=True)
    employee_id = fields.Many2one('bq.base.employee', string='Executor', index=True)
    count_date = fields.Date('Count Date')
    image = fields.Binary('Asset Image', attachment=True,
                          help="This field holds the image used as picture for the asset.")
    description = fields.Text('Description')

    _sql_constraints = [
        ('asset_unique', 'unique(count_id, asset_id)',
         "Another item already exists with this Asset No.!"),
    ]


class CountWizard(models.TransientModel):
    _name = 'bq.itm.asset.count.wizard'
    _description = 'Count Wizard'

    name = fields.Char('Subject', required=True)
    asset_ids = fields.Many2many('bq.itm.asset.asset', string='Assets')
    plan_date = fields.Date('Plan Date', required=True)
    description = fields.Text('Description')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            res = {'asset_ids': active_ids}
        return res

    @api.multi
    def create_count(self):
        self.ensure_one()
        count_dataset = self.env['bq.itm.asset.count']
        count_item_dataset = self.env['bq.itm.asset.count.item']
        new_count = count_dataset.create({'name': self.name, 'plan_date': self.plan_date,
                                          'description': self.description})
        for this_asset_id in self.asset_ids:
            count_item_dataset.create({'count_id': new_count.id, 'asset_id': this_asset_id.id})
        return {'type': 'ir.actions.act_window', 'res_model': 'bq.itm.asset.count',
                'res_id': new_count.id, 'view_type': 'form', 'view_mode': 'form'}


class KeepingConfirmWizard(models.TransientModel):
    _name = 'bq.itm.asset.keeping.confirm.wizard'
    _description = 'Keeping Confirm Wizard'

    signed_keeping_code = fields.Char('Signed Keeping Code', required=True)

    @api.multi
    def confirm_keeping(self):
        self.ensure_one()
        employee_dataset = self.env['bq.base.employee']
        employee_no = self.signed_keeping_code[0:self.signed_keeping_code.find('-')]
        employee = employee_dataset.search([('employee_no', '=', employee_no)])
        if employee:
            employee.bq_itm_asset_signed_keeping_code = self.signed_keeping_code
            return {
                'name': _('Keeping Confirm Wizard'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': self._name,
                'target': 'new',
                'context': {
                    'default_signed_keeping_code': self[0].signed_keeping_code
                }
            }
        else:
            raise UserError(_("Employee No %s doesn't exist") % employee_no)

    @api.multi
    def remove_confirm_keeping(self):
        self.ensure_one()
        employee_dataset = self.env['bq.base.employee']
        employee_no = self.signed_keeping_code[0:self.signed_keeping_code.find('-')]
        employee = employee_dataset.search([('employee_no', '=', employee_no)])
        if employee:
            employee.bq_itm_asset_signed_keeping_code = None
        else:
            raise UserError(_("Employee No %s doesn't exist") % employee_no)
