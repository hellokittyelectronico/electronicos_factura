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
    _inherit = 'account.invoice'
    #_inherit = 'account.move' 

    codigo_qr = fields.Char('codigo_qr')                       
    cufe = fields.Char('cufe')               
    rechazo = fields.Char('rechazo')                       
    grafica_link = fields.Char('pdf')
    factura_electronica = fields.Boolean('Factura Electronica')
    nota_debito = fields.Selection(
        selection=[('30', '30 Nota Débito que referencia una factura electrónica.'), 
                   ('32', '32 Nota Débito sin referencia a facturas'),],
        string=_('Tipo de Nota debito'),
    )
    show_comment = fields.Char("Mostrar comentario")
    nota_credito = fields.Selection(
        selection=[('1', '1 Devolución de parte de los bienes; no aceptación de partes del servicio'), 
                   ('2', '2 Anulación de factura electrónica'), 
                   ('3', '3 Rebaja total aplicada'),
                   ('4', '4 Descuento total aplicado'), 
                   ('5', '5 Rescisión: nulidad por falta de requisitos'), 
                   ('6', '6 Otros'), ],
        string=_('Tipo de Nota credito'),
    )
    factura = fields.Many2one('account.invoice')#domain="[('estado_factura', 'in', ('factura_correcta','a'))]",relation='partner_delivery_partner_rel',column1="id", column2="id2"
    tipoc_o_d = fields.Char('tipo')
    tipo_comprobante = fields.Selection(
        selection=[('I', 'Ingreso'), 
                   ('E', 'Egreso'),
                    ('T', 'Traslado'),],
        string=_('Tipo de comprobante'),
    )
    #forma_pago = fields.Selection(  
    tipo_pago = fields.Selection(    
        selection=[('1', '1 - Instrumento no definido'), 
                   ('2', '2 - Crédito ACH'), 
                   ('3', '3 - Débito ACH'),
                   ('4', '4 - Reversión débito de demanda ACH'), 
                   ('5', '5 - Reversión crédito de demanda ACH'),
                   ('6', '6 - Crédito de demanda ACH'), 
                   ('7', '7 - Débito de demanda ACH'), 
                   ('8', '8 - Mantener'), 
                   ('9', '9 - Clearing Nacional o Regional'), 
                   ('10', '10 - Efectivo'), 
                   ('11', '11 - Reversión Crédito Ahorro'), 
                   ('12', '12 - Reversión Débito Ahorro'), 
                   ('13', '13 - Crédito Ahorro'), 
                   ('14', '14 - Débito Ahorro'), 
                   ('15', '15 - Bookentry Crédito'), 
                   ('16', '16 - Bookentry Débito'), 
                   ('17', '17 - Concentración de la demanda en efectivo /Desembolso Crédito (CCD)'), 
                   ('18', '18 - Concentración de la demanda en efectivo / Desembolso (CCD) débito'),
                   ('19', '19 - Crédito Pago negocio corporativo (CTP)'), 
                   ('20', '20 - Cheque'), 
                   ('21', '21 - Poyecto bancario'), 
                   ('22', '22 - Proyecto bancario certificado'), 
                   ('23', '23 - Cheque bancario'), 
                   ('24', '24 - Nota cambiaria esperando aceptación'), 
                   ('25', '25 - Cheque certificado'), 
                   ('26', '26 - Cheque Local'), 
                   ('27', '27 - Débito Pago Neogcio Corporativo (CTP)'), 
                   ('28', '28 - Crédito Negocio Intercambio Corporativo (CTX)'), 
                   ('29', '29 - Débito Negocio Intercambio Corporativo (CTX)'), 
                   ('30', '30 - Transferecia Crédito'), 
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
                   ('10', _('10- Estandar')),
                   ('11', _('11- Mandato')),],
        string=_('Tipo de factura'),
        default ='10'
    )
    xml_invoice_link = fields.Char(string=_('XML Invoice Link'))
    estado_factura = fields.Selection(
        selection=[('factura_no_generada', 'Factura no generada'), ('factura_correcta', 'Factura correcta'), 
                   ('problemas_factura', 'Problemas con la factura'), ('solicitud_cancelar', 'Cancelación en proceso'),
                   ('cancelar_rechazo', 'Cancelación rechazada'), ('factura_cancelada', 'Factura cancelada'), ],
        string=_('Estado de factura'),
        default='factura_no_generada'
    )#,readonly=True
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
    fecha_name = fields.Date("Fecha orden") #,default=datetime.today()
    agregar_sura = fields.Boolean("Agregar línea de negocio SURA")
    fecha_y_hora = fields.Datetime("Fecha orden")
    num_ocr = fields.Char(string=_('Numero'))
    negocios_sura = fields.Selection(
        selection=[('LR-FINANCIACION_POLIZAS', 'LR-FINANCIACION_POLIZAS'), 
                   ('LR-ACCIDENTES_PERSONALES', 'LR-ACCIDENTES_PERSONALES'), 
                   ('LR-INTERMEDIACION', 'LR-INTERMEDIACION'),
                   ('LR-CUENTAS_MEDICAS_NO_PBS', 'LR-CUENTAS_MEDICAS_NO_PBS'),
                   ('LR-CUENTAS_MEDICAS_PBS', 'LR-CUENTAS_MEDICAS_PBS'), 
                   ('LR-CUENTAS_MEDICAS', 'LR-CUENTAS_MEDICAS'), 
                   ('LR-JUVENIL', 'LR-JUVENIL'),
                   ('LR-PREPAGADA', 'LR-PREPAGADA'),
                   ('LR-PREVENCION', 'LR-PREVENCION'), 
                   ('LR-RECLAMACIONES GENERALES', 'LR-RECLAMACIONES GENERALES'), 
                   ('LR-CUENTAS_MEDICAS_SALUD', 'LR-CUENTAS_MEDICAS_SALUD'),
                   ('LR-SOAT', 'LR-SOAT'),],
        string=_('Nombre'),
    )
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
        ('Nota_credito', 'Nota_credito'),
        ('Documento_soporte', 'Documento_soporte'),
        ('Nota_credito_Documento_soporte', 'Nota_credito_Documento_soporte'),
    ], string='Tipo documento')

    #@api.one
    @api.depends('journal_id')
    def documento(self):
        valores = self.env['base_electronicos.tabla'].search([('name', '=', 'Factura electrónica')])
        response2={}
        valores_lineas = valores.mp_id
        print("haber")
        # print(self.journal_id[0])
        for docu in self: 
            documento = valores.general_factura.search([('diario', '=', docu.journal_id[0].id)])
            print(documento)
            if documento:
                docu.tipo_documento = documento.tipo_factura
            
        # datos_generales = self.env['electronicos_factura.datos_generales'].search([('diario', '=', self.journal_id[0].id)])
        # if datos_generales: 
        #     self.tipo_documento = "soporte"
        # if datos_generales: 
        #     self.tipo_documento = "factura"
    #@api.multi
    

    
    @api.multi
    def generate_cfdi_invoice2(self):
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
        rete_grouped = {}
        valorimpuestos = 0
        t_amount_wo_tax = 0
        for line in self.invoice_line_ids:
            num += 1
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            amounts = line.invoice_line_tax_ids.compute_all(price, line.currency_id, line.quantity, product=line.product_id, partner=line.partner_id)
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
                    val = {'move_id': line.id,
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
                # for rete in self.line_ids:
                if tax_id.rte_iva or tax_id.rte_fuente or tax_id.rte_ica:
                    key = tax['id']
                    val2 = {'rte_fuente': tax_id.rte_fuente,
                    'rte_iva': tax_id.rte_iva,
                    'rte_ica': tax_id.rte_ica,
                    'name': tax_id.name, #tax_group_id.
                    'tax_id': tax['id'],
                    'porcentaje': "{:.4f}".format(tax_id.amount*-1) if tipo_documento == "factura" else "{:.2f}".format(tax_id.amount*-1),
                    'valor_base': this_amount,
                    'amount': tax['amount'],
                    'valor_retenido': tax['amount']*-1,}
                    if key not in rete_grouped:
                        rete_grouped[key] = val2
                    else:
                        rete_grouped[key]['valor_base'] += this_amount
                        rete_grouped[key]['valor_retenido'] += tax['amount']*-1
                    rete_items.append({'rte_fuente': tax_id.rte_fuente,'rte_iva': tax_id.rte_iva,'rte_ica': tax_id.rte_ica,
                    'porcentaje': "{:.4f}".format(tax_id.amount*-1),
                    'valor_base': this_amount,
                    'valor_retenido':  "{:.2f}".format(tax['amount']*-1)})
            valorimpuestos += valorimpuesto 
            # t_amount_wo_tax += this_amount

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
        
        return invoice_lines,valorimpuestos,tax_grouped,rete_grouped

    def to_json2(self):
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
            send = {'tipo_documento':documento.tipo_factura}
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
                        fecha =self.date #str(self.date.strftime("%Y-%m-%d"))
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

    #@api.multi
    def envio_directo2(self):
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
            print("to json")
            send,error = invoice.to_json2()
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
                                self.write({"impreso":False,"transaccionID":final_text['transactionID'],"estado_factura":"factura_correcta"})
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


    def imprimir2(self):
        for invoice in self:
            name = invoice.number
            extension = ".pdf"
            name_ext = name+extension
            import re
            long_total = len(name)
            print(name)
            #lista = re.findall("\d+", self.number)
            #number = lista[0]
            if self.type == 'out_refund':
                lon_prefix = len(self.journal_id.refund_secure_sequence_id.prefix) 
                prefi = self.journal_id.refund_sequence_id.prefix #self.number[0:long_total-len(number)]
            else:
                lon_prefix = len(self.journal_id.sequence_id.prefix) 
                prefi = self.journal_id.sequence_id.prefix #self.number[0:long_total-len(number)]
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
                    module_path = modules.get_module_path('tabla_nomina')        
                    model = "facturas"
                    if '\\' in module_path:
                        src_path = '\\static\\'
                        src_model_path = "{0}{1}\\".format('\\static', model)
                    else:
                        src_path = '/static/'
                        src_model_path = "{0}{1}/".format('/static/', model)
                    
                    # if "model" folder does not exists create it
                    os.chdir("{0}{1}".format(module_path, src_path))
                    if not os.path.exists(model):
                        os.makedirs(model)
                    extension = ".pdf"
                    #file_path = "{0}{1}".format(module_path + src_model_path + str(name), extension)
                    file_path = "{0}{1}".format(module_path + src_model_path + str(self.number), extension)
                    if not (os.path.exists(file_path)):
                        size =1
                        if size == 0:
                            os.remove(file_path)
                            raise UserError(_('imprimible se esta preparando intenta de nuevo, Factura preparandose.'))
                        else:
                            import base64 
                            print(final_data)
                            if final_data['code'] == '400':
                                return self.env['wk.wizard.message'].genrated_message('Estamos recibiendo un codigo 400 Es necesario esperar para volver imprimir el documento', 'Es necesario esperar para volver a imprimir el documento')
                            elif final_data['code'] == '201':
                                print("el codigo")
                                print(final_data['code'])
                                image_64_encode = base64.b64decode(final_data['documentBase64']) #eval(
                                i64 = base64.b64encode(image_64_encode)
                                print("self.name+extension")
                                print(self.number+extension)
                                att_id = self.env['ir.attachment'].create({
                                'name': name+extension,
                                'type': 'binary',
                                'datas': i64,
                                'datas_fname': name+extension,
                                'res_model': 'account.invoice',
                                'res_id': self.id,
                                'mimetype': 'application/xml'
                                })
                                # att_id = self.env['ir.attachment'].create({
                                #     'name': self.name+extension,
                                #     'type': 'binary',
                                #     'datas': i64,
                                #     #'datas_fname': self.name+extension,
                                #     'res_model': 'account.invoice',
                                #     'res_id': self.id,
                                #     })
                                if att_id:
                                    self.write({"impreso":True})
                                    return self.env['wk.wizard.message'].genrated_message("Ve a attachment","Factura impresa" ,"https://navegasoft.com")
                            else:
                                return self.env['wk.wizard.message'].genrated_message('Estamos recibiendo un codigo de error Es necesario esperar para volver imprimir el documento', 'Es necesario esperar para volver a imprimir el documento')
                                
                    else:
                        raise UserError(_('Ve a attachment, Factura ya impresa.'))
 
                    final = resultado["error"]
                    final_error = json.loads(json.dumps(final))
                    data = final_error["data"]
                    data_final = data['message']      
        else:
            raise Warning(result)

