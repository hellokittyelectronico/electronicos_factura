# -*- coding: utf-8 -*-
# Copyright 2019 NMKSoftware
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import SUPERUSER_ID, api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    _name = "account.journal"

    code_refund = fields.Char("Code refund") 
    secure_sequence_id = fields.Many2one('ir.sequence',
        help='Sequence to use to ensure the securisation of data',
        check_company=True,
        readonly=False, copy=False)
    invoice_comment = fields.Html(
        string="Invoice Comment"
    )

    



# class AccountJournal_2(models.Model):
#     _name = "account.journal"
#     _inherit = "account.journal"

   
#     @api.model
#     def create(self, vals):

#         return super(AccountJournal, self).create(vals)

#     @api.model
#     def _create_sequence(self, vals, refund=False):

#         return super(AccountJournal, self)._create_sequence(vals, refund)