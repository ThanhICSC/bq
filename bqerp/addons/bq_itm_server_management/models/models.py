# -*- coding: utf-8 -*-

from odoo import models, fields, api


class NetworkInterface(models.Model):
    _name = 'bq.itm.server.network.interface'
    _rec_name = 'ip_addr'
    _order = 'priority, ip_addr'

    ip_addr = fields.Char(string="IP Address", required=True)
    priority = fields.Integer(string="Priority", required=False)
    server_id = fields.Many2one("bq.itm.server", string="Server", required=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super(NetworkInterface, self).default_get(fields_list)
        server_id = self.env.context.get('server_id')
        if server_id:
            defaults.update({
                'server_id': server_id
            })
        return defaults


class Model(models.Model):
    _name = 'bq.itm.server.model'
    _order = 'name'

    name = fields.Char(string="Name", required=True)


class OperatingSystem(models.Model):
    _name = 'bq.itm.operating.system'
    _order = 'category, name'

    name = fields.Char('Name', required=True,)
    category = fields.Char('Category')


class Server(models.Model):
    _name = 'bq.itm.server'
    _order = 'name'

    name = fields.Char(string="Name", required=True)
    interface_ids = fields.One2many(comodel_name="bq.itm.server.network.interface", inverse_name="server_id",
                                    string="Interfaces", required=False)
    ip_addrs = fields.Char(compute='_compute_ip_addrs', string='IP Addresses')
    model_id = fields.Many2one(comodel_name="bq.itm.server.model", string="Model", required=False)
    os_id = fields.Many2one(comodel_name='bq.itm.operating.system', string='OS', required=True)
    type = fields.Selection(string="Type", selection=[('guest', 'Guest'), ('host', 'Host'), ], required=True,
                            default='host')
    host_id = fields.Many2one(comodel_name="bq.itm.server", string="Host", required=False,
                              domain=[('host_id', '=', False)])
    guest_ids = fields.One2many(comodel_name='bq.itm.server', inverse_name="host_id", string="Guests", required=False)
    description = fields.Char(string="Description", required=False)
    state = fields.Selection(string="State", selection=[('active', 'Active'), ('closed', 'Closed'), ], required=True,
                             default='active')

    @api.one
    @api.depends('interface_ids')
    def _compute_ip_addrs(self):
        self.ip_addrs = '/'.join(self.interface_ids.sorted('priority').mapped('ip_addr'))

    @api.model
    def default_get(self, fields_list):
        defaults = super(Server, self).default_get(fields_list)
        host_id = self.env.context.get('host_id')
        if host_id:
            defaults.update({
                'type': 'guest',
                'host_id': host_id
            })
        return defaults
