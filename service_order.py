
import json
from datetime import datetime, timedelta,date
import base64
from db_connection import db_connection_manage
import sys
import os
from dateutil.relativedelta import relativedelta
from bson import ObjectId
from cms_utils import file_uploads

conct = db_connection_manage()


def file_get(path):
    if path:
        return path
    else:
        return ""

class ServiceOrder():
    
    def CmsNewServiceOrderCreate(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            
            primary_doc_details = data.get("primary_document_details", {})
            so_date = primary_doc_details.get("so_date", "")
            
            # Extract month and year from SO_Date
            if so_date:
                try:

                    so_date_obj = datetime.strptime(so_date, "%Y-%m-%d")
                    po_month = so_date_obj.strftime("%m")
                    po_year = so_date_obj.strftime("%y")
                    next_month_obj = so_date_obj + relativedelta(months=1)
                    next_month = next_month_obj.strftime("%m")
                    next_year = next_month_obj.strftime("%y")

                    next_year = str(int(po_year) + 1).zfill(2)
                    so_month_year = f"{po_month}/{po_year}-{next_year}"

                    # so_date_obj = datetime.strptime(so_date, "%Y-%m-%d")
                    # so_month_year = so_date_obj.strftime("%m-%y")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid SO_Date format'}
            else:
                return {'statusCode': 400, 'body': 'SO_Date is required'}
            
            service_orders = list(db_con.NewPurchaseOrder.find({}))
            service_order_id = "1"
            client_so_num = f"EPL/SO/1/{so_month_year}"

            if service_orders:
                # update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                print(update_id)
                if "ServiceOrder" in update_id[0]['all_attributes']:
                    update_id = (update_id[0]['all_attributes']['ServiceOrder'][5:])
                    print(update_id)
                else:
                    update_id = "1"
                service_order_id = str(int(update_id) + 1)
                print(service_order_id)
            last_client_so_nums = [i["all_attributes"]["so_id"] for i in service_orders if "so_id" in i["all_attributes"]]
            if last_client_so_nums:
                client_so_num = f"EPL/SO/{service_order_id}/{so_month_year}"

            service_order_data = {
                "pk_id": "SOPTG" + service_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": {
                    "ship_to": data.get("ship_to", {}),
                    "req_line": data.get("req_line", ""),
                    "so_terms_conditions": data.get("so_terms_conditions", ""),
                    "kind_attn": data.get("kind_attn", {}),
                    "primary_document_details": primary_doc_details,
                    "job_work_table": data.get("job_work_table", {}),
                    "total_amount": data.get("total_amount", {}),
                    "secondary_doc_details": data.get("secondary_doc_details", {}),
                    "so_id": client_so_num,
                    "partner_id": data.get("partner_id", ""),
                },
                "gsisk_id": "open",
                "gsipk_table": "ServiceOrder",
                "lsi_key": "Pending"
                
            }

            db_con.NewPurchaseOrder.insert_one(service_order_data)
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}        
            update_data = {
                '$set': {
                    'all_attributes.ServiceOrder': "SOPTG" + service_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': 'New SO created successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'SO creation failed'}



    
    def CmsPurchaseOrderGetPartnersDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            partner_id = data.get("partner_id")

            match_stage = {
                "$match": {
                    "gsipk_table": "Partners",
                    "pk_id": partner_id
                }
            }
            # Execute aggregation pipeline
            pipeline = [
                match_stage
            ]
            vendors = list(db_con.Partners.aggregate(pipeline))
            # print(vendors)
            lst = sorted([
                {
                    'partner_id': item.get('pk_id', ""),
                    'partner_type': item.get('gsipk_id',""),
                    "ship_to": {
                        "company_name": "People Tech IT Consultancy Pvt Ltd",
                        "gst_number": "36AAGCP2263H2ZE",
                        "pan_number": " AAGCP2263H",
                        "contact_details": "Sudheendra Soma",
                        "contact_number": "9885900909",
                        "address": "Plot No.14 & 15, RMZ Futura Building, Block B, Hitech City, Hyderabad,Telangana, India- 500081"
                    },
                    "kind_Attn": {
                        "company_name":item["all_attributes"].get('partner_name', ""),
                        "gst_number": item["all_attributes"].get('gst_number', ""),
                        "pan_number": item["all_attributes"].get('pan_number', ""),
                        "contact_number": item["all_attributes"].get('contact_number', ""),
                        "address": item["all_attributes"].get('address1', "")
                    },
                    "req_line": """Dear Sir/Ma'am,
                                Please Supply the Items mentioned in Order subject to delivery, mode and other terms and conditions below and overleaf. Please confirm the acceptance of this order. If you expect any delay in supply,communicate the same immediately on receipt of this purchase order."""
                }
                for item in vendors
            ], key=lambda x: int(x['partner_id'].replace("PTGPAR", "")), reverse=False)
            # # #print(lst)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst[0]}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'vendor deletion failed'}
        


    
    # def CmsGetPartnerNameList(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']

    #         # Find partners and project partner_id and partner_name fields
    #         result = list(db_con.Partners.find({}, {"_id": 0, "all_attributes.partner_id": 1, "all_attributes.partner_name": 1}))

    #         # Extract partner_id and partner_name into the desired structure
    #         partner_list = [{"partnerId": partner['all_attributes']['partner_id'], "partnerName": partner['all_attributes']['partner_name']} for partner in result]

    #         conct.close_connection(client)

    #         # Convert list of partners to a dictionary
    #         partner_dict = {f"partner{index + 1}": partner for index, partner in enumerate(partner_list)}

    #         return {'statusCode': 200, 'body': partner_dict}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Failed to fetch partner names'}


    def CmsGetPartnerNameList(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            # Find partners and project partner_id and partner_name fields
            result = list(db_con.Partners.find({}, {"_id": 0, "all_attributes.partner_id": 1, "all_attributes.partner_name": 1}))

            # Extract partner_id and partner_name into the desired structure
            partner_list = [{"partnerId": partner['all_attributes']['partner_id'], "partnerName": partner['all_attributes']['partner_name']} for partner in result]

            conct.close_connection(client)
            return {'statusCode': 200, 'body': partner_list}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Failed to fetch partner names'}
        


    
    # def CmsUpdateServiceOrder(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         so_id = data['so_id']
            
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = (datetime.now()).isoformat()

    #         # Find the existing service order based on so_id
    #         existing_so = db_con.PurchaseOrder.find_one({"all_attributes.so_id": so_id})
    #         if not existing_so:
    #             return {'statusCode': 404, 'body': 'Service Order not found'}
            
    #         # Prepare update fields
    #         update_fields = {
    #             "ship_to": data.get("ship_to", existing_so["all_attributes"].get("ship_to", {})),
    #             "req_line": data.get("req_line", existing_so["all_attributes"].get("req_line", "")),
    #             "so_terms_conditions": data.get("so_terms_conditions", existing_so["all_attributes"].get("so_terms_conditions", "")),
    #             "kind_attn": data.get("kind_attn", existing_so["all_attributes"].get("kind_attn", {})),
    #             "primary_document_details": data.get("primary_document_details", existing_so["all_attributes"].get("primary_document_details", {})),
    #             "job_work_table": data.get("job_work_table", existing_so["all_attributes"].get("job_work_table", {})),
    #             "total_amount": data.get("total_amount", existing_so["all_attributes"].get("total_amount", {})),
    #             "secondary_doc_details": data.get("secondary_doc_details", existing_so["all_attributes"].get("secondary_doc_details", {})),
    #             "partner_id": data.get("partner_id", existing_so["all_attributes"].get("partner_id", "")),
    #             "so_id": so_id 
    #         }

    #         # Update the service order in the database
    #         db_con.PurchaseOrder.update_one(
    #             {"all_attributes.so_id": so_id},
    #             {"$set": {
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": update_fields
    #             }}
    #         )

    #         conct.close_connection(client)
    #         return {'statusCode': 200, 'body': 'Service Order updated successfully'}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Service Order update failed'}

    def CmsUpdateServiceOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            so_id = data['so_id']
            updatestatus = data["updatestatus"]
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()

            # Find the existing service order based on so_id
            existing_so = db_con.NewPurchaseOrder.find_one({"all_attributes.so_id": so_id, "lsi_key": updatestatus})
            if not existing_so:
                return {'statusCode': 404, 'body': 'Service Order not found'}
            
            new_status = "Pending" if updatestatus == "Rejected" else updatestatus
            
            # Prepare update fields
            update_fields = {
                "ship_to": data.get("ship_to", existing_so["all_attributes"].get("ship_to", {})),
                "req_line": data.get("req_line", existing_so["all_attributes"].get("req_line", "")),
                "so_terms_conditions": data.get("so_terms_conditions", existing_so["all_attributes"].get("so_terms_conditions", "")),
                "kind_attn": data.get("kind_attn", existing_so["all_attributes"].get("kind_attn", {})),
                "primary_document_details": data.get("primary_document_details", existing_so["all_attributes"].get("primary_document_details", {})),
                "job_work_table": data.get("job_work_table", existing_so["all_attributes"].get("job_work_table", {})),
                "total_amount": data.get("total_amount", existing_so["all_attributes"].get("total_amount", {})),
                "secondary_doc_details": data.get("secondary_doc_details", existing_so["all_attributes"].get("secondary_doc_details", {})),
                "partner_id": data.get("partner_id", existing_so["all_attributes"].get("partner_id", "")),
                "so_id": so_id 
            }

            # Update the service order in the databased
            db_con.NewPurchaseOrder.update_one(
                {"all_attributes.so_id": so_id},
                {"$set": {
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": update_fields,
                    "lsi_key": new_status
                }}
            )

            conct.close_connection(client)
            return {'statusCode': 200, 'body': 'Service Order updated successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Service Order update failed'}
        

    # def CmsServiceOrderGet(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']       
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         so_id = data['so_id']
    #         document = db_con.NewPurchaseOrder.find_one({'all_attributes.so_id': so_id}, {'_id': 0})
    #         if not document:
    #             return {'statusCode': 404, 'body': 'No purchase order found for the given status and po_id'}
    #         all_attributes = document["all_attributes"]
    #         primary_document_details = all_attributes.get("primary_document_details", {})
                        
    #         job_work_table = all_attributes.get("job_work_table", {})
    #         if not job_work_table:
    #             return {'statusCode': 400, 'body': 'job work table is missing or invalid'}           
            
    #         extracted_data = {
                
    #             "ship_to": all_attributes.get("ship_to", {}),
    #             "req_line": all_attributes.get("req_line", ""),
    #             "kind_attn": all_attributes.get("kind_attn", {}), 
    #             "primary_document_details": primary_document_details,
    #             # "client_po": all_attributes.get("client_po", {}),
    #             "total_amount": all_attributes.get("total_amount", {}),
    #             "secondary_doc_details": all_attributes.get("secondary_doc_details", {}),
    #             "job_work_table": job_work_table,
    #             "so_terms_conditions": all_attributes.get("so_terms_conditions", ""),
    #             "so_id": all_attributes.get("so_id", ""),
    #             "partner_id": all_attributes.get("partner_id", "")
                
    #         }

    #         return {'statusCode': 200, 'body': extracted_data}
        

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Service Order get failed'}
    def CmsServiceOrderGet(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            so_id = data['so_id']
            id = so_id.split('/')[1]
            if id.startswith('D'):
                document = db_con.DraftServiceOrder.find_one({'all_attributes.so_id': so_id}, {'_id': 0})
                if not document:
                    return {'statusCode': 404, 'body': 'No service order found for the given so_id'}
                all_attributes = document["all_attributes"]
                # primary_document_details = all_attributes.get("primary_document_details", {})
                # job_work_table = all_attributes.get("job_work_table", {})
                # if not job_work_table:
                #     return {'statusCode': 400, 'body': 'job work table is missing or invalid'}
                extracted_data = {
                    "ship_to": all_attributes.get("ship_to", {}),
                    "req_line": all_attributes.get("req_line", ""),
                    "kind_attn": all_attributes.get("kind_attn", {}),
                    # "primary_document_details": primary_document_details,
                    "primary_document_details": all_attributes.get("primary_document_details", {}),
                    # "client_po": all_attributes.get("client_po", {}),
                    "total_amount": all_attributes.get("total_amount", {}),
                    "secondary_doc_details": all_attributes.get("secondary_doc_details", {}),
                    # "job_work_table": job_work_table,
                    "job_work_table": all_attributes.get("job_work_table", {}),
                    "so_terms_conditions": all_attributes.get("so_terms_conditions", ""),
                    "so_id": all_attributes.get("so_id", ""),
                    "partner_id": all_attributes.get("partner_id", "")
                }
                return {'statusCode': 200, 'body': extracted_data}
            else:
                document = db_con.NewPurchaseOrder.find_one({'all_attributes.so_id': so_id}, {'_id': 0})
                if not document:
                    return {'statusCode': 404, 'body': 'No purchase order found for the given status and po_id'}
                all_attributes = document["all_attributes"]
                # primary_document_details = all_attributes.get("primary_document_details", {})
                # job_work_table = all_attributes.get("job_work_table", {})
                # if not job_work_table:
                #     return {'statusCode': 400, 'body': 'job work table is missing or invalid'}
                extracted_data = {
                    "ship_to": all_attributes.get("ship_to", {}),
                    "req_line": all_attributes.get("req_line", ""),
                    "kind_attn": all_attributes.get("kind_attn", {}),
                    # "primary_document_details": primary_document_details,
                    "primary_document_details": all_attributes.get("primary_document_details", {}),
                    # "client_po": all_attributes.get("client_po", {}),
                    "total_amount": all_attributes.get("total_amount", {}),
                    "secondary_doc_details": all_attributes.get("secondary_doc_details", {}),
                    # "job_work_table": job_work_table,
                    "job_work_table": all_attributes.get("job_work_table", {}),
                    "so_terms_conditions": all_attributes.get("so_terms_conditions", ""),
                    "so_id": all_attributes.get("so_id", ""),
                    "partner_id": all_attributes.get("partner_id", "")
                }
                return {'statusCode': 200, 'body': extracted_data}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Service Order get failed'}
        
    def CmsDraftServiceOrderCreate(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            
            primary_doc_details = data.get("primary_document_details", {})
            so_date = primary_doc_details.get("so_date", "")
            
            # Extract month and year from SO_Date
            if so_date:
                try:

                    so_date_obj = datetime.strptime(so_date, "%Y-%m-%d")
                    po_month = so_date_obj.strftime("%m")
                    po_year = so_date_obj.strftime("%y")
                    next_month_obj = so_date_obj + relativedelta(months=1)
                    next_month = next_month_obj.strftime("%m")
                    next_year = next_month_obj.strftime("%y")

                    next_year = str(int(po_year) + 1).zfill(2)
                    so_month_year = f"{po_month}/{po_year}-{next_year}"

                    # so_date_obj = datetime.strptime(so_date, "%Y-%m-%d")
                    # so_month_year = so_date_obj.strftime("%m-%y")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid Draft_SO_Date format'}
            else:
                return {'statusCode': 400, 'body': 'Draft_SO_Date is required'}
            
            service_orders = list(db_con.DraftServiceOrder.find({}))
            service_order_id = "1"
            client_so_num = f"EPL/DSO/1/{so_month_year}"

            if service_orders:
                # update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                print(update_id)
                if "DraftServiceOrder" in update_id[0]['all_attributes']:
                    update_id = (update_id[0]['all_attributes']['DraftServiceOrder'][6:])
                    print(update_id)
                else:
                    update_id = "1"
                service_order_id = str(int(update_id) + 1)
                print(service_order_id)
            last_client_so_nums = [i["all_attributes"]["dso_id"] for i in service_orders if "dso_id" in i["all_attributes"]]
            if last_client_so_nums:
                client_so_num = f"EPL/DSO/{service_order_id}/{so_month_year}"

            service_order_data = {
                "pk_id": "DSOPTG" + service_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": {
                    "ship_to": data.get("ship_to", {}),
                    "req_line": data.get("req_line", ""),
                    "so_terms_conditions": data.get("so_terms_conditions", ""),
                    "kind_attn": data.get("kind_attn", {}),
                    "primary_document_details": primary_doc_details,
                    "job_work_table": data.get("job_work_table", {}),
                    "total_amount": data.get("total_amount", {}),
                    "secondary_doc_details": data.get("secondary_doc_details", {}),
                    # "so_id": client_so_num,
                    "so_id": f"EPL/DSO/{service_order_id}/{so_month_year}",
                    "partner_id": data.get("partner_id", ""),
                },
                "gsisk_id": "open",
                "gsipk_table": "DraftServiceOrder",
                "lsi_key": "Pending"
                
            }

            db_con.DraftServiceOrder.insert_one(service_order_data)
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}        
            update_data = {
                '$set': {
                    'all_attributes.DraftServiceOrder': "DSOPTG" + service_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': 'New Draft_SO created successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'SO creation failed'}

    def cmsServiceUpdateDraft(request_data):
        try:
            data = request_data
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            pk_ids = list(db_con.NewPurchaseOrder.find({'pk_id': {'$regex': '^S'}}, {'pk_id': 1}))
            if len(pk_ids) == 0: 
                pk_id = "SOPTG1"
                max_pk = 1
            else:
                pk_filter = [int(x['pk_id'][5:]) for x in pk_ids]
                max_pk = max(pk_filter) + 1
                pk_id = "SOPTG" + str(max_pk)
            sk_timeStamp = (datetime.now()).isoformat()
            primary_document_details = data.get("primary_document_details", {})
            kind_attn = data.get("kind_attn", {})
            ship_to = data.get("ship_to", {})
            secondary_doc_details = data.get("secondary_doc_details", {})
            job_work_table = data.get("job_work_table", {})
            total_amount = data.get("total_amount", {})
            so_date = primary_document_details.get("so_date", "")
            if so_date:
                try:
                    so_date = datetime.strptime(so_date, "%Y-%m-%d")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid invoice_date format'}
            else:
                return {'statusCode': 400, 'body': 'invoice_date is required'}
            so_month = so_date.month
            so_year = so_date.strftime("%y")  
            so_next = (so_date.year + 1) % 100  
            so_id = f"EPL/SO/{max_pk}/{so_month}/{so_year}-{so_next:02d}"
            item = {
                'pk_id': pk_id,
                'sk_timeStamp': sk_timeStamp,
                'all_attributes': {
                    'ship_to': ship_to,
                    'req_line': data.get('req_line', ''),
                    'so_terms_conditions': data.get('so_terms_conditions', ''),
                    'kind_attn': kind_attn,
                    'primary_document_details': primary_document_details,
                    'job_work_table': job_work_table,
                    'total_amount': total_amount,
                    'secondary_doc_details': secondary_doc_details, 
                    'so_id': so_id,
                    'partner_id': data['partner_id']
                },
                'gsisk_id': "open",
                'gsipk_table': "ServiceOrder",
                'lsi_key': "Pending"
            }
            db_con.DraftServiceOrder.delete_one({'all_attributes.so_id': data['so_id']})
            resp = db_con.NewPurchaseOrder.insert_one(item)
            db_con.all_tables.update_one({'pk_id': 'top_ids'}, {'$set': {'all_attributes.ServiceOrder': pk_id}})
            return {'statusCode': 200, 'body':'Service draft updated successfully'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Service draft update failed'}

    def purchaseOrderCancel(request_body):
            try:
                data = request_body
                env_type = data['env_type']
                pk_id = data['pos_id']
                db_conct = conct.get_conn(env_type)
                db_con = db_conct['db']
                client = db_conct['client']

                id = pk_id.split('/')[1]
                print('pkid', id, pk_id)
                if id == 'SO':
                    db_con.NewPurchaseOrder.update_one(
                    {"all_attributes.so_id": pk_id},
                    {"$set": {
                        "lsi_key": 'Cancel',
                        "sk_timeStamp": (datetime.now()).isoformat()
                    }}
                )
                if id == 'PO':
                    db_con.NewPurchaseOrder.update_one(
                    {"all_attributes.po_id": pk_id},
                    {"$set": {
                        "lsi_key": 'Cancel'
                    }}
                )
                if id == 'INV':
                    db_con.NewPurchaseOrder.update_one(
                    {"all_attributes.inv_id": pk_id},
                    {"$set": {
                        "lsi_key": 'Cancel',
                        "sk_timeStamp": (datetime.now()).isoformat()
                    }}
                )
                if id == 'PI':
                    db_con.ProformaInvoice.update_one(
                    {"all_attributes.pi_id": pk_id},
                    {"$set": {
                        "lsi_key": 'Cancel',
                        "sk_timeStamp": (datetime.now()).isoformat()
                    }}
                )
                if id == 'CFPO':
                    db_con.ForcastPurchaseOrder.update_one(
                    {"all_attributes.Client_Purchaseorder_num": pk_id},
                    {"$set": {
                        "lsi_key": 'Cancel',
                        "sk_timeStamp": (datetime.now()).isoformat()
                    }}
                )
                if id == 'FCPO':
                    db_con.ForcastPurchaseOrder.update_one(
                    {"all_attributes.Client_Purchaseorder_num": pk_id},
                    {"$set": {
                        "lsi_key": 'Cancel',
                        "sk_timeStamp": (datetime.now()).isoformat()
                    }}
                )
                conct.close_connection(client)
                return {'statusCode': 200, 'body': 'Order Cancelled successfully'}

            except Exception as err:
                exc_type, exc_obj, tb = sys.exc_info()
                f_name = tb.tb_frame.f_code.co_filename
                line_no = tb.tb_lineno
                print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
                return {'statusCode': 400, 'body': 'Order Cancellation failed'}
            
    def getAllCancelledOrders(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            cancelled_orders_Array = []
            all_attributes_array = []
            result = list(db_con.NewPurchaseOrder.find({},{'_id': 0})) + list(db_con.ProformaInvoice.find({},{'_id': 0})) + list(db_con.ForcastPurchaseOrder.find({},{'_id': 0}))
            for data in result:
                if data["lsi_key"] == 'Cancel':
                    cancelled_orders_Array.append(data)
            for cancelled_orders in cancelled_orders_Array:
                all_attributes_array.append(cancelled_orders['all_attributes'])
            conct.close_connection(client)
            return {'statusCode': 200, 'body': all_attributes_array}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Order Cancellation failed'}

