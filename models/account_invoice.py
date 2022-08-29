from odoo import models, fields, modules,tools , api,_ 
import os
import requests
import json 
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import babel
from odoo.tools.safe_eval import safe_eval

import time
from dateutil import relativedelta
from datetime import datetime, timedelta
from datetime import time as datetime_time

class AccountMove(models.Model):
    _inherit = 'account.move'
    #_inherit = 'account.move' 

    codigo_qr = fields.Char('codigo_qr')                       
    cufe = fields.Char('cufe')   
    factura_cfdi = fields.Boolean("si si o no")
    rechazo = fields.Char('rechazo')                       
    grafica_link = fields.Char('pdf')
    factura_electronica = fields.Boolean('Factura Electronica')
    nota_debito = fields.Selection(
        selection=[('1', '1 Intereses'), 
                   ('2', '2 Gastos por cobrar'), 
                   ('3', '3 Cambio del valor'),
                   ('4', '4 Otro'),],
        string=_('Tipo de Nota debito'),
    )
    nota_credito = fields.Selection(
        selection=[('1', '1 Devolución de parte de los bienes; no aceptación de partes del servicio'), 
                   ('2', '2 Anulación de factura electrónica'), 
                   ('3', '3 Rebaja total aplicada'),
                   ('4', '4 Descuento total aplicado'), 
                   ('5', '5 Rescisión: nulidad por falta de requisitos'), 
                   ('6', '6 Otros'), ],
        string=_('Tipo de Nota credito'),
    )
    factura = fields.Many2one('account.move', domain="[('estado_factura', 'in', ('factura_correcta','a'))]")#,relation='partner_delivery_partner_rel',column1="id", column2="id2"
    tipoc_o_d = fields.Char('tipo')
    tipo_comprobante = fields.Selection(
        selection=[('I', 'Ingreso'), 
                   ('E', 'Egreso'),
                    ('T', 'Traslado'),],
        string=_('Tipo de comprobante'),
    )
    #forma_pago = fields.Selection(
    tipo_pago = fields.Selection(    
        selection=[#('1', '1 - Instrumento no definido'), 
                   #('2', '2 - Crédito ACH'), 
                   #('3', '3 - Débito ACH'),
                   #('4', '4 - Reversión débito de demanda ACH'), 
                   #('5', '5 - Reversión crédito de demanda ACH'),
                   #('6', '6 - Crédito de demanda ACH'), 
                   #('7', '7 - Débito de demanda ACH'), 
                   #('8', '8 - Mantener'), 
                   #('9', '9 - Clearing Nacional o Regional'), 
                   ('10', '10 - Efectivo'), 
                   #('11', '11 - Reversión Crédito Ahorro'), 
                   #('12', '12 - Reversión Débito Ahorro'), 
                   #('13', '13 - Crédito Ahorro'), 
                   #('14', '14 - Débito Ahorro'), 
                   #('15', '15 - Bookentry Crédito'), 
                   #('16', '16 - Bookentry Débito'), 
                   #('17', '17 - Concentración de la demanda en efectivo /Desembolso Crédito (CCD)'), 
                   #('18', '18 - Concentración de la demanda en efectivo / Desembolso (CCD) débito'),
                   #('19', '19 - Crédito Pago negocio corporativo (CTP)'), 
                   ('20', '20 - Cheque'), 
                   #('21', '21 - Poyecto bancario'), 
                   #('22', '22 - Proyecto bancario certificado'), 
                   #('23', '23 - Cheque bancario'), 
                   #('24', '24 - Nota cambiaria esperando aceptación'), 
                   #('25', '25 - Cheque certificado'), 
                   #('26', '26 - Cheque Local'), 
                   #('27', '27 - Débito Pago Neogcio Corporativo (CTP)'), 
                   #('28', '28 - Crédito Negocio Intercambio Corporativo (CTX)'), 
                   #('29', '29 - Débito Negocio Intercambio Corporativo (CTX)'), 
                   #('30', '30 - Transferecia Crédito'), 
                   ('42', '42 - Consignación bancaria'), 
                   ('ZZZ', 'ZZZ - Acuerdo mutuo'),],
        string=_('Tipo de pago'), default='10'
    )
    methodo_pago = fields.Selection(
        selection=[('1', _('Contado')),
				   ('2', _('Credito')),],
        string=_('Método de pago'), 
        default='1'
    )
    tipo_factura = fields.Selection(
        selection=[('1', _('1- Combustibles')),
                   ('2', _('2- Emisor es Autorretenedor')),
                   ('3', _('3- Excluidos y Exentos')),
                   ('4', _('4- Extranjero')),
                   ('5', _('5- Generica')),
                   ('6', _('6- Generica con pago anticipado')),
                   ('7', _('7- Generica con periodo de facturacion')),
                   ('8', _('8- Consorcio')),
                   ('9', _('9- Servicios AIU')),
                   ('10', _('10- Estandar')),],
        string=_('Tipo de factura'),
        default ='10'
    )
    xml_invoice_link = fields.Char(string=_('XML Invoice Link'))
    estado_factura = fields.Selection(
        selection=[('factura_no_generada', 'Factura no generada'), ('factura_correcta', 'Factura correcta'), 
                   ('problemas_factura', 'Problemas con la factura'), ('solicitud_cancelar', 'Cancelación en proceso'),
                   ('cancelar_rechazo', 'Cancelación rechazada'), ('factura_cancelada', 'Factura cancelada'), ],
        string=_('Estado de factura'),
        default='factura_no_generada',
        readonly=False
    )
    pdf_cdfi_invoice = fields.Binary("CDFI Invoice")
    qrcode_image = fields.Binary("QRCode")
    regimen_fiscal = fields.Selection(
        selection=[('0', _('Simplificado')),
                   ('2', _('Comun')),],
        string=_('Régimen Fiscal'), 
    )
    transaccionID = fields.Char(string=_('transaccionID'))
    impresa = fields.Char(string=_('Impresa'))
    fecha_factura = fields.Datetime(string=_('Fecha Factura'), readonly=True)
    nombre_not = fields.Char(string=_('Nombre nota'))
    checkin = fields.Char(string=_('Checkin'))
    checkout = fields.Char(string=_('Checkout'))
    estado_factura = fields.Selection([
        ('no_generada', 'No_generada'),
        ('Generada_correctamente', 'Generada_correctamente'),
        ('Generada_con_errores', 'Generada_con_errores'),
    ], string='Estado',default="no_generada")
    impreso = fields.Boolean("Impreso?")
    # FechaGen = fields.Char('Fecha Generacion')
    # HoraGen = fields.Char('Hora Generacion')
    # id_plataforma = fields.Char('id_plataforma')
    # password = fields.Char('password')
    # cune = fields.Char('CUNE')
    # PeriodoNomina = fields.Char('Periodo Nomina') 
    # TipoMoneda = fields.Char('TipoMoneda', default="COP") 

    # Notas = fields.Char('Notas')    
    tipo_documento = fields.Char(string="Documento", compute='documento',store=True)#
    
    sub_tipo_documento = fields.Selection([
        ('Factura_Electronica', 'Factura Electronica'),
        ('Nota_debito', 'Nota_debito'),
        ('Documento_soporte', 'Documento_soporte'),
    ], string='Tipo documento')

    calidades_atributos = fields.Many2many("account.calidadess")
    usuario_aduanero = fields.Many2many("account.aduaneros")    
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False
        tipo_pago = '10'
        tipo_factura = '1'
        metodo_pago = '10'
        warning = {}
        domain = {}
        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id #.with_context(force_company=company_id) #with_company(company_id)#
        type = self.move_type
        if p:
            rec_account = p.property_account_receivable_id
            pay_account = p.property_account_payable_id
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('in_invoice', 'in_refund'):
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term_id.id
            else:
                account_id = rec_account.id
                payment_term_id = p.property_payment_term_id.id
            
            delivery_partner_id = self.partner_id.id #self.get_delivery_partner_id()
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=delivery_partner_id)

            if p.tipo_factura:
                tipo_factura = p.tipo_factura
            if p.tipo_pago:
                tipo_pago = p.tipo_pago
            if p.metodo_pago:
                metodo_pago = p.metodo_pago
            # If partner has no warning, check its company
            if p.invoice_warn == 'no-message' and p.parent_id:
                p = p.parent_id
            if p.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                    p = p.parent_id
                warning = {
                    'title': _("Warning for %s") % p.name,
                    'message': p.invoice_warn_msg
                    }
                if p.invoice_warn == 'block':
                    self.partner_id = False

        # self.account_id = account_id
        # self.payment_term_id = payment_term_id
        self.invoice_date = False
        self.fiscal_position_id = fiscal_position

        self.tipo_factura = tipo_factura
        self.tipo_pago = tipo_pago
        # self.metodo_pago = metodo_pago

        if type in ('in_invoice', 'out_refund'):
            bank_ids = p.commercial_partner_id.bank_ids
            bank_id = bank_ids[0].id if bank_ids else False
            self.partner_bank_id = bank_id
            domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}

        res = {}
        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        return res


    @api.depends('journal_id')
    def documento(self):
        valores = self.env['base_electronicos.tabla'].search([('name', '=', 'Factura electrónica')])
        response2={}
        valores_lineas = valores.mp_id
        print("haber")
        print(self.journal_id)
        documento = valores.general_factura.search([('diario', '=', self.journal_id.id)])
        print(documento)
        if documento:
            if self.move_type == "out_invoice" and documento.tipo_factura == "factura":
                self.tipo_documento = documento.tipo_factura
            elif self.move_type == "out_refund" and documento.tipo_factura == "factura":
                self.tipo_documento = "Nota Credito"
            elif self.move_type == "in_invoice" and documento.tipo_factura == "documento_soporte":
                self.tipo_documento = documento.tipo_factura
            elif self.move_type == "in_refund" and documento.tipo_factura == "documento_soporte":
                self.tipo_documento = "Nota Credito Doc soporte"
        # datos_generales = self.env['electronicos_factura.datos_generales'].search([('diario', '=', self.journal_id[0].id)])
        # if datos_generales: 
        #     self.tipo_documento = "soporte"
        # if datos_generales: 
        #     self.tipo_documento = "factura"
    #@api.multi
    @api.returns('self')
    def refund(self, invoice_date=None, date=None, description=None, journal_id=None,nota_credito=None):
        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self._prepare_refund(invoice, invoice_date=invoice_date, date=date,
                                    description=description, journal_id=journal_id,nota_credito=nota_credito)
            refund_invoice = self.create(values)
            invoice_type = {'out_invoice': ('customer invoices credit note'),
                'in_invoice': ('vendor bill credit note')}
            message = _("This %s has been created from: <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>") % (invoice_type[invoice.type], invoice.id, invoice.number)
            refund_invoice.message_post(body=message)
            new_invoices += refund_invoice
        return new_invoices

    @api.model
    def _prepare_refund(self, invoice, invoice_date=None, date=None, description=None, journal_id=None,nota_credito=None):
        values = super(AccountInvoice, self)._prepare_refund(invoice, invoice_date=invoice_date, 
                                                           date=date, description=description, journal_id=journal_id)
        if invoice.estado_factura == 'generada_correctamente':
            # values['uuid_relacionado'] = invoice.folio_fiscal
            # values['methodo_pago'] = invoice.methodo_pago
            # values['tipo_pago'] = invoice.tipo_pago
            # values['tipo_comprobante'] = 'E'
            # values['uso_cfdi'] = 'G02'
            # values['tipo_relacion'] = '01'
            values['nota_credito'] = nota_credito
            values['factura'] = invoice.id

        return values

    # @api.model
    # def refund(self, invoice_date=None, date=None, description=None, journal_id=None):
    #     values = super(AccountInvoice, self).refund(invoice, invoice_date=invoice_date, 
    #                                                        date=date, description=description, journal_id=journal_id)
    #     if invoice.estado_factura == 'factura_correcta':
    #         # values['uuid_relacionado'] = invoice.folio_fiscal
    #         # values['methodo_pago'] = invoice.methodo_pago
    #         # values['tipo_pago'] = invoice.tipo_pago
    #         # values['tipo_comprobante'] = 'E'
    #         # values['uso_cfdi'] = 'G02'
    #         # values['tipo_relacion'] = '01'
    #         values['nota_debito'] = nota_debito

    #     return values

    #@api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if self.estado_factura == 'factura_correcta' or self.estado_factura == 'factura_cancelada':
            default['estado_factura'] = 'factura_no_generada'
            #default['folio_fiscal'] = ''
            default['fecha_factura'] = None
            default['factura_cfdi'] = False
        return super(AccountInvoice, self).copy(default=default)
    
    #@api.one
    @api.depends('number')
    def _get_number_folio(self):
        if self.number:
            self.number_folio = self.number.replace('INV','').replace('/','')

    #@api.one        
    @api.depends('amount_total', 'currency_id')
    def _get_amount_to_text(self):
        self.amount_to_text = amount_to_text_es_MX.get_amount_to_text(self, self.amount_total, 'es_cheque', self.currency_id.name)
        
    @api.model
    def _get_amount_2_text(self, amount_total):
        return amount_to_text_es_MX.get_amount_to_text(self, amount_total, 'es_cheque', self.currency_id.name)

    #@api.multi
    @api.onchange('payment_term_id')
    def _get_metodo_pago(self):
        return
        # if self.payment_term_id:
        #     if self.payment_term_id.methodo_pago == 'PPD':
        #         values = {
        #          'methodo_pago': self.payment_term_id.methodo_pago,
        #          'tipo_pago': '99'
        #         }
        #     else:
        #         values = {
        #             'methodo_pago': self.payment_term_id.methodo_pago,
        #             'tipo_pago': False
        #             }
        # else:
        #     values = {
        #         'methodo_pago': False,
        #         'tipo_pago': False
        #         }
        # self.update(values)
    

    
    #@api.multi
    def generate_cfdi_invoice(self):
        # after validate, send invoice data to external system via http post
        for invoice in self:
            if estado_factura == 'factura_correcta':
                raise UserError(_('Error para timbrar factura, Factura ya generada.'))
            if estado_factura == 'factura_cancelada':
                raise UserError(_('Error para timbrar factura, Factura ya generada y cancelada.'))
            self.fecha_factura= datetime.now()
            values = invoice.to_json()
            url = "https://odoo15.navegasoft.com/admonclientes/objects/"
            response = requests.post(url , 
                                     auth=None,verify=False, data=json.dumps(values), 
                                     headers={"Content-type": "application/json"})

            #print 'Response: ', response.status_code
            json_response = response.json()
            xml_file_link = False
            estado_factura = json_response['estado_factura']
            if estado_factura == 'problemas_factura':
                raise UserError(_(json_response['problemas_message']))
            # Receive and stroe XML invoice
            if json_response.get('factura_xml'):
                xml_file_link = invoice.company_id.factura_dir + '/' + invoice.number.replace('/', '_') + '.xml'
                xml_file = open(xml_file_link, 'w')
                xml_invoice = base64.b64decode(json_response['factura_xml'])
                xml_file.write(xml_invoice.decode("utf-8"))
                xml_file.close()
                invoice._set_data_from_xml(xml_invoice)
            invoice.write({'estado_factura': estado_factura,
                           'xml_invoice_link': xml_file_link,
                           'factura_cfdi': True})
            invoice.message_post(body="CFDI emitido")
        return True
    
    def veybuscalineas(self):
        num = 0
        invoice_lines = []
        tax_grouped = {}
        valorimpuestos = 0
        t_amount_wo_tax = 0
        for line in self.invoice_line_ids:
            num += 1
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            amounts = line.tax_ids.compute_all(price, line.currency_id, line.quantity, product=line.product_id, partner=line.move_id.partner_id)
            amount_wo_tax = line.price_unit * line.quantity
            this_amount = price * line.quantity
            print(amounts)
            taxes = amounts['taxes']
            tax_item ={}
            tax_items =[]
            rete_items = []
            valorimpuesto = 0
            incluido = False
            for tax in taxes:
                tax_id = self.env['account.tax'].browse(tax['id'])
                if tax_id.price_include or tax_id.amount_type == 'division':
                    amount_wo_tax -= tax['amount']
                if tax_id.tipo_impuesto:
                    tax_item={'codigo_impuesto': int(tax_id.tipo_impuesto),
                    'porcentaje_impuesto': "{:.2f}".format(tax_id.amount),
                    'valor_base_impuesto': "{:.2f}".format(this_amount),
                    'incluido': tax['price_include'],
                    'valor_impuesto':  "{:.2f}".format(tax['amount'])}
                    valorimpuesto += tax['amount']
                    incluido = tax['price_include']
                    tax_items.append(tax_item)
                    val = {'move_id': line.move_id.id,
                    'name': tax_id.name, #tax_group_id.
                    'tax_id': tax['id'],
                    'codigo': int(tax_id.tipo_impuesto),
                    'porcentaje': "{:.2f}".format(tax_id.amount),
                    'base': this_amount,
                    'amount': tax['amount']}
                    key = tax['id']
                    if key not in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += this_amount
            valorimpuestos += valorimpuesto 
            t_amount_wo_tax += this_amount
            invoice_lines.append({'numero_linea':num,
                                'codigo':line.product_id.default_code,
                                'cantidad': line.quantity,
                                'valor_unitario': "{:.2f}".format(amounts['total_excluded']),
                                'price': "{:.2f}".format(price),
                                'incluido': incluido,
                                'descuento':line.discount,
                                'descripcion': line.name[:1000],
                                'taxes': tax_items,
                                'rete_items':rete_items,
                                'periodo_fecha':line.periodo_fecha,
                                'periodo_codigo':line.periodo_codigo})
        for rete in self.line_ids:
            if rete.tax_line_id.rte_iva or rete.tax_line_id.rte_fuente or rete.tax_line_id.rte_ica:
                rete_items.append({'rte_fuente': tax_id.rte_fuente,'rte_iva': tax_id.rte_iva,'rte_ica': tax_id.rte_ica,
                'porcentaje': "{:.2f}".format(tax_id.amount*-1),
                'valor_base': t_amount_wo_tax,
                'valor_retenido':  "{:.2f}".format(tax['amount']*-1)})
        return invoice_lines,valorimpuestos,tax_grouped,rete_items

    def to_json(self):
        totalDays =100
        numero =1
        send = {}
        valores = self.env['base_electronicos.tabla'].search([('name', '=', 'Factura electrónica')])
        response2={}
        valores_lineas = valores.mp_id
        print("haber")
        print(self.journal_id)
        documento = valores.general_factura.search([('diario', '=', self.journal_id.id)])
        print(documento)
        if documento:
            send = {'tipo_documento':self.tipo_documento}
        else:
            return self.env['wk.wizard.message'].genrated_message("El diario no esta configurado en la tabla de envio "," Error en la configuracion","https://navegasoft.com") ,True
        for linea in valores_lineas:
            #buscar en el comprobante el codigo
            print(linea.name)
            try:
                #search de company_id in the field
                if linea.campo_tecnico:
                    if ("self.partner_id.state_id.code" == linea.campo_tecnico) | ("self.company_id.partner_id.state_id.code" == linea.campo_tecnico):
                        if self.partner_id.state_id.code:
                            send[linea.name] = eval(linea.campo_tecnico)
                        else:
                            return self.env['wk.wizard.message'].genrated_message("El campo tecnico esta en blanco "+linea.campo_tecnico," Error en el campo"+linea.name,"https://navegasoft.com") ,True
                    elif linea.name.strip() == "fecha":
                        print("imprimiendo fecha")
                        fecha =str(self.date.strftime("%Y-%m-%d"))
                        print(fecha)
                        send[linea.name] =fecha
                    elif linea.campo_tecnico.strip() == "lineas_producto":
                        send[linea.name],send["valorimpuestos"],send["tax_grouped"],send['rete_items'] =self.veybuscalineas()
                    elif linea.campo_tecnico.strip() == "totales":
                        send["valorsinimpuestos"] =self.amount_untaxed
                    elif linea.campo_tecnico.strip() == "valor_impuestos":
                        pass #send[linea.name] =self.veybuscaimpuestos()
                    elif linea.campo_tecnico.strip() == "retenciones":
                        pass #send[linea.name] =self.veybuscaretenciones()
                    else:
                        try:
                            safe_eval(linea.campo_tecnico, {'self': self}) #mode='exec',nocopy=True,
                        except Exception as e:
                            return self.env['wk.wizard.message'].genrated_message("El campo tecnico NO EXISTE "+linea.campo_tecnico," Error en el campo"+linea.name,"https://navegasoft.com") ,True
                        
                        if eval(linea.campo_tecnico):
                            send[linea.name] = eval(linea.campo_tecnico)
                        else:
                            if linea.obligatorio:
                                print("no tiene campo tecnico")
                                return self.env['wk.wizard.message'].genrated_message("El campo tecnico esta en blanco "+linea.campo_tecnico," Error en el campo"+linea.name,"https://navegasoft.com") ,True
                # else:
                #     print("no congigurado")
                #     return self.env['wk.wizard.message'].genrated_message("El campo no esta configurado"+linea.campo_tecnico,"Error en el campo"+linea.name,"https://navegasoft.com")    
            except SyntaxError:
                return self.env['wk.wizard.message'].genrated_message("El campo tecnico no existe "+linea.campo_tecnico,"Error en el campo"+linea.name,"https://navegasoft.com"),True
        if "id_plataforma" not in send:
            send['id_plataforma'] =self.company_id.partner_id.id_plataforma
        return send,False
        # print('send')
        # print(send)
                    #pass
                # if linea.name == "DepartamentoEstado":
                #     print(linea.name)
                #     print(linea.campo_tecnico)
                #     print(eval(linea.campo_tecnico))
            # else:
            #     send[linea.name] = None
        # print(send)
        #send['credit_note']= self.credit_note

    def pedircufe(self,send,urlini):
        headers = {'content-type': 'application/json'}
        print("PIDENDO CUFE 99999999999999999")
        # print(send)
        resultado = requests.post(urlini,headers=headers,data = json.dumps(send, indent=4, sort_keys=True, default=str))
        print(resultado.text)

        if resultado.status_code == 200:
            resultado2 = json.loads(resultado.text)
            print(resultado2["result"])
            if "result" in resultado2:
                final_text = json.loads(json.dumps(resultado2))
                result = final_text["result"]
                print("final_error")
                print(final_text)
                print("result")
                print(result)
                return result
        #         if "error_d" in final:
        #             if "transactionID" in final:
        #                 print("final")
        #                 print(resultado)
        #                 final_text = json.loads(json.dumps(final))#eval()
        #                 self.write({"impreso":False,"transaccionID":final_text['transactionID'],"estado_factura":"Generada_correctamente"})
        #             return self.env['wk.wizard.message'].genrated_message(final_text['mensaje'],final_text['titulo'] ,final_text['link'])
        #         else:
        #             final_text = json.loads(json.dumps(final))#.encode().decode("utf-8") eval(
        #             #final_text = final_error['error']
        #             return self.env['wk.wizard.message'].genrated_message("2 "+final_text['error'], final_text['titulo'],final_text['link'])
        #         # else:
        #         #     return self.env['wk.wizard.message'].genrated_message('3 No hemos recibido una respuesta satisfactoria vuelve a enviarlo', 'Reenviar')    
        #     else:
        #         if "error" in resultado:
        #             final = resultado["error"]
        #             final_error = json.loads(json.dumps(final))
        #             data = final_error["data"]
        #             data_final = data['message']
        #             return self.env['wk.wizard.message'].genrated_message("1 "+data_final,"Los datos no estan correctos" ,"https://navegasoft.com")
        # else:
        #     raise Warning(result)

    #@api.multi
    def envio_directo(self):
        import time
        for invoice in self:
            if self.estado_factura == 'factura_correcta':
                raise UserError(_('Error para timbrar factura, Factura ya generada.'))
            if self.estado_factura == 'factura_cancelada':
                raise UserError(_('Error para timbrar factura, Factura ya generada y cancelada.'))
            self.fecha_factura= datetime.now()
            now2 = datetime.now()
            # current_time = now2.strftime("%H:%M:%S")
            # self.FechaGen = str(now2.date())
            # self.HoraGen = str(current_time)
            urlini = "https://odoo15.navegasoft.com/admonclientes/objects/"
            if not self.factura.cufe and self.tipo_documento == "Nota Credito":
                if not self.factura:
                    raise UserError("Recuerda que debes asociar una factura y un tipo.")
                else:
                    long_total = len(self.factura.name)
                    prefijo = self.factura.journal_id.code
                    lon_prefix = len(self.factura.journal_id.code)#sequence_id.prefix 
                    #prefi = self.factura.journal_id.code # sequence_id.prefix  self.number[0:long_total-len(number)]
                    folio = self.factura.name[lon_prefix:long_total] 
                    send = {"id_plataforma":self.company_id.partner_id.id_plataforma,"password":self.company_id.partner_id.password,"prefijo":prefijo,"folio":folio,"tipo_documento":"cufe","documento_electronico":"factura"}
                    cufe = self.pedircufe(send,urlini)
                    print(cufe)
                    self.factura.write({"cufe":cufe['cufe']})
                    # return
                    #self.write({"cufe":})
            send,error = invoice.to_json()
            if error:
                return send
            else: 
                headers = {'content-type': 'application/json'}
                print(send)
                result = requests.post(urlini,headers=headers,data = json.dumps(send, indent=4, sort_keys=True, default=str))
                if result.status_code == 200:
                    resultado = json.loads(result.text)
                    print("final_error")
                    print(resultado)
                    if "result" in resultado:
                        final = resultado["result"]
                        if "error_d" in final:
                            if "transactionID" in final:
                                print("final")
                                print(resultado)
                                final_text = json.loads(json.dumps(final))#eval()
                                self.write({"impreso":False,"transaccionID":final_text['transactionID'],"estado_factura":"Generada_correctamente"})
                            return self.env['wk.wizard.message'].genrated_message(final_text['mensaje'],final_text['titulo'] ,final_text['link'])
                        else:
                            final_text = json.loads(json.dumps(final))#.encode().decode("utf-8") eval(
                            #final_text = final_error['error']
                            return self.env['wk.wizard.message'].genrated_message("2 "+final_text['error'], final_text['titulo'],final_text['link'])
                        # else:
                        #     return self.env['wk.wizard.message'].genrated_message('3 No hemos recibido una respuesta satisfactoria vuelve a enviarlo', 'Reenviar')    
                    else:
                        if "error" in resultado:
                            final = resultado["error"]
                            final_error = json.loads(json.dumps(final))
                            data = final_error["data"]
                            data_final = data['message']
                            return self.env['wk.wizard.message'].genrated_message("1 "+data_final,"Los datos no estan correctos" ,"https://navegasoft.com")
                else:
                    raise Warning(result)
                    return self.env['wk.wizard.message'].genrated_message('Existen problemas de coneccion debes reportarlo con navegasoft', 'Servidor')


    def imprimir(self):
        for invoice in self:
            name = invoice.name
            extension = ".pdf"
            name_ext = name+extension
            import re
            long_total = len(name)
            print(name)
            #lista = re.findall("\d+", self.number)
            #number = lista[0]
            if self.move_type == 'out_refund':
                lon_prefix = len(self.journal_id.code_refund)#refund_secure_sequence_id.prefix 
                prefi = self.journal_id.code_refund #self.number[0:long_total-len(number)]
            else:
                lon_prefix = len(self.journal_id.secure_sequence_id.prefix) 
                prefi = self.journal_id.secure_sequence_id.prefix #self.number[0:long_total-len(number)]
            number = name[lon_prefix:long_total]
        
        urlini = "https://odoo15.navegasoft.com/admonclientes/status/"
        headers = {'content-type': 'application/json'}
        send = {"id_plataforma":self.company_id.partner_id.id_plataforma,'password': self.company_id.partner_id.password,
        "transaccionID":self.transaccionID,"prefix":prefi,
        "number":number,'documento_electronico':"factura",'tipo_documento':self.tipo_documento}#"ambiente":self.ambiente,
        result = requests.post(urlini,headers=headers,data = json.dumps(send))
        #resultado = json.loads(result.text)
        #print(result.text)
        if result.status_code == 200:
            resultado = json.loads(result.text)
            if "documentBase64" in resultado:
                final = resultado["documentBase64"]
                return self.env['wk.wizard.message'].genrated_message('Documento impreso', 'listos')
            else:
                if "error" in resultado:
                    final = resultado["error"]
                    final_error = json.loads(json.dumps(final))
                    data = final_error["data"]
                    data_final = data['message']
                    final_data = json.loads(json.dumps(data_final))
                    # archivo = final_data['code']
                    return self.env['wk.wizard.message'].genrated_message(data_final,"Los datos no estan correctos" ,"https://navegasoft.com")
                else:
                    final = json.loads(json.dumps(resultado))
                    final2 = final['result']
                    final_data = json.loads(json.dumps(final2)) #eval(final2)
                    #archivo = final_data['code']
                    # module_path = modules.get_module_path('electronicos_factura')        
                    # model = "facturas"
                    # if '\\' in module_path:
                    #     src_path = '\\static\\'
                    #     src_model_path = "{0}{1}\\".format('\\static', model)
                    # else:
                    #     src_path = '/static/'
                    #     src_model_path = "{0}{1}/".format('/static/', model)
                    
                    # # if "model" folder does not exists create it
                    # os.chdir("{0}{1}".format(module_path, src_path))
                    # if not os.path.exists(model):
                    #     os.makedirs(model)
                    # extension = ".pdf"
                    # #file_path = "{0}{1}".format(module_path + src_model_path + str(name), extension)
                    # file_path = "{0}{1}".format(module_path + src_model_path + str(self.name), extension)
                    # if not (os.path.exists(file_path)):
                    #     size =1
                    #     if size == 0:
                    #         os.remove(file_path)
                    #         raise UserError(_('imprimible se esta preparando intenta de nuevo, Factura preparandose.'))
                    #     else:
                    import base64 
                    print(final_data)
                    if final_data['code'] == '400':
                        return self.env['wk.wizard.message'].genrated_message('Estamos recibiendo un codigo 400 Es necesario esperar para volver imprimir el documento', 'Es necesario esperar para volver a imprimir el documento')
                    elif final_data['code'] == '200':
                        print("el codigo")
                        print(final_data['code'])
                        image_64_encode = base64.b64decode(final_data['documentBase64']) #eval(
                        i64 = base64.b64encode(image_64_encode)
                        print("self.name+extension")
                        print(self.name+extension)
                        att_id = self.env['ir.attachment'].create({
                            'name': self.name+extension,
                            'type': 'binary',
                            'datas': i64,
                            #'datas_fname': self.name+extension,
                            'res_model': 'account.move',
                            'res_id': self.id,
                            })
                        if att_id:
                            self.write({"impreso":True})
                            return self.env['wk.wizard.message'].genrated_message("Ve a attachment","Factura impresa" ,"https://navegasoft.com")
                    elif final_data['code'] == '201':
                        print("el codigo")
                        print(final_data['code'])
                        image_64_encode = base64.b64decode(final_data['documentBase64']) #eval(
                        i64 = base64.b64encode(image_64_encode)
                        print("self.name+extension")
                        print(self.name+extension)
                        att_id = self.env['ir.attachment'].create({
                            'name': self.name+extension,
                            'type': 'binary',
                            'datas': i64,
                            #'datas_fname': self.name+extension,
                            'res_model': 'account.move',
                            'res_id': self.id,
                            })
                        if att_id:
                            self.write({"impreso":True})
                            return self.env['wk.wizard.message'].genrated_message("Ve a attachment","Factura impresa" ,"https://navegasoft.com")
                    else:
                        return self.env['wk.wizard.message'].genrated_message('Estamos recibiendo un codigo de error Es necesario esperar para volver imprimir el documento', 'Es necesario esperar para volver a imprimir el documento')
                                
                    # else:
                    #     raise UserError(_('Ve a attachment, Factura ya impresa.'))
 
                    final = resultado["error"]
                    final_error = json.loads(json.dumps(final))
                    data = final_error["data"]
                    data_final = data['message']      
        else:
            raise Warning(result)


