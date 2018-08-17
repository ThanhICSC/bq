# -*- coding: utf-8 -*-
# Copyright (C) 2018 MAXSNS Corp (http://www.maxsns.com)
# @author Henry Zhou (zhouhenry@live.com)
# License OPL-1 - See https://www.odoo.com/documentation/user/11.0/legal/licenses/licenses.html

from odoo import models, fields, api


class WeChatAccount(models.Model):
    _name = 'wechat.account'
    _description = "WeChat Account"

    app_id = fields.Char(string="App ID", required=True)
    open_id = fields.Char(string="Open ID", required=True, index=True)
    user_id = fields.Many2one("res.users", string="User", required=True)

    _sql_constraints = [
        ('app_id_open_id_uniq', 'unique(app_id, open_id)',
         'The open_id must be unique per app_id!'),
    ]


class ResUsers(models.Model):
    _inherit = "res.users"

    wechat_union_id = fields.Char(string="WeChat Union ID", index=True)
    wechat_account_ids = fields.One2many('wechat.account', 'user_id', string="WeChat Accounts")
