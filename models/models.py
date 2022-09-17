# -*- coding: utf-8 -*-
from odoo import models, fields, modules,tools , api,_ 
import os
import requests
import json 
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import babel

import time
from dateutil import relativedelta
from datetime import datetime, timedelta
from datetime import time as datetime_time


class datos_generales(models.Model):
    _name= 'electronicos_factura.datos_generales'
    _descripcion='electronicos_factura.datos_generales'

    name = fields.Char("Nombre")
    company_id = fields.Many2one('res.company', string='Compañia', readonly=True, copy=False,
        default=lambda self: self.env['res.company']._company_default_get())
        #states={'draft': [('readonly', False)]})

    diario = fields.Many2one('account.journal', string='Diario',ondelete='restrict')
    tipo_factura = fields.Selection(
        selection=[('factura', _('Factura')),
				   ('nota_credito_factura', _('Nota Credito Factura')),
                   ('nota_debito_factura', _('Nota Debito Factura')),
                   ('documento_soporte', _('Documento Soporte')),
                   ('Nota_credito_Documento_soporte', _('Nota Credito Documento Soporte')),],
        string=_('Tipo de documento'), 
        default='factura'
    )
    password = fields.Char('password')
    general_factura = fields.Many2one('base_electronicos.tabla', string='Asignar a',ondelete='restrict', index=True)

    def documento(self):
        valores = self.env['account.invoice'].search([('journal_id.id', '=', self.diario.id)])
        response2={}
        # print(self.journal_id[0])
        for docu in valores: 
            #documento = valores.general_factura.search([('diario', '=', docu.journal_id[0].id)])
            # print(documento)
            # if documento:
            docu.tipo_documento = self.tipo_factura


class base_electronicos(models.Model):
    _name = 'base_electronicos.tabla'
    _inherit = 'base_electronicos.tabla'

    general_factura = fields.One2many('electronicos_factura.datos_generales','general_factura', ondelete='cascade')



class AccountMoveLine(models.Model):
    _inherit = 'account.invoice.line'

    periodo_fecha = fields.Date("Fecha periodo", required=True, default=fields.Date.context_today)
    periodo_codigo = fields.Selection(selection=[('1', 'Por operación'),('2', 'Acumulado Semanal'),],string=_('Periodo'), required=True,default='1')