class calidades(models.Model):
    _name = 'account.calidadess'
    
    codigo = fields.Char("Codigo")
    responsabilidad = fields.Char("Responsabilidad")
    descripcion = fields.Text("Descripcion")


class aduaneros(models.Model):
    _name = 'account.aduaneros'
    
    codigo = fields.Char("Codigo")
    responsabilidad = fields.Char("Responsabilidad")
    descripcion = fields.Char("Descripcion")

class taxdemedida(models.Model):
    #_name = 'account.tax'
    _inherit = 'account.tax'

    tipo_impuesto = fields.Selection(
        selection=[('1', 'IVA'), 
                   ('2', 'Impuesto al consumo'),
                   ('3', 'ICA'),
                   ('4', 'Impuesto nacional al consumo'),],
        string=_('Tipo de Impuesto'),
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    periodo_fecha = fields.Date("Fecha periodo", required=True, default=fields.Date.context_today)
    periodo_codigo = fields.Selection(selection=[('1', 'Por operación'),('2', 'Acumulado Semanal'),],string=_('Periodo'), required=True,default='1')



# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line.periodo'

#     periodo_fecha = fields.Date("Fecha periodo", required=True, default=fields.Date.context_today)
#     periodo_codigo = fields.Selection(selection=[('operacion', 'Por operación'),('acumulado', 'Acumulado Semanal'),],string=_('Periodo'), required=True,default='operacion')


class Accountrefund(models.TransientModel):
    _inherit = 'account.move.reversal'
  
    nota_credito = fields.Selection(
        selection=[('1', '1 Devolución de parte de los bienes; no aceptación de partes del servicio'), 
                   ('2', '2 Anulación de factura electrónica'), 
                   ('3', '3 Rebaja total aplicada'),
                   ('4', '4 Descuento total aplicado'), 
                   ('5', '5 Rescisión: nulidad por falta de requisitos'), 
                   ('6', '6 Otros'), ],
        string=_('Tipo de Nota credito'),
    )

    
    def _prepare_default_reversal(self, move):
        reverse_date = self.date if self.date_mode == 'custom' else move.date
        return {
            'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=move.name, reason=self.reason) 
                   if self.reason
                   else _('Reversal of: %s', move.name),
            'date': reverse_date,
            'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
            'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
            'invoice_payment_term_id': None,
            'invoice_user_id': move.invoice_user_id.id,
            'auto_post': True if reverse_date > fields.Date.context_today(self) else False,
            'nota_credito':self.nota_credito,
            'factura':move.id,
            'estado_factura':'no_generada',
        }


    # VERSION 15
    # def _prepare_default_reversal(self, move):
    #     reverse_date = self.date if self.date_mode == 'custom' else move.date
    #     return {
    #         'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=move.name, reason=self.reason) 
    #                if self.reason
    #                else _('Reversal of: %s', move.name),
    #         'date': reverse_date,
    #         'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
    #         'journal_id': self.journal_id.id,
    #         'invoice_payment_term_id': None,
    #         'invoice_user_id': move.invoice_user_id.id,
    #         'auto_post': True if reverse_date > fields.Date.context_today(self) else False,
    #         'nota_credito':self.nota_credito,
    #         'factura':move.id,
    #         'estado_factura':'no_generada',
    #     }

