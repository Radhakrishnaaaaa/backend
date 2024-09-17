import json
from datetime import datetime,timedelta
import base64
from db_connection import db_connection_manage
import sys
import os
from bson import ObjectId


conct = db_connection_manage()

class Invoice():
    def cmsPOClientList(request_body):
        try:
            data = request_body #test1
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            clients = list(db_con.Clients.find({}))
            req_line = "Dear Sir/Ma'am, Here is the Tax Invoice, please find the details below"
            client_details = [
                {
                    "client_id": item["all_attributes"]["client_id"],
                    "client_name": item["all_attributes"]["client_name"],
                    # "types_of_boms": list(item["all_attributes"]["boms"].keys())
                    "types_of_boms": item["all_attributes"]["types_of_boms"],
                    "client_location": item["all_attributes"]["client_location"],
                    "contact_number": item["all_attributes"]["contact_number"],
                    "req_line": req_line
                }
                for item in clients
            ]
            return {'statusCode': 200, 'body': client_details}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
        
    def cmsGetClientDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            client_id = data.get("client_id")
            match_stage = {
                "$match": {
                    "gsipk_table": "Clients",
                    "pk_id": client_id
                }
            }
            pipeline = [
                match_stage
            ]
            clients = list(db_con.Clients.aggregate(pipeline))
            lst = sorted([
                {
                    'client_id': item.get('pk_id', ""),
                    "ship_to": {
                        "company_name": item["all_attributes"].get('client_name', ""),
                        "gst_number": item["all_attributes"].get('gst_number', ""),
                        "pan_number": item["all_attributes"].get('pan_number', ""),
                        "contact_number": item["all_attributes"].get('contact_number', ""),
                        "address": item["all_attributes"].get('client_location', "")
                    },
                    "kind_Attn": {
                        "company_name": item["all_attributes"].get('client_name', ""),
                        "gst_number": item["all_attributes"].get('gst_number', ""),
                        "pan_number": item["all_attributes"].get('pan_number', ""),
                        "contact_number": item["all_attributes"].get('contact_number', ""),
                        "address": item["all_attributes"].get('client_location', "")
                    },
                    "req_line": """Dear Sir/Ma'am, Here is the Tax Invoice, please find the details below"""
                }
                for item in clients
            ], key=lambda x: int(x['client_id'].replace("PTGCLI", "")), reverse=False)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst[0]}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request check data once'}
        
    def cmsInvoiceSearch(request_body):
        try:
            data = request_body #test
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            boms = list(db_con.BOM.find({}))
            cmpt = list(db_con.Inventory.find({}))
            res = []
            for i in boms:
                bom_name = [
                    i["all_attributes"]["bom_id"],
                    i["all_attributes"]["bom_name"]
                ]
                res.append(bom_name)
            for i in cmpt:
                mfr_part = [
                    i["all_attributes"]["cmpt_id"],
                    i["all_attributes"]["ctgr_name"],
                    i["all_attributes"].get("mfr") or i["all_attributes"].get("manufacturer"),
                    i["all_attributes"]["mfr_prt_num"],
                    i["all_attributes"]["description"]
                ]
                res.append(mfr_part)
            return {'statusCode': 200, 'body': res}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
    # def cmsInvoiceCreate(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
   
    #         pk_ids = list(db_con.NewPurchaseOrder.find({'pk_id': {'$regex': '^I'}}, {'pk_id': 1}))
    #         if len(pk_ids) == 0:
    #             pk_id = "IOPTG1"
    #             max_pk = 1
    #         else:
    #             pk_filter = [int(x['pk_id'][5:]) for x in pk_ids]
    #             max_pk = max(pk_filter) + 1
    #             pk_id = "IOPTG" + str(max_pk)
           
    #         sk_timeStamp = datetime.now().isoformat()
           
    #         primary_doc_details = data.get("primary_document_details", {})
    #         kind_attn = data.get("kind_attn", {})
    #         ship_to = data.get("buyer", {})
    #         secondary_doc_details = data.get("secondary_doc_details", {})
    #         purchase_list = data.get("purchase_list", {})
    #         total_amount = data.get("total_amount", {})

    #         invoice_date=data['primary_document_details'].get("invoice_date",0)
           
    #         po_month = invoice_date.month
    #         po_year = invoice_date.year
    #         po_next=po_year+1
    #         po_id = f"EPL/INV/{max_pk}/{po_month}/{po_year}-{po_next}
           
    #         insertion_list = {
    #             'pk_id': pk_id,
    #             'sk_timeStamp': sk_timeStamp,
    #             'all_attributes': {
    #                 'ship_to': ship_to,
    #                 'kind_attn': kind_attn,
    #                 'primary_doc_details': primary_doc_details,
    #                 'purchase_list': purchase_list,
    #                 'total_amount': total_amount,
    #                 'secondary_doc_details': secondary_doc_details,
    #                 'po_id': po_id,
    #                 'client_id': "CFPO1"
    #             },
    #             'gsisk_id': "open",
    #             'gsipk_table': "PurchaseOrder",
    #             'lsi_key': "Invoice"
    #         }
           
    #         insertion = db_con.NewPurchaseOrder.insert_one(insertion_list)
           
    #         db_con.all_tables.update_one({'pk_id':'top_ids'},{'$set':{'all_attributes.Invoice':pk_id}})
    #         return {'statusCode': 200, 'body': "Invoice created successfully"}    
       
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         return {'statusCode': 400, 'body': f'Bad Request(check data): {err} (file: {f_name}, line: {line_no})'}

    def cmsInvoiceCreate(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            client_id = data['client_id']
            pk_ids = list(db_con.NewPurchaseOrder.find({'pk_id': {'$regex': '^I'}}, {'pk_id': 1}))
            if len(pk_ids) == 0: 
                pk_id = "IOPTG1"
                max_pk = 1
            else:
                pk_filter = [int(x['pk_id'][5:]) for x in pk_ids]
                max_pk = max(pk_filter) + 1
                pk_id = "IOPTG" + str(max_pk)
            sk_timeStamp = datetime.now().isoformat()
            primary_document_details = data.get("primary_document_details", {})
            kind_attn = data.get("kind_attn", {})
            ship_to = data.get("ship_to", {})
            secondary_doc_details = data.get("secondary_doc_details", {})
            purchase_list = data.get("purchase_list", {})
            total_amount = data.get("total_amount", {})
            invoice_date_str = primary_document_details.get("invoice_date", "")
            if invoice_date_str:
                try:
                    invoice_date = datetime.strptime(invoice_date_str, "%Y-%m-%d")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid invoice_date format'}
            else:
                return {'statusCode': 400, 'body': 'invoice_date is required'}
            po_month = invoice_date.month
            po_year = invoice_date.strftime("%y")  
            po_next = (invoice_date.year + 1) % 100  
            inv_id = f"EPL/INV/{max_pk}/{po_month}/{po_year}-{po_next:02d}"
            insertion_list = {
                'pk_id': pk_id,
                'sk_timeStamp': sk_timeStamp,
                'all_attributes': {
                    'ship_to': ship_to,
                    'kind_attn': kind_attn,
                    'primary_document_details': primary_document_details,
                    'purchase_list': purchase_list,
                    'total_amount': total_amount,
                    'secondary_doc_details': secondary_doc_details, 
                    'inv_id': inv_id,
                    'client_id': client_id
                },
                'gsisk_id': "open",
                'gsipk_table': "Invoice",
                'lsi_key': "Pending"
            }
            insertion = db_con.NewPurchaseOrder.insert_one(insertion_list)
            db_con.all_tables.update_one({'pk_id': 'top_ids'}, {'$set': {'all_attributes.Invoice': pk_id}})
            return {'statusCode': 200, 'body': "Invoice created successfully"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Bad Request(check data): {err} (file: {f_name}, line: {line_no})'}
        
    def cmsInvoiceSearchAdd(request_body):
        try:
            data = request_body #test
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            id = data['search']
            if id.startswith('C'):
                cmpt = list(db_con.Inventory.find({"all_attributes.cmpt_id": id}))
                result = {
                    'cmpt_id': cmpt[0]["all_attributes"]["cmpt_id"],
                    # 'mfr_prt_num': cmpt[0]["all_attributes"].get("mfr") or cmpt[0]["all_attributes"].get("manufacturer")
                    'mfr_prt_num': cmpt[0]["all_attributes"].get("mfr_prt_num")
                }
                return {'statusCode': 200, 'body': result}
            else:
                bom = list(db_con.BOM.find({'all_attributes.bom_id': id}))
                result = {
                    "bom_id": bom[0]["all_attributes"]["bom_id"],
                    "bom_name": bom[0]["all_attributes"]["bom_name"]
                }
                return {'statusCode': 200, 'body': result}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Bad Request(check data): {err} (file: {f_name}, line: {line_no})'}

    # def cmsGetEditInvoice(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         pk_id = data['inv_id']
    #         result = list(db_con.NewPurchaseOrder.find({'all_attributes.inv_id':pk_id, "gsipk_table":"Invoice"}))
    #         if result:
    #             invoice_data = result[0]["all_attributes"]
    #             purchase_list = []
    #             if "purchase_list" in invoice_data:
    #                 parts = invoice_data.pop("purchase_list")
    #                 for part_key in parts:
    #                     if part_key.startswith("part"):
    #                         purchase_list.append(parts[part_key])
    #             invoice_data["purchase_list"] = purchase_list
    #             return {'statusCode': 200, 'body': invoice_data}
    #         # else:
    #         #     return {'statusCode': 404, 'body': 'Invoice not found'}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         return {'statusCode': 400, 'body': f'Bad Request(check data): {err} (file: {f_name}, line: {line_no})'}
    def cmsGetEditInvoice(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            pk_id = data['inv_id']
            id = pk_id.split('/')[1]
            if id.startswith('D'):
                result = list(db_con.DraftInvoice.find({'all_attributes.inv_id': pk_id, "gsipk_table": "Draft_Invoice"}))
                if result:
                    invoice_data = result[0]["all_attributes"]
                    purchase_list = []
                    if "purchase_list" in invoice_data:
                        parts = invoice_data.pop("purchase_list")
                        for part_key in parts:
                            if part_key.startswith("part"):
                                purchase_list.append(parts[part_key])
                    invoice_data["purchase_list"] = purchase_list
                    return {'statusCode': 200, 'body': invoice_data}
            else:
                result = list(db_con.NewPurchaseOrder.find({'all_attributes.inv_id': pk_id, "gsipk_table": "Invoice"}))
                if result:
                    invoice_data = result[0]["all_attributes"]
                    purchase_list = []
                    if "purchase_list" in invoice_data:
                        parts = invoice_data.pop("purchase_list")
                        for part_key in parts:
                            if part_key.startswith("part"):
                                purchase_list.append(parts[part_key])
                    invoice_data["purchase_list"] = purchase_list
                    return {'statusCode': 200, 'body': invoice_data}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Bad Request(check data): {err} (file: {f_name}, line: {line_no})'}
        
    def cmsInvoiceEdit(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            updatestatus = data["updatestatus"]
            sk_timeStamp = (datetime.now()).isoformat()
            inv_id = data['inv_id']
            client_id = data['client_id']
            res = db_con.NewPurchaseOrder.find_one({"all_attributes.inv_id": inv_id, "lsi_key": updatestatus})
            if not res:
                return {'statusCode': 404, 'body': 'Invoice not found'}
            new_status = "Pending" if updatestatus == "Rejected" else updatestatus
            update_fields = {
                "ship_to": data.get("ship_to", res["all_attributes"].get("ship_to", {})),
                "kind_attn": data.get("kind_attn", res["all_attributes"].get("kind_attn", {})),
                "primary_document_details": data.get("primary_document_details",
                                                     res["all_attributes"].get("primary_document_details", {})),
                "purchase_list": data.get("purchase_list", res["all_attributes"].get("purchase_list", {})),
                "total_amount": data.get("total_amount", res["all_attributes"].get("total_amount", {})),
                "secondary_doc_details": data.get("secondary_doc_details", res["all_attributes"].get("secondary_doc_details", {})),
                "inv_id": inv_id,
                "client_id": client_id
            }
            db_con.NewPurchaseOrder.update_one(
                {"all_attributes.inv_id": inv_id},
                {"$set": {
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": update_fields,
                    "lsi_key": new_status
                }}
            )
            return {'statusCode': 200, 'body': 'Invoice updated successfully'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Invoice update failed'}
    def cmsInvoiceSaveDraft(request_body):
        # try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            client_id = data['client_id']
            pk_ids = list(db_con.DraftInvoice.find({'pk_id': {'$regex': '^D'}}, {'pk_id': 1}))
            if len(pk_ids) == 0: 
                pk_id = "DIOPTG1"
                max_pk = 1
            else:
                pk_filter = [int(x['pk_id'][6:]) for x in pk_ids]
                max_pk = max(pk_filter) + 1
                pk_id = "DIOPTG" + str(max_pk)
            sk_timeStamp = datetime.now().isoformat()
            primary_document_details = data.get("primary_document_details", {})
            kind_attn = data.get("kind_attn", {})
            ship_to = data.get("ship_to", {})
            secondary_doc_details = data.get("secondary_doc_details", {})
            purchase_list = data.get("purchase_list", {})
            total_amount = data.get("total_amount", {})
            invoice_date_str = primary_document_details.get("invoice_date", "")
            if invoice_date_str:
                try:
                    invoice_date = datetime.strptime(invoice_date_str, "%Y-%m-%d")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Dratf Invalid invoice_date format'}
            else:
                return {'statusCode': 400, 'body': 'draft invoice_date is required'}
            po_month = invoice_date.month
            po_year = invoice_date.strftime("%y")  
            po_next = (invoice_date.year + 1) % 100  
            inv_id = f"EPL/DINV/{max_pk}/{po_month}/{po_year}-{po_next:02d}"
            insertion_list = {
                'pk_id': pk_id,
                'sk_timeStamp': sk_timeStamp,
                'all_attributes': {
                    'ship_to': ship_to,
                    'kind_attn': kind_attn,
                    'primary_document_details': primary_document_details,
                    'purchase_list': purchase_list,
                    'total_amount': total_amount,
                    'secondary_doc_details': secondary_doc_details, 
                    'inv_id': inv_id,
                    'client_id': client_id
                },
                'gsisk_id': "open",
                'gsipk_table': "Draft_Invoice",
                'lsi_key': "Pending"
            }
            insertion = db_con.DraftInvoice.insert_one(insertion_list)
            db_con.all_tables.update_one({'pk_id': 'top_ids'}, {'$set': {'all_attributes.DraftInvoice': pk_id}})
            return {'statusCode': 200, 'body': "Draft Invoice created successfully"}
        # except Exception as err:
        #     exc_type, exc_obj, tb = sys.exc_info()
        #     f_name = tb.tb_frame.f_code.co_filename
        #     line_no = tb.tb_lineno
        #     return {'statusCode': 400, 'body': f'Bad Request(check data): {err} (file: {f_name}, line: {line_no})'}
        
    def cmsInvoiceUpdateDraft(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            pk_ids = list(db_con.NewPurchaseOrder.find({'pk_id': {'$regex': '^I'}}, {'pk_id': 1}))
            if len(pk_ids) == 0: 
                pk_id = "IOPTG1"
                max_pk = 1
            else:
                pk_filter = [int(x['pk_id'][5:]) for x in pk_ids]
                max_pk = max(pk_filter) + 1
                pk_id = "IOPTG" + str(max_pk)
            sk_timeStamp = datetime.now().isoformat()
            primary_document_details = data.get("primary_document_details", {})
            kind_attn = data.get("kind_attn", {})
            ship_to = data.get("ship_to", {})
            secondary_doc_details = data.get("secondary_doc_details", {})
            purchase_list = data.get("purchase_list", {})
            total_amount = data.get("total_amount", {})
            invoice_date_str = primary_document_details.get("invoice_date", "")
            if invoice_date_str:
                try:
                    invoice_date = datetime.strptime(invoice_date_str, "%Y-%m-%d")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid invoice_date format'}
            else:
                return {'statusCode': 400, 'body': 'invoice_date is required'}
            po_month = invoice_date.month
            po_year = invoice_date.strftime("%y")  
            po_next = (invoice_date.year + 1) % 100  
            inv_id = f"EPL/INV/{max_pk}/{po_month}/{po_year}-{po_next:02d}"
            item = {
                'pk_id': pk_id,
                'sk_timeStamp': sk_timeStamp,
                'all_attributes': {
                    'ship_to': ship_to,
                    'kind_attn': kind_attn,
                    'primary_document_details': primary_document_details,
                    'purchase_list': purchase_list,
                    'total_amount': total_amount,
                    'secondary_doc_details': secondary_doc_details, 
                    'inv_id': inv_id,
                    'client_id': data['client_id']
                },
                'gsisk_id': "open",
                'gsipk_table': "Invoice",
                'lsi_key': "Pending"
            }
            db_con.DraftInvoice.delete_one({'all_attributes.inv_id': data['inv_id']})
            resp = db_con.NewPurchaseOrder.insert_one(item)
            db_con.all_tables.update_one({'pk_id': 'top_ids'}, {'$set': {'all_attributes.Invoice': pk_id}})
            return {'statusCode':200, 'body': 'Invoice draft update and saved'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Invoice draft update failed'}