# import json


import json
from datetime import datetime, timedelta,date
import base64
from db_connection import db_connection_manage
import sys
from dateutil.relativedelta import relativedelta
import os
from bson import ObjectId
from cms_utils import file_uploads

conct = db_connection_manage()


def file_get(path):
    if path:
        return path
    else:
        return ""

class PurchaseOrder():
    
    def CmsNewPurchaseOrderCreate(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            
            primary_doc_details = data.get("primary_document_details", {})
            po_date = primary_doc_details.get("po_date", "")
            
            # Extract month and year from PO_Datedew
            if po_date:
                try:
                    po_date_obj = datetime.strptime(po_date, "%Y-%m-%d")
                    po_month = po_date_obj.strftime("%m")
                    po_year = po_date_obj.strftime("%y")
                    next_month_obj = po_date_obj + relativedelta(months=1)
                    next_month = next_month_obj.strftime("%m")
                    next_year = next_month_obj.strftime("%y")

                    next_year = str(int(po_year) + 1).zfill(2)
                    po_month_year = f"{po_month}/{po_year}-{next_year}"

                    # po_date_obj = datetime.strptime(po_date, "%Y-%m-%d")
                    # po_month_year = po_date_obj.strftime("%m-%y")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid PO_Date format'}
            else:
                return {'statusCode': 400, 'body': 'PO_Date is required'}
            
            purchase_order = list(db_con.NewPurchaseOrder.find({}))
            bom_id = data.get('bom_id', '')
            purchase_order_id = "1"
            client_po_num = f"EPL/PO/1/{po_month_year}"

            # client_po_num = ""
            purchase_order_id = '1'
            if purchase_order:
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                print(update_id)
                # if "NewPurchaseOrder" in update_id[0]['all_attributes']:
                if "PurchaseOrder" in update_id[0]['all_attributes']:
                    update_id = (update_id[0]['all_attributes']['PurchaseOrder'][4:])
                #     update_id = (update_id[0]['all_attributes']['NewPurchaseOrder'][4:])
                    print(update_id)
                else:
                    update_id = "1"
                purchase_order_id = str(int(update_id) + 1)
                print(purchase_order_id)

            # if purchase_order:
            #     purchase_order_ids = [i["pk_id"] for i in purchase_order]
            #     purchase_order_ids = sorted(purchase_order_ids, key=lambda x: int(x[4:]), reverse=True)
            #     numeric_part = int(purchase_order_ids[0].split("G")[1]) + 1
            #     purchase_order_id = str(numeric_part)
                last_client_po_nums = [i["all_attributes"]["po_id"] for i in purchase_order if "po_id" in i["all_attributes"]]
                if last_client_po_nums:
                    # last_client_po_nums = sorted(last_client_po_nums, key=lambda x: int(x.split("/")[2]), reverse=True)
                    # last_increment = int(last_client_po_nums[0].split("/")[2]) + 1
                    client_po_num = f"EPL/PO/{purchase_order_id}/{po_month_year}"

            purchase_data = {
                "pk_id": "OPTG" + purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": {
                    "ship_to": data.get("ship_to", {}),
                    "req_line": data.get("req_line", ""),
                    "po_terms_conditions": data.get("po_terms_conditions", ""),
                    "kind_attn": data.get("kind_attn", {}),
                    "primary_document_details": primary_doc_details,
                    "purchase_list": data.get("purchase_list", {}),
                    "total_amount": data.get("total_amount", {}),
                    "secondary_doc_details": data.get("secondary_doc_details", {}),
                    "po_id": client_po_num,
                    "vendor_id":data.get("vendor_id", ""),
                },
                "gsisk_id": "open",
                "gsipk_table": "PurchaseOrder",
                "lsi_key": "Pending"
                
            }

            # db_con.PurchaseOrder.insert_one(purchase_data)
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}        
            db_con.NewPurchaseOrder.insert_one(purchase_data)
            update_data = {
                '$set': {
                    # 'all_attributes.NewPurchaseOrder': "OPTG" + purchase_order_id
                    'all_attributes.PurchaseOrder': "OPTG" + purchase_order_id
                }
            }
            db_con.all_tables.update_one(key,update_data)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': 'New PO created successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO creation failed'}
        



    
    def CmsNewCreatePurchaseOrderSaveDraft(request_body):
        try:
            data = request_body
            print(data)
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            
            primary_doc_details = data.get("primary_document_details", {})
            po_date = primary_doc_details.get("po_date", "")
            
            # Extract month and year from PO_Date
            if po_date:
                try:
                    po_date_obj = datetime.strptime(po_date, "%Y-%m-%d")
                    po_month = po_date_obj.strftime("%m")
                    po_year = po_date_obj.strftime("%y")
                    next_month_obj = po_date_obj + relativedelta(months=1)
                    next_month = next_month_obj.strftime("%m")
                    next_year = next_month_obj.strftime("%y")

                    next_year = str(int(po_year) + 1).zfill(2)
                    po_month_year = f"{po_month}/{po_year}-{next_year}"

                    # po_date_obj = datetime.strptime(po_date, "%Y-%m-%d")
                    # po_month_year = po_date_obj.strftime("%m-%y")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid PO_Date format'}
            else:
                return {'statusCode': 400, 'body': 'PO_Date is required'}
            
            purchase_order = list(db_con.DraftPurchaseOrder.find({}))
            bom_id = data.get('bom_id', '')
            purchase_order_id = "1"
            client_po_num = f"EPL/DPO/1/{po_month_year}"

            # client_po_num = ""
            purchase_order_id = '1'
            if purchase_order:
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                print(update_id)
                if "DraftPurchaseOrder" in update_id[0]['all_attributes']:
                    update_id = (update_id[0]['all_attributes']['DraftPurchaseOrder'][5:])
                    print(update_id)
                else:
                    update_id = "1"
                purchase_order_id = str(int(update_id) + 1)
                print(purchase_order_id)

            # if purchase_order:
            #     purchase_order_ids = [i["pk_id"] for i in purchase_order]
            #     purchase_order_ids = sorted(purchase_order_ids, key=lambda x: int(x[4:]), reverse=True)
            #     numeric_part = int(purchase_order_ids[0].split("G")[1]) + 1
            #     purchase_order_id = str(numeric_part)
                last_client_po_nums = [i["all_attributes"]["po_id"] for i in purchase_order if "po_id" in i["all_attributes"]]
                if last_client_po_nums:
                    # last_client_po_nums = sorted(last_client_po_nums, key=lambda x: int(x.split("/")[2]), reverse=True)
                    # last_increment = int(last_client_po_nums[0].split("/")[2]) + 1
                    client_po_num = f"EPL/DPO/{purchase_order_id}/{po_month_year}"
                    print(client_po_num)

            purchase_data = {
                "pk_id": "DOPTG" + purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": {
                    "ship_to": data.get("ship_to", {}),
                    "req_line": data.get("req_line", ""),
                    "po_terms_conditions": data.get("po_terms_conditions", ""),
                    "kind_attn": data.get("kind_attn", {}),
                    "primary_document_details": primary_doc_details,
                    "purchase_list": data.get("purchase_list", {}),
                    "total_amount": data.get("total_amount", {}),
                    "secondary_doc_details": data.get("secondary_doc_details", {}),
                    "po_id": client_po_num,
                    "vendor_id":data.get("vendor_id", ""),
                },
                "gsisk_id": "open",
                "gsipk_table": "DraftPurchaseOrder",
                "lsi_key": "Pending"
                
            }
            print(purchase_data["all_attributes"]["po_id"])

            # db_con.PurchaseOrder.insert_one(purchase_data)
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}        
            db_con.DraftPurchaseOrder.insert_one(purchase_data)
            update_data = {
                '$set': {
                    'all_attributes.DraftPurchaseOrder': "DOPTG" + purchase_order_id
                }
            }
            db_con.all_tables.update_one(key,update_data)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': 'Draft PO created successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO creation failed'}



    def CmsPurchaseOrderCreate(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            purchase_order = list(db_con.PurchaseOrder.find({}))
            bom_id= data.get('bom_id','')
            purchase_order_id = "1"

            # Update from here
            if purchase_order:
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                print(update_id)
                # if "NewPurchaseOrder" in update_id[0]['all_attributes']:
                if "PurchaseOrder" in update_id[0]['all_attributes']:
                    update_id = (update_id[0]['all_attributes']['PurchaseOrder'][4:])
                #     update_id = (update_id[0]['all_attributes']['NewPurchaseOrder'][4:])
                    print(update_id)
                else:
                    update_id = "1"
                purchase_order_id = str(int(update_id) + 1)
            # Till here

            # if purchase_order:
            #     # print(purchase_order)
            #     purchase_order_ids = [i[("pk_id")] for i in purchase_order]
            #     # print(purchase_order_ids)
            #     purchase_order_ids = sorted(purchase_order_ids, key=lambda x: int(x[4:]), reverse=True)
            #     # print(purchase_order_ids)
            #     numeric_part = int(purchase_order_ids[0].split("G")[1]) + 1
            #     # print(numeric_part)
            #     purchase_order_id = str(numeric_part)
            #     # print(purchase_order_id)
            documents = data['documents']
            doc = {}
            for inx, docs in enumerate(documents):
                image_path = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "",
                                                      "OPTG" + purchase_order_id, docs["doc_name"], docs['doc_body'])
                doc[docs["doc_name"]] = image_path
            data["documents"] = doc
            for key, value in data["parts"].items():
                if key.startswith("part"):
                    data["parts"][key]["received_qty"] = 0
                    data["parts"][key]["packaging"] = data["parts"][key].get("packaging", "")
                    data["parts"][key]["manufacturer"] = data["parts"][key].get("manufacturer", "-")
            if data.get('created_from', '') == 'Vendor':
                ordered_parts = [part['cmpt_id'] for key, part in data['parts'].items()]
                # Retrieve vendor document from MongoDB
                vendor_document = list(db_con.Vendor.find({"gsipk_table": "Vendor", "pk_id": data['vendor_id']}))
                print(vendor_document)
                if vendor_document and 'parts' in vendor_document[0]['all_attributes']:
                    vendor_parts = vendor_document[0]['all_attributes']['parts']
                    # Update status of ordered parts in vendor's parts list
                    for part_no, part_data in vendor_parts.items():
                        if part_data['cmpt_id'] in ordered_parts and part_data['bom_id']==bom_id:
                            vendor_parts[part_no]['status'] = True
                    # Update vendor document in MongoDB
                    db_con.Vendor.update_one(
                        {"gsipk_table": "Vendor", "pk_id": data['vendor_id']},
                        {"$set": {"all_attributes.parts": vendor_parts}}
                    )
                    # data["parts"]=vendor_parts
                    # response = {'statusCode': 200, 'body': 'Vendor parts updated successfully'}
            purchase_data = {
                "pk_id": "OPTG" + purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": data,
                "gsisk_id": data["status"],
                "gsipk_table": "PurchaseOrder",
                "lsi_key": data["vendor_id"]
            }

            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}
            db_con.PurchaseOrder.insert_one(purchase_data)
            update_data = {
                '$set': {
                    'all_attributes.PurchaseOrder': "OPTG" + purchase_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            # db_con.PurchaseOrder.insert_one(purchase_data)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': f'New PO created successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def CmsPurchaseOrderEdit(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id = data["order_id"]
            filter = {"pk_id": po_id}
            # Perform the query
            result = (db_con.PurchaseOrder.find_one(filter))
            documents = data['documents']
            # doc = {}
            # for inx, docs in enumerate(documents):
            #     if "/" not in docs["doc_body"]:
            #         image_path = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "",
            #                                               po_id, docs["doc_name"],
            #                                               docs['doc_body'])
            #         doc[docs["doc_name"]] = image_path
            #     else:
            #         img = docs['doc_body']
            #         image_type = docs["doc_name"]
            id = 1
            documents = data['documents']
            doc = {}
            for inx, docs in enumerate(documents):
                image_path = file_uploads.upload_file("EMS", "PtgCms" + env_type, "",
                                                    "E-Kit" + str(id), docs["doc_name"],
                                                    docs['doc_body'])
                doc[docs["doc_name"]] = image_path

            del data["documents"]
            for key, value in data.items():
                # #print(key,value)
                # Check if the key exists in the nested dictionary 'all_attributes'
                if key in result['all_attributes']:
                    # If the key exists and the value is a dictionary, update its contents
                    if isinstance(value, dict):
                        result['all_attributes'][key] = value
                        # for nested_key, nested_value in value.items():
                        #     # #print(nested_key)
                        #     result['all_attributes'][key][nested_key] = nested_value
                    else:
                        # If the key exists but the value is not a dictionary, update the value directly
                        result['all_attributes'][key] = value
            # result["all_attributes"]["documents"].update(doc)
            result['all_attributes']['documents'] = doc
            # print(result)
            # Update the database
            db_con.PurchaseOrder.update_one({"_id": result["_id"]}, {"$set": result})
            conct.close_connection(client)
            return {'statusCode': 200, 'body': f' PO Edited successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def CmsPurchaseOrderEditGet(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id = data["order_id"]
            filter = {"pk_id": po_id}
            result = list(db_con.PurchaseOrder.find(filter))
            if result:
                result = result[0]
                category = list(
                    db_con.Metadata.find({}, {"_id": 0, "pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1}))
                category = {
                    item['pk_id'].replace("MDID", "CTID"): (
                        {
                            "ctgr_name": item['gsisk_id'],
                            "sub_categories": {
                                key: value for key, value in item['sub_categories'].items()
                            }
                        }
                        if item['gsipk_id'] == 'Electronic'
                        else {"ctgr_name": item['gsisk_id']}
                    )
                    for item in category
                }
                inventory = list(db_con.Inventory.find({}, {"all_attributes": 1}))
                inventory = {item['all_attributes']['cmpt_id']: item['all_attributes'] for item in inventory}
                response = {
                    "vendor_id": result["all_attributes"]["vendor_id"],
                    "vendor_name": result["all_attributes"]["vendor_name"],
                    "order_id": result["pk_id"],
                    "order_date": result["sk_timeStamp"].split("T")[0],
                    "status": result["all_attributes"]["status"],
                    "terms_and_conditions": result["all_attributes"]["terms_and_conditions"],
                    "payment_terms": result["all_attributes"]["payment_terms"],
                    "shipping_address": result["all_attributes"]["shipping_address"],
                    "billing_address": result["all_attributes"]["billing_address"],
                    # "against_po": "NO PO for Bom",  # Assuming this field needs to be populated
                    "against_po": result['all_attributes']['against_po'],
                    "receiver": result["all_attributes"]["receiver"],
                    "receiver_contact": result["all_attributes"]["receiver_contact"],
                    "ordered_by": result["all_attributes"]["ordered_by"],
                    "ordered_by_contact": result["all_attributes"]["ordered_by_contact"],
                    "deo": result["all_attributes"].get("deo", "--"),  # You need to specify where this value comes from
                    "parts": [
                        {
                            "cmpt_id": part["cmpt_id"],
                            "ctgr_id": part["ctgr_id"],
                            "department": part["department"],
                            "manufacturer": inventory[part["cmpt_id"]].get("manufacturer", "-"),  # part["manufacturer"],
                            "mfr_prt_num": part["mfr_prt_num"],
                            "ctgr_name": inventory[part["cmpt_id"]]["ctgr_name"],
                            # "received_qty": part["received_qty"],
                            "received_qty": part.get("received_qty", 0),
                            "prdt_name": part["prdt_name"],  # file_uploads.parts_Qty(part["ctgr_id"],db_con),#,
                            "description": inventory[part["cmpt_id"]]["description"],
                            "packaging": part["packaging"],
                            "qty": part["qty"],
                            "price": part["price"],
                            "unit_price": part["unit_price"]
                        }
                        for part in result["all_attributes"]["parts"].values()
                    ],
                    "documents": [
                        {
                            "doc_name": doc_name,
                            "doc_body": file_get(doc_body)
                        }
                        for doc_name, doc_body in result["all_attributes"]["documents"].items()
                    ]
                }
                print(response)
                conct.close_connection(client)
                return {'statusCode': 200, 'body': response}
            else:
                return {'statusCode': 404, 'body': "No data found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def CmsPurchaseOrderGetVendor(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            search_status = data.get("status", "Active")
            # print(search_status)
            # Build the match stage of the aggregation pipeline
            match_stage = {
                "$match": {
                    "gsipk_table": "Vendor",
                    "lsi_key": search_status
                }
            }
            # Execute aggregation pipeline
            pipeline = [
                match_stage
            ]
            vendors = list(db_con.Vendor.aggregate(pipeline))
            # print(vendors)
            lst = sorted([
                {
                    'vendor_id': item.get('pk_id', ""),
                    'vendor_type': item["all_attributes"].get('vendor_type', ""),
                    'vendor_name': item["all_attributes"].get('vendor_name', "")
                }
                for item in vendors
            ], key=lambda x: int(x['vendor_id'].replace("PTGVEN", "")), reverse=False)
            # #print(lst)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'vendor deletion failed'}

    def cmsPurchaseOrderGetAllData(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            bom = list(db_con.BOM.find())
            bom_dict = {i["all_attributes"]["bom_id"]: i["all_attributes"]["bom_name"] for i in bom}

            # Build the match stage of the aggregation pipeline
            match_stage = {
                "$match": {
                    "gsipk_table": "PurchaseOrder"
                }
            }
            # Execute aggregation pipeline
            pipeline = [
                match_stage
            ]
            po_data = list(db_con.PurchaseOrder.aggregate(pipeline))

            lst = [
                {
                    "OrderNo": i['pk_id'],
                    "sk_timeStamp": i['sk_timeStamp'],
                    "bom_id": i["all_attributes"].get("bom_id", ""),
                    "bom_name": bom_dict.get(i["all_attributes"].get("bom_id", ""), ""),
                    "VendorId": i["all_attributes"]["vendor_id"],
                    "VendorName": i["all_attributes"]["vendor_name"],
                    "Orderdate": datetime.strptime(i["sk_timeStamp"][:10] + " 10:00:00",
                                                   "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y"),
                    "OrderPrice": i["all_attributes"].get("total_price", ""),
                    "Status": i["all_attributes"]["status"]
                }
                for i in po_data if i["all_attributes"]["status"] != "Received"
            ]
            lst = sorted(lst, key=lambda d: d['sk_timeStamp'], reverse=True)

            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def cmsPurchaseOrderGetVendorDetailsById(request_body):
        try:
            data = request_body #test
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            filter = {"pk_id": data["po_id"]}
            result = list(db_con.PurchaseOrder.find(filter))
            # print(result["lsi_key"])
            filter2 = {"pk_id": result[0]["lsi_key"]}
            vendor = list(db_con.Vendor.find(filter2))
            # print(vendor)
            response = {}
            if vendor:
                # vendor = vendor[0]
                response['order_id'] = data["po_id"]
                response['vendor_id'] = vendor[0]['pk_id']
                response['vendor_name'] = vendor[0]['all_attributes']['vendor_name']
                response['contact'] = vendor[0]['all_attributes']['contact_number']
                response['location'] = vendor[0]['all_attributes']['address1']
                response['email'] = vendor[0]['all_attributes']['email']
                response['against_po'] = result[0]['all_attributes'].get("against_po", "")
                response['deo'] = result[0]['all_attributes']['deo']
                response['ordered_date'] = (result[0]['sk_timeStamp']).split("T")[0]
                response['status'] = result[0]['all_attributes']['status']
                response['shipping_address'] = result[0]['all_attributes'].get("shipping_address", "")
                response['billing_address'] = result[0]['all_attributes'].get("billing_address", "")
            else:
                response['body'] = 'No vendor found for the purchase order'
            conct.close_connection(client)
            return {'statusCode': 200, 'body': response}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def cmsPurchaseOrderGetComponentsById(request_body):
        try:
            data = request_body #test
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            filter = {"pk_id": data["po_id"]}
            result = list(db_con.PurchaseOrder.find(filter))
            # print(result)
            if result:
                result = result[0]

                pipeline_categories = {"pk_id": 1, "all_attributes": 1, "sub_categories": 1}
                categories = list(db_con.Metadata.find({}, pipeline_categories))

                category = {item['pk_id'].replace("MDID", "CTID"): item for item in categories}

                pipeline_inventory = [
                    {"$match": {"gsipk_table": "Inventory"}},
                    {"$project": {"all_attributes": 1}}
                ]
                inventory = list(db_con.Inventory.find({}, {"all_attributes": 1}))
                inventory = {item['all_attributes']['cmpt_id']: item['all_attributes'] for item in inventory}

                qatest = list(db_con.GateEntry.find({"gsisk_id": data['po_id']}, {"_id": 0, "all_attributes.parts": 1}))

                qa_ref = {}
                for entry in qatest:
                    part = entry['all_attributes']['parts']
                    for part_key, value in part.items():
                        qa_ref[value['cmpt_id']] = int(value['received_qty']) if value['cmpt_id'] not in qa_ref else qa_ref[
                                                                                                                         value[
                                                                                                                             'cmpt_id']] + int(
                            value['received_qty'])
                dbpart = result["all_attributes"]["parts"]
                result = [
                    {
                        "cmpt_id": result["all_attributes"]["parts"][part_key]["cmpt_id"],
                        "ctgr_id": result["all_attributes"]["parts"][part_key]["ctgr_id"],
                        "ctgr_name": result["all_attributes"]["parts"][part_key]["ctgr_name"],
                        "department": result["all_attributes"]["parts"][part_key]["department"],
                        "mfr_part_num": result["all_attributes"]["parts"][part_key]["mfr_prt_num"],
                        "part_name": category[dbpart[part_key]["ctgr_id"]]['sub_categories'][
                            inventory[dbpart[part_key]["cmpt_id"]]['sub_ctgr']],
                        "received_qty": str(int(qa_ref[result["all_attributes"]["parts"][part_key]["cmpt_id"]]))
                        if result["all_attributes"]["parts"][part_key]["cmpt_id"] in qa_ref else '0',
                        "manufacturer": inventory[result["all_attributes"]["parts"][part_key]["cmpt_id"]].get('mfr', result[
                            "all_attributes"]["parts"][part_key].get("manufacturer", "-")),
                        "description": inventory[result["all_attributes"]["parts"][part_key]["cmpt_id"]].get('description',
                                                                                                             result[
                                                                                                                 "all_attributes"][
                                                                                                                 "parts"][
                                                                                                                 part_key][
                                                                                                                 "description"]),
                        "packaging": inventory[result["all_attributes"]["parts"][part_key]["cmpt_id"]].get('package',
                                                                                                           result[
                                                                                                               "all_attributes"][
                                                                                                               "parts"][
                                                                                                               part_key].get(
                                                                                                               "packaging",
                                                                                                               "")),
                        "quantity": result["all_attributes"]["parts"][part_key]["qty"],
                        "price": result["all_attributes"]["parts"][part_key]["price"],
                        "price_per_piece": result["all_attributes"]["parts"][part_key]["unit_price"]
                    }
                    if part_key.startswith("part") and
                       result["all_attributes"]["parts"][part_key]["department"] == 'Electronic'
                    else {
                        "cmpt_id": result["all_attributes"]["parts"][part_key]["cmpt_id"],
                        "ctgr_id": result["all_attributes"]["parts"][part_key]["ctgr_id"],
                        "ctgr_name": result["all_attributes"]["parts"][part_key]["ctgr_name"],
                        "department": result["all_attributes"]["parts"][part_key]["department"],
                        "mfr_part_num": result["all_attributes"]["parts"][part_key]["mfr_prt_num"],
                        # "balance_qty":int(result["all_attributes"]["parts"][part_key]["qty"])-int(qa_ref[result["all_attributes"]["parts"][part_key]["cmpt_id"]]) if result["all_attributes"]["parts"][part_key]["cmpt_id"] in qa_ref else result["all_attributes"]["parts"][part_key]["qty"],
                        "received_qty": str(int(qa_ref[result["all_attributes"]["parts"][part_key]["cmpt_id"]]))
                        if
                        result["all_attributes"]["parts"][part_key]["cmpt_id"] in qa_ref else '0',
                        "part_name": inventory[result["all_attributes"]["parts"][part_key]["cmpt_id"]].get('prdt_name',
                                                                                                           '--'),
                        "manufacturer": inventory[result["all_attributes"]["parts"][part_key]["cmpt_id"]].get('mfr', result[
                            "all_attributes"]["parts"][part_key].get("manufacturer", "-")),
                        "description": inventory[result["all_attributes"]["parts"][part_key]["cmpt_id"]].get('description',
                                                                                                             result[
                                                                                                                 "all_attributes"][
                                                                                                                 "parts"][
                                                                                                                 part_key][
                                                                                                                 "description"]),
                        "packaging": inventory[result["all_attributes"]["parts"][part_key]["cmpt_id"]].get('package',
                                                                                                           result[
                                                                                                               "all_attributes"][
                                                                                                               "parts"][
                                                                                                               part_key].get(
                                                                                                               "packaging",
                                                                                                               "")),
                        "quantity": result["all_attributes"]["parts"][part_key]["qty"],
                        "price": result["all_attributes"]["parts"][part_key]["price"],
                        "price_per_piece": result["all_attributes"]["parts"][part_key]["unit_price"]
                    }
                    for part_key in result["all_attributes"]["parts"]
                ]


                pipeline_gt_entr = [
                    {"$match": {"gsipk_table": "GateEntry", "gsisk_id": data['po_id']}},
                    {"$project": {"all_attributes.parts": 1}},
                    {"$unwind": "$all_attributes.parts"},
                    {"$replaceRoot": {"newRoot": "$all_attributes.parts"}}
                ]

                gt_entr = list(db_con.GateEntry.aggregate(pipeline_gt_entr))
                total_qty = 0
                print(gt_entr)
                if gt_entr:
                    total_qty = sum(sum(int(part['received_qty']) for key, part in item.items()) for item in gt_entr)

            conct.close_connection(client)
            return {'statusCode': 200, 'body': result, "rcvd_qty": str(total_qty)}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def CmsPurchaseOrderGetOtherInfo(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            filter = {"pk_id": data["po_id"]}
            projection = {
                "all_attributes.terms_and_conditions": 1,
                "all_attributes.payment_terms": 1,
                "_id": 0
            }
            result = (db_con.PurchaseOrder.find_one(filter, projection))["all_attributes"]
            conct.close_connection(client)
            return {'statusCode': 200, 'body': result}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def CmsPurchaseOrderGetBankDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            filter = {"pk_id": data["po_id"]}
            projection = {
                "lsi_key": 1,
                "_id": 0
            }
            result = (db_con.PurchaseOrder.find_one(filter, projection))
            projection2 = {
                "all_attributes.bank_name": 1,
                "all_attributes.account_number": 1,
                "all_attributes.gst_number": 1,
                "all_attributes.ifsc_code": 1,
                "_id": 0
            }
            filter2 = {"pk_id": result["lsi_key"]}
            vendor = db_con.Vendor.find_one(filter2, projection2)
            response = {}
            if vendor:
                response['bank_name'] = vendor["all_attributes"]["bank_name"]
                response['account_number'] = vendor['all_attributes']["account_number"]
                response['gst_number'] = vendor['all_attributes']['gst_number']
                response['ifsc_code'] = vendor['all_attributes']['ifsc_code']
            else:
                response['body'] = 'No vendor found for the purchase order'

            conct.close_connection(client)
            return {'statusCode': 200, 'body': response}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def CmsPurchaseOrderGetDocumentsById(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            filter = {"pk_id": data["po_id"]}
            projection = {
                "all_attributes.documents": 1,
                "_id": 0
            }
            result = (db_con.PurchaseOrder.find_one(filter, projection))["all_attributes"]
            # print(result)
            lst = []
            for key, doc in result["documents"].items():
                res = {}
                res["content"] = file_get(doc)
                res["document_name"] = key
                lst.append(res)
            # print(lst)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}
        



    def cmsPurchaseOrderGateEntryGetDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id = data["po_id"]
            return_id = data.get("return_id", "")
            filter = {"pk_id": data["po_id"]}
            projection = {
                "_id": 0
            }
            result = (db_con.PurchaseOrder.find_one(filter, projection))
            if result:
                bom_id = result['all_attributes'].get('bom_id','')
                category = db_con["Metadata"].find()
                category = {
                    item['pk_id'].replace("MDID", "CTID"): (
                        {
                            "ctgr_name": item['gsisk_id'],
                            "sub_categories": {
                                key: value for key, value in item['sub_categories'].items()
                            }
                        }
                        if item['gsipk_id'] == 'Electronic'
                        else {"ctgr_name": item['gsisk_id']}
                    )
                    for item in category
                }
                filter = {"gsipk_table": "Inventory"}
                projection = {
                    "_id": 0,
                    "all_attributes": 1
                }
                inventory = list(db_con["Inventory"].find(filter, projection))
                inventory = {item["all_attributes"]['cmpt_id']: item["all_attributes"] for item in inventory}
                part_info = {}
                if data.get('status', '') == "PurchaseReturn":
                    return_ref = {}
                    return_inventory = list(db_con.GateEntry.find({"all_attributes.return_id": return_id}))
                    for item in return_inventory:
                        for part_key, part_attributes in item["all_attributes"]['parts'].items():
                            cmpt_id = part_attributes['cmpt_id']
                            received_qty = part_attributes['received_qty']
                            return_ref[cmpt_id] = received_qty if cmpt_id not in return_ref else str(
                                int(return_ref[cmpt_id]) + int(received_qty))
                    # return return_ref
                    return_data = db_con["PurchaseReturn"].find_one(
                        {"gsipk_table": "PurchaseReturn", "pk_id": return_id})
                    part_info["parts"] = {
                        key: {
                            "cmpt_id": value['cmpt_id'],
                            "ctgr_id": value['ctgr_id'],
                            "unit_price": value['price_per_piece'],
                            "received_qty": '0' if not return_ref and value[
                                'cmpt_id'] not in return_ref else return_ref.get(value['cmpt_id'], '0'),
                            "balance_qty": str(int(value['qty']) - abs(
                                int('0' if not return_ref and value['cmpt_id'] not in return_ref else return_ref[
                                    value['cmpt_id']]))),
                            "description": inventory[value['cmpt_id']].get('description', '-'),
                            "packaging": inventory[value['cmpt_id']].get('packaging', '-'),
                            "mfr_prt_num": value['mfr_prt_num'],
                            "manufacturer": inventory[value['cmpt_id']].get('manufacturer', '-'),
                            "price": value['price'],
                            "qty": value['qty'],
                            "ctgr_name": category[value['ctgr_id']]['ctgr_name'],
                            "department": value['department'],
                            "prdt_name": category[value['ctgr_id']]['sub_categories'][
                                inventory[value['cmpt_id']]['sub_ctgr']]
                            if value['department'] != 'Mechanic' else inventory[value['cmpt_id']]['prdt_name']
                        }
                        for key, value in return_data['all_attributes']['parts'].items()
                        if str(int(value['qty']) - int(
                            '0' if not return_ref and value['cmpt_id'] not in return_ref else return_ref.get(
                                value['cmpt_id'], '0'))) != '0'
                    }
                    part_info["order_id"] = result["pk_id"]
                    part_info['return_id'] = data['return_id']
                    part_info["order_date"] = result["sk_timeStamp"][:10]
                    part_info['total_ordered_quantity'] = result['all_attributes']['total_qty']
                    return {"statusCode": 200, "body": part_info}
                else:
                    gate_entry = list(db_con["GateEntry"].find({"gsipk_table": "GateEntry", "gsisk_id": po_id}))
                    ref = {}
                    for item in gate_entry:
                        # if item['all_attributes'].get("return_id","")=="":
                        for key, value in item['all_attributes']['parts'].items():
                            ref[value['cmpt_id']] = int(value['received_qty']) if value['cmpt_id'] not in ref else ref[value['cmpt_id']] + int(value['received_qty'])
                    part_info["parts"] = {
                        key: {
                            "cmpt_id": value['cmpt_id'],
                            "ctgr_id": value['ctgr_id'],
                            "received_qty": value.get('received_qty', '0'),
                            "description": inventory[value['cmpt_id']].get('description', ''),
                            "packaging": inventory[value['cmpt_id']].get('packaging', ''),
                            "unit_price": value['unit_price'],
                            "mfr_prt_num": value['mfr_prt_num'],
                            "manufacturer": inventory[value['cmpt_id']].get('manufacturer', '-'),
                            "price": value['price'],
                            "qty": value['qty'],
                            "ctgr_name": category[value['ctgr_id']]['ctgr_name'],
                            "department": value['department'],
                            "prdt_name": category[value['ctgr_id']]['sub_categories'][
                                inventory[value['cmpt_id']]['sub_ctgr']]
                            if value['department'] != 'Mechanic' else inventory[value['cmpt_id']]['prdt_name'],
                            "balance_qty": str(
                                abs(int(value['qty']) - abs(ref[value['cmpt_id']]) if gate_entry else int(
                                    value['qty'])))
                        }
                        for key, value in result['all_attributes']['parts'].items()
                        if (not gate_entry or value['cmpt_id'] in ref) and (
                            str(int(value['qty']) - ref[value['cmpt_id']]) if gate_entry else value['qty']) != "0"
                    }
                    ven_id=result['all_attributes']['vendor_id']
                    # query=list(db_con.Vendor.find({'pk_id':ven_id},{'_id':0,'all_attributes.vendor_poc_name':1,'all_attributes.vendor_poc_contact_num':1}))
                    query=list(db_con.Vendor.find({'pk_id':ven_id},{'_id':0,'all_attributes':1}))
                    part_info["order_id"] = result["pk_id"]
                    part_info["order_date"] = result["sk_timeStamp"][:10]
                    part_info['total_ordered_quantity'] = result['all_attributes']['total_qty']
                    # part_info['vendor_poc_name'] = query[0]['all_attributes']['vendor_poc_name']
                    # part_info['vendor_poc_contact_num'] = query[0]['all_attributes']['vendor_poc_contact_num']
                    part_info['vendor_poc_name'] = query[0]['all_attributes'].get('vendor_poc_name', '-')
                    part_info['vendor_poc_contact_num'] = query[0]['all_attributes'].get('vendor_poc_contact_num', '-')
                    part_info['receiver'] = result['all_attributes']['receiver']
                    part_info['receiver_contact'] = result['all_attributes']['receiver_contact']
 
                    # return {"statusCode": 200, "body": part_info}
 
            conct.close_connection(client)
            return {'statusCode': 200, 'body': part_info}
 
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    # def cmsPurchaseOrderGateEntryGetDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         po_id = data["po_id"]
    #         return_id = data.get("return_id", "")
    #         filter = {"pk_id": data["po_id"]}
    #         projection = {
    #             "_id": 0
    #         }
    #         result = (db_con.PurchaseOrder.find_one(filter, projection))
    #         if result:
    #             bom_id = result['all_attributes'].get('bom_id','')
    #             category = db_con["Metadata"].find()
    #             category = {
    #                 item['pk_id'].replace("MDID", "CTID"): (
    #                     {
    #                         "ctgr_name": item['gsisk_id'],
    #                         "sub_categories": {
    #                             key: value for key, value in item['sub_categories'].items()
    #                         }
    #                     }
    #                     if item['gsipk_id'] == 'Electronic'
    #                     else {"ctgr_name": item['gsisk_id']}
    #                 )
    #                 for item in category
    #             }
    #             filter = {"gsipk_table": "Inventory"}
    #             projection = {
    #                 "_id": 0,
    #                 "all_attributes": 1
    #             }
    #             inventory = list(db_con["Inventory"].find(filter, projection))
    #             inventory = {item["all_attributes"]['cmpt_id']: item["all_attributes"] for item in inventory}
    #             part_info = {}
    #             if data.get('status', '') == "PurchaseReturn":
    #                 return_ref = {}
    #                 return_inventory = list(db_con.GateEntry.find({"all_attributes.return_id": return_id}))
    #                 for item in return_inventory:
    #                     for part_key, part_attributes in item["all_attributes"]['parts'].items():
    #                         cmpt_id = part_attributes['cmpt_id']
    #                         received_qty = part_attributes['received_qty']
    #                         return_ref[cmpt_id] = received_qty if cmpt_id not in return_ref else str(
    #                             int(return_ref[cmpt_id]) + int(received_qty))
    #                 # return return_ref
    #                 return_data = db_con["PurchaseReturn"].find_one(
    #                     {"gsipk_table": "PurchaseReturn", "pk_id": return_id})
    #                 part_info["parts"] = {
    #                     key: {
    #                         "cmpt_id": value['cmpt_id'],
    #                         "ctgr_id": value['ctgr_id'],
    #                         "unit_price": value['price_per_piece'],
    #                         "received_qty": '0' if not return_ref and value[
    #                             'cmpt_id'] not in return_ref else return_ref.get(value['cmpt_id'], '0'),
    #                         "balance_qty": str(int(value['qty']) - abs(
    #                             int('0' if not return_ref and value['cmpt_id'] not in return_ref else return_ref[
    #                                 value['cmpt_id']]))),
    #                         "description": inventory[value['cmpt_id']].get('description', '-'),
    #                         "packaging": inventory[value['cmpt_id']].get('packaging', '-'),
    #                         "mfr_prt_num": value['mfr_prt_num'],
    #                         "manufacturer": inventory[value['cmpt_id']].get('manufacturer', '-'),
    #                         "price": value['price'],
    #                         "qty": value['qty'],
    #                         "ctgr_name": category[value['ctgr_id']]['ctgr_name'],
    #                         "department": value['department'],
    #                         "prdt_name": category[value['ctgr_id']]['sub_categories'][
    #                             inventory[value['cmpt_id']]['sub_ctgr']]
    #                         if value['department'] != 'Mechanic' else inventory[value['cmpt_id']]['prdt_name']
    #                     }
    #                     for key, value in return_data['all_attributes']['parts'].items()
    #                     if str(int(value['qty']) - int(
    #                         '0' if not return_ref and value['cmpt_id'] not in return_ref else return_ref.get(
    #                             value['cmpt_id'], '0'))) != '0'
    #                 }
    #                 part_info["order_id"] = result["pk_id"]
    #                 part_info['return_id'] = data['return_id']
    #                 part_info["order_date"] = result["sk_timeStamp"][:10]
    #                 part_info['total_ordered_quantity'] = result['all_attributes']['total_qty']
    #                 return {"statusCode": 200, "body": part_info}
    #             else:
    #                 gate_entry = list(db_con["GateEntry"].find({"gsipk_table": "GateEntry", "gsisk_id": po_id}))
    #                 ref = {}
    #                 for item in gate_entry:
    #                     # if item['all_attributes'].get("return_id","")=="":
    #                     for key, value in item['all_attributes']['parts'].items():
    #                         ref[value['cmpt_id']] = int(value['received_qty']) if value['cmpt_id'] not in ref else ref[
    #                                                                                                                    value[
    #                                                                                                                        'cmpt_id']] + int(
    #                             value['received_qty'])
    #                 part_info["parts"] = {
    #                     key: {
    #                         "cmpt_id": value['cmpt_id'],
    #                         "ctgr_id": value['ctgr_id'],
    #                         "received_qty": value.get('received_qty', '0'),
    #                         "description": inventory[value['cmpt_id']].get('description', ''),
    #                         "packaging": inventory[value['cmpt_id']].get('packaging', ''),
    #                         "unit_price": value['unit_price'],
    #                         "mfr_prt_num": value['mfr_prt_num'],
    #                         "manufacturer": inventory[value['cmpt_id']].get('manufacturer', '-'),
    #                         "price": value['price'],
    #                         "qty": value['qty'],
    #                         "ctgr_name": category[value['ctgr_id']]['ctgr_name'],
    #                         "department": value['department'],
    #                         "prdt_name": category[value['ctgr_id']]['sub_categories'][
    #                             inventory[value['cmpt_id']]['sub_ctgr']]
    #                         if value['department'] != 'Mechanic' else inventory[value['cmpt_id']]['prdt_name'],
    #                         "balance_qty": str(
    #                             abs(int(value['qty']) - abs(ref[value['cmpt_id']]) if gate_entry else int(
    #                                 value['qty'])))
    #                     }
    #                     for key, value in result['all_attributes']['parts'].items()
    #                     if (not gate_entry or value['cmpt_id'] in ref) and (
    #                         str(int(value['qty']) - ref[value['cmpt_id']]) if gate_entry else value['qty']) != "0"
    #                 }
    #                 part_info["order_id"] = result["pk_id"]
    #                 part_info["order_date"] = result["sk_timeStamp"][:10]
    #                 part_info['total_ordered_quantity'] = result['all_attributes']['total_qty']
    #                 # return {"statusCode": 200, "body": part_info}
    #         conct.close_connection(client)
    #         return {'statusCode': 200, 'body': part_info}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'PO deletion failed'}



    
    def CmsPurchaseOrderGateEntryCreate(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        sk_timeStamp = (datetime.now()).isoformat()
        purchaseorder_id = data['order_number']
        invoice_document = data['documents']['invoice']
        file_type = data['documents']['file_type']
        sender_name = data['sender_name']
        sender_contact_number = data['sender_contact_number']
        receiver_name = data.get('receiver_name', '')
        receiver_contact = data.get('receiver_contact', '')
        parts = data['parts']
        po_tablename = "PurchaseOrder"
        purchase_order_query = {"gsipk_table": po_tablename, "pk_id": purchaseorder_id}
        result = db_con[po_tablename].find_one(purchase_order_query)
        if result:
            # Query to fetch inventory data
            inventory_query = {"gsipk_table": 'Inventory'}
            invent_data = list(db_con.Inventory.find(inventory_query))
            invent_data = {item['pk_id']: item for item in invent_data}
            # Query to fetch QA Test data
            qa_test_query = {"gsipk_table": 'GateEntry', "gsisk_id": purchaseorder_id}
            qatest = list(db_con.GateEntry.find(qa_test_query))
            qa_ref = {}
            for entry in qatest:
                part = entry["all_attributes"]['parts']
                for part_key, value in part.items():
                    qa_ref[value['cmpt_id']] = int(value['qty']) if value['cmpt_id'] not in qa_ref else qa_ref[value[
                        'cmpt_id']] + int(value['qty'])
            vendorId = result['all_attributes']['vendor_id']
            parts = (result)['all_attributes']['parts']
            part_ref = {part['cmpt_id']: int(part['qty']) for key, part in parts.items()}
            part_ref = {key: part_ref[key] + qa_ref.get(key, 0) for key in part_ref.keys()}
            if any(int(part['qty']) > part_ref[part['cmpt_id']] for part in data['parts']):
                return {"statusCode": 400, "body": "Gate entry quantity should be less than ordered amount"}
            if any(int(part['received_qty']) > int(part['qty']) for part in data['parts']):
                return {"statusCode": 400,
                        "body": "Please ensure the received quantity is less than or equal to the ordered amount"}
            total_qty = sum(int(part['received_qty']) for part in data['parts'])
            if not total_qty:
                return {"statusCode": 400, "body": "Cannot create record without components"}
            inward_tablename = 'GateEntry'
            status = 'Entry'
            pending = 'QA_test'
            # Query to fetch existing inward details
            inward_query = {"gsipk_table": inward_tablename, "gsisk_id": purchaseorder_id}
            inward_details = list(db_con[inward_tablename].find(inward_query))
            inward_id = '01'
            inward_ids = []
            if inward_details:
                inward_ids = sorted([i["all_attributes"]["inwardId"].split("_IN")[-1] for i in inward_details],
                                    reverse=True)
                inward_id = str(((2 - len(str(int(inward_ids[0]) + 1)))) * "0") + str(int(inward_ids[0]) + 1) if len(
                    str(int(inward_ids[0]))) <= 2 else str(int(inward_ids[0]) + 1)
            part_key_reference = {}
            for key in result['all_attributes']['parts'].keys():
                part_key_reference[result['all_attributes']['parts'][key]['mfr_prt_num']] = key
            if not part_key_reference:
                return {"statusCode": 400, "body": "Something went wrong while fetching parts for the order"}
            parts_data, component_twi = {}, []
            for part in data['parts']:
                part_number = part_key_reference[part['mfr_prt_num']]
                parts_data[part_number] = part
                pk_id = part['cmpt_id']
                sk_timeStamp = invent_data[part['cmpt_id']]['sk_timeStamp']
                # qty = int(part['received_qty']) + int(invent_data[part['cmpt_id']]["all_attributes"]['qty'])
                qty = int(float(part['received_qty'])) + int(float(invent_data[part['cmpt_id']]["all_attributes"]['qty']))
                # rcd = int(part['received_qty']) + int(invent_data[part['cmpt_id']]["all_attributes"].get('rcd_qty', 0))
                rcd = int(float(part['received_qty'])) + int(float(invent_data[part['cmpt_id']]["all_attributes"].get('rcd_qty', 0)))
                # Update quantity and received quantity in inventory
                db_con.Inventory.update_one(
                    {"pk_id": pk_id, "sk_timeStamp": sk_timeStamp},
                    {"$set": {"all_attributes.rcd_qty": str(rcd)}}
                )
            if not parts_data:
                return {"statusCode": 400, "body": "Cannot create gate entry without parts"}

            image_upload = {}
            if data["images"]:
                for i in data["images"]:
                    img = i["image"]
                    file_type1 = i["file_type"]
                    image_type = i["image_type"]
                    image_upload[i["file_type"]] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "",
                                                                            purchaseorder_id + inward_id,
                                                                            file_type1, i["image"])
            # Removed the condition to return an error if images are not provided

            file_upload = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "",
                                                purchaseorder_id + inward_id, "invoice." + file_type,
                                                invoice_document) if invoice_document else True
            if file_upload:
                all_attributes = {
                    'inwardId': purchaseorder_id + "_IN" + inward_id,
                    'status': inward_tablename,
                    'total_recieved_quantity': total_qty,
                    'actions': pending,
                    'purchaseorder_id': purchaseorder_id,
                    'invoice': file_upload if invoice_document else '',
                    'invoice_num': data.get('invoice_num'),
                    'photo': image_upload,
                    'gate_entry_date': sk_timeStamp[:10],
                    'sender_name': sender_name,
                    'sender_contact_number': sender_contact_number,
                    'parts': parts_data,
                    'vendorId': vendorId,
                    'rec_name': receiver_name,
                    'rec_cont': receiver_contact,
                    'vendorId': vendorId
                }

                if data.get('return_id', ''):
                    all_attributes['return_id'] = data['return_id']

                item = {
                    "pk_id": purchaseorder_id + "_IN" + inward_id,
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": all_attributes,
                    "gsipk_table": inward_tablename,
                    "gsisk_id": purchaseorder_id,
                    "lsi_key": '--'
                }

                response = db_con.GateEntry.insert_one(item)
                return {"statusCode": 200, "body": "Record for gate entry created successfully"}
            else:
                return {"statusCode": 400, "body": "Failed while uploading invoice documents"}




    # def CmsPurchaseOrderGateEntryCreate(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     sk_timeStamp = (datetime.now()).isoformat()
    #     purchaseorder_id = data['order_number']
    #     invoice_document = data['documents']['invoice']
    #     file_type = data['documents']['file_type']
    #     sender_name = data['sender_name']
    #     sender_contact_number = data['sender_contact_number']
    #     receiver_name = data.get('receiver_name', '')
    #     receiver_contact = data.get('receiver_contact', '')
    #     parts = data['parts']
    #     po_tablename = "PurchaseOrder"
    #     purchase_order_query = {"gsipk_table": po_tablename, "pk_id": purchaseorder_id}
    #     result = db_con[po_tablename].find_one(purchase_order_query)
    #     if result:
    #         # Query to fetch inventory data
    #         inventory_query = {"gsipk_table": 'Inventory'}
    #         invent_data = list(db_con.Inventory.find(inventory_query))
    #         invent_data = {item['pk_id']: item for item in invent_data}
    #         # Query to fetch QA Test data
    #         qa_test_query = {"gsipk_table": 'GateEntry', "gsisk_id": purchaseorder_id}
    #         qatest = list(db_con.GateEntry.find(qa_test_query))
    #         qa_ref = {}
    #         for entry in qatest:
    #             part = entry["all_attributes"]['parts']
    #             for part_key, value in part.items():
    #                 qa_ref[value['cmpt_id']] = int(value['qty']) if value['cmpt_id'] not in qa_ref else qa_ref[value[
    #                     'cmpt_id']] + int(value['qty'])
    #         vendorId = result['all_attributes']['vendor_id']
    #         parts = (result)['all_attributes']['parts']
    #         part_ref = {part['cmpt_id']: int(part['qty']) for key, part in parts.items()}
    #         part_ref = {key: part_ref[key] + qa_ref.get(key, 0) for key in part_ref.keys()}
    #         if any(int(part['qty']) > part_ref[part['cmpt_id']] for part in data['parts']):
    #             return {"statusCode": 400, "body": "gate entry quantity should be less than ordered amount"}
    #         if any(int(part['received_qty']) > int(part['qty']) for part in data['parts']):
    #             return {"statusCode": 400,
    #                     "body": "Please ensure the received quantity is less than or equal to the ordered amount"}
    #         total_qty = sum(int(part['received_qty']) for part in data['parts'])
    #         if not total_qty:
    #             return {"statusCode": 400, "body": "Cannot create record without components"}
    #         inward_tablename = 'GateEntry'
    #         status = 'Entry'
    #         pending = 'QA_test'
    #         # Query to fetch existing inward details
    #         inward_query = {"gsipk_table": inward_tablename, "gsisk_id": purchaseorder_id}
    #         inward_details = list(db_con[inward_tablename].find(inward_query))
    #         inward_id = '01'
    #         inward_ids = []
    #         if inward_details:
    #             inward_ids = sorted([i["all_attributes"]["inwardId"].split("_IN")[-1] for i in inward_details],
    #                                 reverse=True)
    #             inward_id = str(((2 - len(str(int(inward_ids[0]) + 1)))) * "0") + str(int(inward_ids[0]) + 1) if len(
    #                 str(int(inward_ids[0]))) <= 2 else str(int(inward_ids[0]) + 1)
    #         part_key_reference = {}
    #         for key in result['all_attributes']['parts'].keys():
    #             part_key_reference[result['all_attributes']['parts'][key]['mfr_prt_num']] = key
    #         if not part_key_reference:
    #             return {"statusCode": 400, "body": "Something went wrong while fetching parts for the order"}
    #         parts_data, component_twi = {}, []
    #         for part in data['parts']:
    #             part_number = part_key_reference[part['mfr_prt_num']]
    #             parts_data[part_number] = part
    #             pk_id = part['cmpt_id']
    #             sk_timeStamp = invent_data[part['cmpt_id']]['sk_timeStamp']
    #             qty = int(part['received_qty']) + int(invent_data[part['cmpt_id']]["all_attributes"]['qty'])
    #             rcd = int(part['received_qty']) + int(invent_data[part['cmpt_id']]["all_attributes"].get('rcd_qty', 0))
    #             # Update quantity and received quantity in inventory
    #             db_con.Inventory.update_one(
    #                 {"pk_id": pk_id, "sk_timeStamp": sk_timeStamp},
    #                 {"$set": {"all_attributes.rcd_qty": str(rcd)}}
    #             )
    #         if not parts_data:
    #             return {"statusCode": 400, "body": "Cannot create gate entry without parts"}

    #         image_upload = {}
    #         if data["images"]:
    #             for i in data["images"]:
    #                 img = i["image"]
    #                 file_type1 = i["file_type"]
    #                 image_type = i["image_type"]
    #                 # print(img,"imgimgimg")
    #                 # print(image_type)
    #                 # print(file_type1)
    #                 # image_upload[i["file_type"]] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "",
    #                 #                                                         purchaseorder_id + inward_id,
    #                 #                                                         file_type1 + "." + image_type, i["image"])
    #                 image_upload[i["file_type"]] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "",
    #                                                                         purchaseorder_id + inward_id,
    #                                                                         file_type1, i["image"])
    #         else:
    #             return {"statusCode": 400, "body": "Please upload box image"}
    #         if image_upload:
    #             # file_upload = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "",
    #             #                                        purchaseorder_id + inward_id, "invoice." + file_type,
    #             #                                        invoice_document) if invoice_document else True
    #             file_upload = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "",
    #                                                    purchaseorder_id + inward_id, "invoice." + file_type,
    #                                                    invoice_document) if invoice_document else True
    #             if file_upload:
    #                 all_attributes = {
    #                     'inwardId': purchaseorder_id + "_IN" + inward_id,
    #                     'status': inward_tablename,
    #                     'total_recieved_quantity': total_qty,
    #                     'actions': pending,
    #                     'purchaseorder_id': purchaseorder_id,
    #                     'invoice': file_upload if invoice_document else '',
    #                     'invoice_num': data.get('invoice_num'),
    #                     'photo': image_upload,
    #                     'gate_entry_date': sk_timeStamp[:10],
    #                     'sender_name': sender_name,
    #                     'sender_contact_number': sender_contact_number,
    #                     'parts': parts_data,
    #                     'vendorId': vendorId,
    #                     'rec_name': receiver_name,
    #                     'rec_cont': receiver_contact,
    #                     'vendorId': vendorId
    #                 }

    #                 if data.get('return_id', ''):
    #                     all_attributes['return_id'] = data['return_id']

    #                 item = {
    #                     "pk_id": purchaseorder_id + "_IN" + inward_id,
    #                     "sk_timeStamp": sk_timeStamp,
    #                     "all_attributes": all_attributes,
    #                     "gsipk_table": inward_tablename,
    #                     "gsisk_id": purchaseorder_id,
    #                     "lsi_key": '--'
    #                 }

    #                 response = db_con.GateEntry.insert_one(item)
    #                 return {"statusCode": 200, "body": "Record for gate entry created successfully"}
    #             else:
    #                 return {"statusCode": 400, "body": "Failed while uploading invoice documents"}
    #         # else:
    #         #     return {"statusCode": 400, "body": "Failed while uploading box photo}

    def cmsPurchaseOrderSaveQATest(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            result = list(db_con.QATest.find({}))
            po_id = data["order_no"]
            # QUERY TO RETRIEVE DATA FOR QATEST
            gsipk_table = "QATest"
            qa_id = data['inwardId'].split('IN')[-1]
            gate_id = data["inwardId"]
            QA_test = "QA_test"
            poData = list(db_con.PurchaseOrder.find(
                {"pk_id": po_id}
                , {"_id": 0, "all_attributes": 1}))
            gateEntry = list(db_con.GateEntry.find({
                # "$and": [
                #     {"pk_id": gate_id},
                #     {"all_attributes.actions": QA_test}]},
                "$and": [
                    {"pk_id": gate_id}]},
                {"_id": 0, "all_attributes": 1, "pk_id": 1, "sk_timeStamp": 1}))
            #GENERATING AUTO INCREMENT BATCH ID
            batch_id = db_con.all_tables.find_one({"pk_id":"top_ids"},{"_id":0,"all_attributes.batchId":1})
            if 'batchId' in batch_id['all_attributes']:
                batch_id = int(batch_id['all_attributes']['batchId'])+1
            else:
                batch_id = len(list(db_con.inward.find({})))
            if gateEntry:
                parts = gateEntry[0]['all_attributes']['parts']
                quant_ref = {part['cmpt_id']: int(part['received_qty']) for key, part in parts.items()}
                if any(1 for part in data['parts'] if
                       quant_ref[part['cmpt_id']] != int(part['pass_qty']) + int(part['fail_qty'])):
                    return {'statusCode': 404,
                            'body': 'pass qty and fail qty do not match the quantity for some components'}
                parts = [
                    {
                        "cmpt_id": part_data["cmpt_id"],
                        "ctgr_id": part_data['ctgr_id'],
                        "mfr_prt_num": part_data["mfr_prt_num"],
                        "prdt_name": part_data["prdt_name"],
                        "description": part_data["description"],
                        "department": data["parts"][j]["department"],
                        "packaging": part_data["packaging"],
                        "qty": str(part_data["qty"]),
                        "price": data["parts"][j]["price"],
                        "price_per_piece": data["parts"][j]["unit_price"],
                        "manufacturer": part_data['manufacturer'] if 'manufacturer' in part_data else '-',
                        "pass_qty": data["parts"][j]["pass_qty"],
                        "fail_qty": data["parts"][j]["fail_qty"],
                        "lot_id": data["parts"][j]["lot_id"],
                        "batchId": "BTC" + str(batch_id)
                        # "batchId": "BTC" + str(gate_id[9:])
                    }
                    for i in poData
                    for part_key, part_data in i.get("all_attributes", {}).get("parts", {}).items()
                    for j in range(len(data.get("parts", [])))
                    if part_data["mfr_prt_num"] == data["parts"][j].get("part_no")
                ]
                for part in data['parts']:
                    cmpt_id = part["cmpt_id"]
                    quant_ref[cmpt_id] += int(part['fail_qty'])
                    inventory_query = {
                        "gsipk_table": "Inventory",
                        "pk_id": cmpt_id
                    }
                    inventory_data = db_con["Inventory"].find_one(inventory_query)
                    fail_qty = int(inventory_data['all_attributes'].get("fail_qty", 0)) + int(part['fail_qty'])
                    # UPDATE FAIL_QTY IN INVENTORY COLLECTION
                    db_con["Inventory"].update_one(
                        inventory_query,
                        {"$set": {"all_attributes.fail_qty": fail_qty}}
                    )
                docs1 = {}
                photo = {}
                for key, doc in data["invoice_photo"].items():
                    photo[key] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "", gate_id, key,doc)
                docs1["photo"] = photo
                # UPLOADING IMAGE AND DOCUMENT
                if "invoice_document" in data.keys():
                    docs1["invoice"] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "pdf",gate_id, "invoice.pdf", data["invoice_document"])
                for doc in data["documents"]:
                    image_path = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, doc["doc_type"],gate_id, doc["doc_name"], doc["doc_body"])
                    docs1["QATest"] = image_path

                for excel in data.get("excle", []):
                    excel_path = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, excel["excle_type"], gate_id, excel["file_type"], excel["excle"])
                    docs1[excel["file_type"]] = excel_path

                # Add CSV file
                if "csv_document" in data.keys():
                    csv_path = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "csv", gate_id, "SendFinalProducts.csv", data["csv_document"])
                    docs1["SendFinalProducts.csv"] = csv_path
                
                # QUERY TO RETRIEVE DATA FOR VENDOR
                vendor_id = gateEntry[0]["all_attributes"]["vendorId"]
                vendor_query = {
                    "gsipk_table": "Vendor",
                    "pk_id": vendor_id
                }
                vendor_data = db_con["Vendor"].find_one(vendor_query)
                all_attributes = {
                    "parts": {f'part{i + 1}': parts[i] for i in range(len(parts))},
                    "QA_date": data["QA_date"],
                    "vendorId": vendor_id,
                    "vendor_contact_number": vendor_data["all_attributes"]["contact_number"],
                    "vendor_name": vendor_data["all_attributes"]["vendor_name"],
                    'actions': 'inward',
                    "sender_name": data["sender_name"],
                    "invoice_num": data["invoice_num"],
                    "sender_contact_number": data["sender_contact_number"],
                    "description": data["description"],
                    "sk_timeStamp": sk_timeStamp,
                    "po_id": po_id,
                    "inwardId": data["inwardId"],
                    "gate_entry_date": gateEntry[0]["all_attributes"]["gate_entry_date"]
                }
                all_attributes.update(docs1)

                # INSERT QA DATA INTO MONGODB
                qa_item = {
                    "pk_id": po_id + "_QAID" + qa_id,
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": all_attributes,
                    "gsipk_table": gsipk_table,
                    "gsisk_id": po_id,
                    "lsi_key": "status_QA-Test"
                }
                db_con[gsipk_table].insert_one(qa_item)
                db_con['all_tables'].update_one(
                    {"pk_id": 'top_ids'},
                    {"$set": {"all_attributes.batchId": str(batch_id)}}
                    )
                # UPDATE GATE ENTRY DATA IN MONGODB
                db_con["GateEntry"].update_one(
                    {"pk_id": gate_id},
                    {"$set": {
                        "all_attributes.pending": "Inward",
                        "all_attributes.actions": "Inward"
                    }}
                )
                conct.close_connection(client)
                return {'statusCode': 200, 'body': 'QA added successfully'}

            else:
                return {"statusCode": 400, "body": "No record found for Gate Entry"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def cmsPurchaseOrderQaTestGetDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id = data['po_id']
            inwardId = data['inwardId']
            po_tablename = 'PurchaseOrder'
            inward_tablename = 'GateEntry'

            # Fetch category data
            category = {}
            # for item in db_con['Metadata'].find({"gsipk_table": "Metadata"}):
            for item in db_con['Metadata'].find():
                pk_id = item['pk_id'].replace("MDID", "CTID")
                if item['gsipk_id'] == 'Electronic':
                    sub_categories = {key: value for key, value in item['sub_categories'].items()}
                    category[pk_id] = {"ctgr_name": item['gsisk_id'], "sub_categories": sub_categories}
                else:
                    category[pk_id] = {"ctgr_name": item['gsisk_id']}
            # #print(category)
            # Fetch inventory data
            inventory = {}
            d = list(db_con['Inventory'].find())

            for item in d:
                # #print(item)
                inventory[item['pk_id']] = item['all_attributes']

            # Fetch gate entry details
            result = db_con[inward_tablename].find_one(
                # Query criteria
                {"gsipk_table": inward_tablename, "gsisk_id": po_id, "pk_id": inwardId}
                # {"all_attributes": 1}# Projection
            )
            result = dict(result) if result else {}


            if result:
                response = {
                    'order_no': po_id,
                    'inwardId': result['all_attributes']['inwardId'],
                    'QA_date': str(datetime.today()),
                    'invoice_photo': {i: file_get(result['all_attributes']['photo'][i]) for i in
                                      result['all_attributes']['photo']},
                    'invoice_document': file_get(result['all_attributes']['invoice']),
                    'invoice_num': result['all_attributes']['invoice_num'],
                    'sender_name': result['all_attributes']['sender_name'],
                    'vendorId': result['all_attributes']['vendorId'],
                    'sender_contact_number': result['all_attributes']['sender_contact_number'],
                    'parts': []
                }
                # #print(result['all_attributes']['parts'])
                for key, value in result['all_attributes']['parts'].items():
                    if value['received_qty'] != '0':
                        part_data = {
                            "s_no": key.replace("part", ""),
                            "ctgr_id": value['ctgr_id'],
                            "cmpt_id": value['cmpt_id'],
                            "part_no": value['mfr_prt_num'],
                            "part_name": category[value['ctgr_id']]['sub_categories'][
                                inventory[value['cmpt_id']]['sub_ctgr']] if value['department'] == 'Electronic' else
                            inventory[value['cmpt_id']].get('prdt_name', ''),
                            "unit_price": value['unit_price'],
                            "department": value['department'],
                            "received_qty": value['received_qty'],
                            "price": value['price'],
                            "description": inventory[value['cmpt_id']].get('description', ''),
                            "packaging": inventory[value['cmpt_id']].get('package', ''),
                            "manufacturer": inventory[value['cmpt_id']].get('mfr', '-'),
                            "pass_qty": "0",
                            "fail_qty": "0"
                        }
                        response['parts'].append(part_data)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': response}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def CmsInventorySearchSuggestionInPO(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            env_type = data.get("env_type", "")

            category_name = data["name"].strip()

            if not category_name:
                return {"statusCode": 404, "body": "Please provide a search parameter"}

            db = list(db_con.Metadata.find({}, {"gsisk_id": 1, "sub_categories": 1, "pk_id": 1}))
            matched_values = []
            category_metadata = {item['pk_id'].replace("MDID", "CTID"): {"category_name": item['gsisk_id']} for item in
                                 db}
            query = {"gsipk_id": data.get('department', "")} if data.get("department", '') in ['Electronic',
                                                                                               'Mechanic'] else {}
            db = list(db_con.Inventory.find(query, {"all_attributes": 1, "gsisk_id": 1}))

            matched_values = [
                [
                    item['all_attributes']['cmpt_id'],
                    item['all_attributes']["mfr_prt_num"],
                    category_metadata[item['all_attributes']['ctgr_id']]['category_name'],
                    item['all_attributes']["description"]
                ]
                for item in db
                if category_name.lower() in str(item['all_attributes']["mfr_prt_num"]).lower()
                   or category_name.lower() in item['gsisk_id'].lower()
                   or category_name.lower() in item['all_attributes']["description"].lower()
                   or category_name.lower() in category_metadata[item['all_attributes']['ctgr_id']][
                       'category_name'].lower()

            ]
            if len(matched_values):
                return {'statusCode': 200, 'body': matched_values}
            else:
                return {'statusCode': 400, 'body': "no data found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': "Internal server error"}



    def CmsInventorySearchComponentInPO(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # print(data)
            env_type = data.get("env_type", "")
            databaseTableName = f"PtgCms{env_type}"
            Inventory_table = 'Inventory'
            metadata_table = 'Metadata'

            metadata = list(db_con.Metadata.find({}))

            inventory = list(db_con.Inventory.find({}, {"pk_id": 1, "all_attributes.description": 1,
                                                        "all_attributes.package": 1, "all_attributes.mfr": 1,
                                                        "all_attributes.cmpt_id": 1, "all_attributes.prdt_name": 1,
                                                        "all_attributes.department": 1, "all_attributes.sub_ctgr": 1}))
            # print(inventory)
            inventory = {item["pk_id"]: item for item in inventory}
            # print(inventory)
            category_metadata = {item['pk_id'].replace("MDID", "CTID"): {"category_name": item['gsisk_id']} for item in
                                 metadata}

            query = {"gsipk_id": "Electronic"}
            category_data = list(db_con.Metadata.find(query, {"pk_id": 1, "sub_categories": 1}))
            category_data = {
                item['pk_id'].replace("MDID", "CTID"): {key: value for key, value in item['sub_categories'].items()} for
                item in category_data}

            projection = {
                "all_attributes.cmpt_id": 1,
                "all_attributes.ctgr_id": 1,
                "all_attributes.ctgr_name": 1,
                "all_attributes.manufacturer": 1,
                "all_attributes.package": 1,
                "all_attributes.department": 1,
                "all_attributes.description": 1,
                "all_attributes.mfr_prt_num": 1,
                "all_attributes.sub_ctgr": 1,
                "all_attributes.prdt_name": 1,
                "gsisk_id": 1
            }
            db = list(
                db_con.Inventory.find({"gsipk_table": "Inventory", "all_attributes.cmpt_id": data["component_id"]},
                                      projection))

            db = db[0]
            # print(db)
            if db:
                # print(db["all_attributes"]['cmpt_id'])
                result = {
                    'cmpt_id': db["all_attributes"]['cmpt_id'],
                    'ctgr_id': db["all_attributes"]['ctgr_id'],
                    'manufacturer': db["all_attributes"].get('manufacturer', '-'),
                    'ctgr_name': category_metadata[db["all_attributes"]['ctgr_id']]['category_name'],
                    'department': db["all_attributes"]['department'],
                    'packaging': db["all_attributes"].get('package', ' '),
                    'description': db["all_attributes"]['description'],
                    "mfr_prt_num": db["all_attributes"].get('mfr_prt_num', '-'),
                    'prdt_name': category_data[db["all_attributes"]['ctgr_id']][
                        inventory[db["all_attributes"]['cmpt_id']]["all_attributes"]['sub_ctgr']] if
                    inventory[db["all_attributes"]['cmpt_id']]["all_attributes"]['department'] == 'Electronic' else db[
                        "all_attributes"].get('prdt_name', ''),
                    'qty': '1',
                    'price': ''
                }
                return {"statusCode": 200, "body": result}
            else:
                return {"statusCode": 400, "body": "No Data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}


    
    def cmsPurchaseOrderInwardGetAllDetailsForModal(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']

        inwardId = data['inward_id']
        env_type = data.get("env_type", "")
        if env_type:
            databaseTableName = f"PtgCms{env_type}"
            gsipk_table = data['status']

            date_today = datetime.today()

            # Query to fetch data for inward
            inward_query = {"all_attributes.inwardId": inwardId, "gsipk_table": gsipk_table}
            result = db_con[gsipk_table].find_one(inward_query)

            response = {}
            geq = {}
            if result:

                # Fetch data for GateEntry if gsipk_table is not 'GateEntry'
                if gsipk_table != 'GateEntry':
                    gateentry_query = {"pk_id": inwardId}
                    gateentry = db_con.GateEntry.find_one(gateentry_query)
                    if gateentry:
                        response['receiver_name'] = gateentry["all_attributes"].get('rec_name', "--")
                        response['receiver_contact'] = gateentry["all_attributes"].get('rec_cont', "--")
                        geq = {gateentry["all_attributes"]['parts'][key]['cmpt_id']:
                            gateentry["all_attributes"]['parts'][key]['received_qty'] for key in
                            gateentry["all_attributes"]['parts'].keys()}
                    else:
                        return {"statusCode": 400, "body": ""}

                else:
                    response['receiver_name'] = result['all_attributes'].get('rec_name', '--')
                    response['receiver_contact'] = result['all_attributes'].get('rec_cont', '--')
                    _parts = result["all_attributes"]["parts"]
                    geq = {
                        _parts[key]["cmpt_id"]: _parts[key]["received_qty"]
                        for key in _parts.keys()
                    }
                response['inward_id'] = inwardId
                # response['description'] = result['all_attributes']['description']
                response['description'] = result['all_attributes'].get('description', "--")
                response['sender_name'] = result['all_attributes']['sender_name']
                response['sender_contact_number'] = result['all_attributes']['sender_contact_number']
                response['gate_entry_date'] = result['all_attributes']['gate_entry_date']
                response['qa_date'] = result['all_attributes'].get("QA_date", "-")
                response['inward_date'] = result['all_attributes'].get("inward_date", "-")

                response['qa_document'] = file_get(result['all_attributes'].get("QATest", ""))
                response['invoice'] = file_get(result['all_attributes'].get("invoice", ""))
                response['photo'] = {i: file_get(result['all_attributes']['photo'][i]) for i in
                                    result['all_attributes']['photo']}
                response['qa_document_name'] = result['all_attributes'].get("QATest", "").split("/")[-1]
                response['invoice_name'] = result['all_attributes'].get("invoice", "").split("/")[-1]

                # Filter and add only CSV files to the excel field
                # if inward == status:
                # csv_files = [
                #     {"name": file["name"], "url": file_get(file["url"])}
                #     for file in result['all_attributes'].get("excel", [])
                #     if file["name"].endswith('.csv') or file["name"].endswith('.xls') or file["name"].endswith('.xlsx')
                # ]
                # response['excel'] = csv_files
                r = result.get('all_attributes',{}).get('excel', {})
                if r:
                    files = [
                    {"name": key, "url": value}
                    for key, value in result['all_attributes']['excel'].items()
                    if key.endswith('.csv') or key.endswith('.xls') or key.endswith('.xlsx') or key.endswith('.pdf')
                    ]
                    response['excel'] = files
                else:
                    csv_files = [
                    {"name": key, "url": file_get(value)}
                    for key, value in result['all_attributes'].items()
                    if key.endswith('.csv') or key.endswith('.xls') or key.endswith('.xlsx') or key.endswith('.pdf')
                    ]
                    response['excel'] = csv_files
                # files = [
                # {"name": key, "url": value}
                # for key, value in result['all_attributes']['excel'].items()
                # if key.endswith('.csv') or key.endswith('.xls') or key.endswith('.xlsx') or key.endswith('.pdf')
                # ]
                # response['excel'] = csv_files
                # response['files'] = files
            
                

                category_query = {"gsipk_table": 'Metadata'}
                category_result = list(db_con.Metadata.find(category_query))
                category = {
                    item['pk_id'].replace("MDID", "CTID"): (
                        {
                            "ctgr_name": item['gsisk_id'],
                            "sub_categories": {
                                key: value for key, value in item['sub_categories'].items()
                            }
                        }
                        if item['gsipk_id'] == 'Electronic'
                        else {"ctgr_name": item['gsisk_id']}
                    )
                    for item in category_result
                }

                Parts = []
                total_quantity = 0
                for part in result['all_attributes']['parts']:
                    part_info = result['all_attributes']['parts'][part]
                    if gsipk_table == 'GateEntry':
                        if int(result['all_attributes']['parts'][part].get('received_qty', '0')) == 0:
                            continue
                    inventory_table = 'Inventory'
                    part_query = {"gsipk_table": inventory_table, "all_attributes.cmpt_id": part_info['cmpt_id']}
                    part_data = db_con[inventory_table].find_one(part_query)
                    if part_data:
                        total_quantity += int(part_info.get("qty", "0"))
                        Parts.append(
                            {
                                "s_no": part.replace("part", ""),
                                "cmpt_id": part_data['all_attributes']['cmpt_id'],
                                "part_no": part_data['all_attributes']['mfr_prt_num'],
                                "part_name": category[part_data['all_attributes']['ctgr_id']]["sub_categories"][
                                    part_data['all_attributes']['sub_ctgr']] if part_data['all_attributes'][
                                'department'] == 'Electronic' else
                                part_data['all_attributes']['prdt_name'],
                                "description": part_data['all_attributes']['description'],
                                "manufacturer": part_data['all_attributes'].get('mfr', "-"),
                                "packaging": part_data['all_attributes'].get('package', ""),
                                "quantity": part_info.get("qty", "0"),
                                "pass_quantity": part_info.get("pass_qty", ""),
                                "fail_quantity": part_info.get("fail_qty", ""),
                                'gate_entry_qty': geq.get(part_data['all_attributes']['cmpt_id'], '0'),
                                "inventory_position": part_info.get("inventory_position", ""),
                                "lot_id": part_info.get("lot_id","-"),
                                "batch_no": part_info.get("batchId", "")
                            }
                        )
                Parts = sorted(Parts, key=lambda x: int(x['s_no']))
                response['parts'] = Parts
                response['total_quantity'] = total_quantity
                return {'statusCode': 200, 'body': response}
            else:
                return {'statusCode': 200, 'body': "No data found"}
        else:
            return {"statusCode": 400, "body": "something went wrong, please try again"}




    # def cmsPurchaseOrderInwardGetAllDetailsForModal(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     # print(data)

    #     inwardId = data['inward_id']
    #     env_type = data.get("env_type", "")
    #     if env_type:
    #         databaseTableName = f"PtgCms{env_type}"
    #         gsipk_table = data['status']

    #         date_today = datetime.today()

    #         # Query to fetch data for inward
    #         inward_query = {"all_attributes.inwardId": inwardId, "gsipk_table": gsipk_table}
    #         result = db_con[gsipk_table].find_one(inward_query)
    #         print(result)
    #         response = {}
    #         geq = {}
    #         if result:
    #             # Fetch data for GateEntry if gsipk_table is not 'GateEntry'
    #             if gsipk_table != 'GateEntry':
    #                 gateentry_query = {"pk_id": inwardId}
    #                 gateentry = db_con.GateEntry.find_one(gateentry_query)
    #                 # print(gateentry)
    #                 if gateentry:
    #                     response['receiver_name'] = gateentry["all_attributes"].get('rec_name', "--")
    #                     response['receiver_contact'] = gateentry["all_attributes"].get('rec_cont', "--")
    #                     geq = {gateentry["all_attributes"]['parts'][key]['cmpt_id']:
    #                                gateentry["all_attributes"]['parts'][key]['received_qty'] for key in
    #                            gateentry["all_attributes"]['parts'].keys()}
    #                     # return gateentry['all_attributes']['parts']
    #                 else:
    #                     return {"statusCode": 400, "body": ""}

    #             else:
    #                 response['receiver_name'] = result['all_attributes'].get('rec_name', '--')
    #                 response['receiver_contact'] = result['all_attributes'].get('rec_cont', '--')
    #                 _parts = result["all_attributes"]["parts"]
    #                 geq = {
    #                     _parts[key]["cmpt_id"]: _parts[key]["received_qty"]
    #                     for key in _parts.keys()
    #                 }
    #             response['inward_id'] = inwardId
    #             response['sender_name'] = result['all_attributes']['sender_name']
    #             response['sender_contact_number'] = result['all_attributes']['sender_contact_number']
    #             response['description']=result['all_attributes'].get('description'," ")
    #             response['gate_entry_date'] = result['all_attributes']['gate_entry_date']
    #             response['qa_date'] = result['all_attributes'].get("QA_date", "-")
    #             response['inward_date'] = result['all_attributes'].get("inward_date", "-")

    #             response['qa_document'] = file_get((result['all_attributes'].get("QATest", "")))
    #             response['invoice'] = file_get(result['all_attributes'].get("invoice", ""))
    #             response['photo'] = {i: file_get(result['all_attributes']['photo'][i]) for i in
    #                                  result['all_attributes']['photo']}
    #             response['qa_document_name'] = result['all_attributes'].get("QATest", "").split("/")[-1]
    #             response['invoice_name'] = result['all_attributes'].get("invoice", "").split("/")[-1]

    #             csv_files = [
    #                 {"name": key, "url": file_get(value)}
    #                 for key, value in result['all_attributes'].items()
    #                 if key.endswith('.csv') or key.endswith('.xls') or key.endswith('.xlsx') or key.endswith('.pdf')
    #             ]
    #             response['excel'] = csv_files

    #             category_query = {"gsipk_table": 'Metadata'}
    #             category_result = list(db_con.Metadata.find(category_query))
    #             category = {
    #                 item['pk_id'].replace("MDID", "CTID"): (
    #                     {
    #                         "ctgr_name": item['gsisk_id'],
    #                         "sub_categories": {
    #                             key: value for key, value in item['sub_categories'].items()
    #                         }
    #                     }
    #                     if item['gsipk_id'] == 'Electronic'
    #                     else {"ctgr_name": item['gsisk_id']}
    #                 )
    #                 for item in category_result
    #             }

    #             Parts = []
    #             total_quantity = 0
    #             for part in result['all_attributes']['parts']:
    #                 part_info = result['all_attributes']['parts'][part]
    #                 if gsipk_table == 'GateEntry':
    #                     if int(result['all_attributes']['parts'][part].get('received_qty', '0')) == 0:
    #                         continue
    #                 inventory_table = 'Inventory'
    #                 part_query = {"gsipk_table": inventory_table, "all_attributes.cmpt_id": part_info['cmpt_id']}
    #                 part_data = db_con[inventory_table].find_one(part_query)
    #                 if part_data:
    #                     total_quantity += int(part_info.get("qty", "0"))
    #                     Parts.append(
    #                         {
    #                             "s_no": part.replace("part", ""),
    #                             "cmpt_id": part_data['all_attributes']['cmpt_id'],
    #                             "part_no": part_data['all_attributes']['mfr_prt_num'],
    #                             "part_name": category[part_data['all_attributes']['ctgr_id']]["sub_categories"][
    #                                 part_data['all_attributes']['sub_ctgr']] if part_data['all_attributes'][
    #                                                                                 'department'] == 'Electronic' else
    #                             part_data['all_attributes']['prdt_name'],
    #                             "description": part_data['all_attributes']['description'],
    #                             "manufacturer": part_data['all_attributes'].get('mfr', "-"),
    #                             "packaging": part_data['all_attributes'].get('package', ""),
    #                             "quantity": part_info.get("qty", "0"),
    #                             "pass_quantity": part_info.get("pass_qty", ""),
    #                             "fail_quantity": part_info.get("fail_qty", ""),
    #                             # "lot_id": part_info.get("lot_id",""),
    #                             "lot_id": part_info.get("lot_id","-"),
    #                             'gate_entry_qty': geq.get(part_data['all_attributes']['cmpt_id'], '0'),
    #                             "inventory_position": part_info.get("inventory_position", ""),
    #                             "batch_no": part_info.get("batchId", "")
    #                         }
    #                     )
    #             Parts = sorted(Parts, key=lambda x: int(x['s_no']))
    #             response['parts'] = Parts
    #             response['total_quantity'] = total_quantity
    #             return {'statusCode': 200, 'body': response}
    #         else:
    #             return {'statusCode': 200, 'body': "No data found"}
    #     else:
    #         return {"statusCode": 400, "body": "something went wrong, please try agian"}

    def cmsPurchaseOrderInwardCategoryInfoGetDetails(request_body):
        data = request_body
        # print(data)
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        purchaseOrder = data["po_id"]
        final_result = []
        inward_ids = []

        # Querying for dataInward
        dataInward = list(db_con.inward.find({"gsisk_id": purchaseOrder, "lsi_key": "status_inward"}))
        if dataInward:
            final_result.extend(dataInward)
            inward_ids = [item['all_attributes']['inwardId'] for item in dataInward]

        # Querying for QATest
        data = list(db_con.QATest.find({"gsisk_id": purchaseOrder}))
        if data:
            [final_result.append(item) for item in data if item['all_attributes']['inwardId'] not in inward_ids]
            [inward_ids.append(item['all_attributes']['inwardId']) for item in data]

        # Querying for GateEntry
        pending = "QA_test"
        dataEntry = list(db_con.GateEntry.find({"gsisk_id": purchaseOrder, "all_attributes.actions": pending}))
        if dataEntry:
            [final_result.append(item) for item in dataEntry if item['all_attributes']['inwardId'] not in inward_ids]
        # print()
        lst = []
        # print(final_result)
        if final_result:
            for i in final_result:
                # return i
                no_of_parts = len([1 for item in i["all_attributes"]["parts"].values() if
                                   (i["gsipk_table"] == 'GateEntry' and item['received_qty'] != '0') or (
                                               i["gsipk_table"] == 'QATest' and item.get('pass_qty') != '0') or (
                                               i["gsipk_table"] == 'inward')])
                # return no_of_parts
                dt = {}
                status = 1
                if i.get("gsipk_table", "") == 'QATest':
                    status = sum(int(i["all_attributes"]["parts"][key]['pass_qty']) for key in
                                 i["all_attributes"]["parts"].keys())
                    dt["pass_qty"] = \
                    [(i["all_attributes"]["parts"][key]['pass_qty']) for key in i["all_attributes"]["parts"]][0]
                    dt["fail_qty"] = \
                    [(i["all_attributes"]["parts"][key]['fail_qty']) for key in i["all_attributes"]["parts"]][0]
                    # no_of_parts = len(i["all_attributes"]["parts"])
                # if i.get
                dt["inward_id"] = i["all_attributes"]["inwardId"]
                # dt["no_of_parts"] = len(i["all_attributes"]["parts"])
                dt["no_of_parts"] = no_of_parts
                dt["gate_entry_date"] = i["all_attributes"]["gate_entry_date"]
                dt["QA_date"] = str(i["all_attributes"].get("QA_date", "").split(" ")[0])
                dt["status"] = i.get("gsipk_table", "")
                dt["inward_date"] = i["all_attributes"].get("inward_date", "")
                dt["invoice"] = file_get(i["all_attributes"].get("invoice", ""))
                dt["invoice_name"] = (i["all_attributes"].get("invoice", "")).split("/")[-1]
                dt["QA_document"] = file_get(i["all_attributes"].get("QATest", ""))
                dt["QA_document_name"] = (i["all_attributes"].get("QATest", "")).split("/")[-1]
                dt["actions"] = i["all_attributes"]["actions"]
                dt['btn'] = status
                lst.append(dt)
            lst=sorted(lst, key=lambda x: x["gate_entry_date"], reverse=True)
            return {'statusCode': 200, 'body': lst}
        else:
            return {'statusCode': 400, 'body': []}

    
    def cmsPurchaseOrdersInwardGetDetailsbyId(request_body):
        try:
            data = request_body  # test
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            po_id = data['po_id']
            inward_id = data['inward_id']
            collection = db_con['QATest']
            po_tablename = 'purchaseOrder'
            inward_tablename = 'QATest'

            result = list(db_con.QATest.find({"all_attributes.inwardId": inward_id}))
            parts = []

            if result:
                category = list(
                    db_con.Metadata.find({}, {"pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1}))
                category = {
                    item['pk_id'].replace("MDID", "CTID"): (
                        {
                            "ctgr_name": item['gsisk_id'],
                            "sub_categories": {
                                key: value for key, value in item['sub_categories'].items()
                            }
                        }
                        if item['gsipk_id'] == 'Electronic'
                        else {"ctgr_name": item['gsisk_id']}
                    )
                    for item in category
                }

                inventory = list(db_con.Inventory.find({}, {"pk_id": 1, "all_attributes.description": 1,
                                                            "all_attributes.package": 1, "all_attributes.mfr": 1,
                                                            "all_attributes.cmpt_id": 1,
                                                            "all_attributes.prdt_name": 1,
                                                            "all_attributes.department": 1,
                                                            "all_attributes.sub_ctgr": 1}))
                inventory = {item['pk_id']: item for item in inventory}
                response = {}
                response['order_no'] = po_id
                response['QA_id'] = result[0]['pk_id']
                response['inward_id'] = result[0]['all_attributes'].get('inwardId', "")
                response['vendor_id'] = result[0]['all_attributes'].get('vendorId', "")
                response['order_date'] = result[0]['all_attributes'].get('gate_entry_date', "")
                response['description'] = result[0]['all_attributes'].get('description', "")
                response['invoice'] = file_get(result[0]['all_attributes'].get('invoice', ""))
                response['invoice_num'] = result[0]['all_attributes'].get('invoice_num', "")
                response['qa_date'] = result[0]['all_attributes'].get('QA_date', "")
                response['invoice_name'] = result[0]['all_attributes'].get('invoice', "").split("/")[-1] if \
                    result[0]['all_attributes'].get('invoice', "") else ""
                response['invoice_photo'] = {i: file_get(result[0]['all_attributes']['photo'][i]) for i in
                                            result[0]['all_attributes']['photo']}
                response['qa_test_document'] = file_get(result[0]['all_attributes'].get('QATest', ""))
                response['qa_test_document_name'] = result[0]['all_attributes'].get('QATest', "").split("/")[-1] if \
                    result[0]['all_attributes'].get('QATest', "") else ""

                for key in result[0]['all_attributes']['parts'].keys():
                    part_info = result[0]['all_attributes']['parts'][key]
                    cmpt_id = part_info['cmpt_id']
                    ctgr_id = part_info['ctgr_id']
                    if part_info['pass_qty'] != '0':
                        parts.append(
                            {
                                "s_no": key.replace("part", ""),
                                "cmpt_id": part_info['cmpt_id'],
                                "ctgr_id": part_info['ctgr_id'],
                                "manufacturer": inventory[part_info['cmpt_id']].get('mfr',
                                                                                    part_info['manufacturer']),
                                "part_no": part_info['mfr_prt_num'],
                                "part_name": category[ctgr_id]['sub_categories'][
                                    inventory[cmpt_id]["all_attributes"]['sub_ctgr']] if
                                inventory[cmpt_id]["all_attributes"]['department'] == 'Electronic' else
                                inventory[cmpt_id]["all_attributes"]['prdt_name'],
                                "description": inventory[part_info['cmpt_id']].get('description',
                                                                                part_info['description']),
                                "packaging": inventory[part_info['cmpt_id']].get('package', part_info['packaging']),
                                "quantity": part_info['qty'],
                                "pass_qty": part_info['pass_qty'],
                                "fail_qty": part_info['fail_qty'],
                                "inventory_position": "",
                                "batchId": part_info.get('batchId', ""),
                                "lot_id": part_info.get("lot_id", "-")
                            }
                        )
                response['parts'] = parts

                # Add excel files
                excel_files = []
                for key, value in result[0]['all_attributes'].items():
                    if key.endswith('.csv') or key.endswith('.pdf')or key.endswith('.xls')or key.endswith('.xlsx'):
                        excel_files.append({
                            "name": key,
                            "url": value
                        })
                response['excel'] = excel_files

                return {'statusCode': 200, 'body': response}
            else:
                return {'statusCode': 200, 'body': "No data found"}
        # else:
        #     return {"statusCode": 400, "body": "Something went wrong, please try again"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {"statusCode": 400, "body": "Internal server error"}





    # def cmsPurchaseOrdersInwardGetDetailsbyId(request_body):
    #     try:
    #         data = request_body #test
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         # print(data)
    #         env_type = data.get("env_type", "")
    #         if env_type:
    #             # databaseTableName = f"PtgCms{env_type}"
    #             po_id = data['po_id']
    #             inward_id = data['inward_id']
    #             collection = db_con['QATest']
    #             po_tablename = 'purchaseOrder'
    #             inward_tablename = 'QATest'

    #             result = list(db_con.QATest.find({"all_attributes.inwardId": inward_id}))
    #             parts = []
    #             # print(result)
    #             if result:

    #                 category = list(
    #                     db_con.Metadata.find({}, {"pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1}))
    #                 category = {
    #                     item['pk_id'].replace("MDID", "CTID"): (
    #                         {
    #                             "ctgr_name": item['gsisk_id'],
    #                             "sub_categories": {
    #                                 key: value for key, value in item['sub_categories'].items()
    #                             }
    #                         }
    #                         if item['gsipk_id'] == 'Electronic'
    #                         else {"ctgr_name": item['gsisk_id']}
    #                     )
    #                     for item in category
    #                 }

    #                 inventory = list(db_con.Inventory.find({}, {"pk_id": 1, "all_attributes.description": 1,
    #                                                             "all_attributes.package": 1, "all_attributes.mfr": 1,
    #                                                             "all_attributes.cmpt_id": 1,
    #                                                             "all_attributes.prdt_name": 1,
    #                                                             "all_attributes.department": 1,
    #                                                             "all_attributes.sub_ctgr": 1}))
    #                 # print(inventory)
    #                 # print("------------------------")
    #                 inventory = {item['pk_id']: item for item in inventory}
    #                 pattern = r"^Part\d+$"
    #                 response = {}
    #                 response['order_no'] = po_id
    #                 response['QA_id'] = result[0]['pk_id']
    #                 response['inward_id'] = result[0]['all_attributes'].get('inwardId', "")
    #                 response['vendor_id'] = result[0]['all_attributes'].get('vendorId', "")
    #                 response['order_date'] = result[0]['all_attributes'].get('gate_entry_date', "")
    #                 response['description'] = result[0]['all_attributes'].get('description', "")
    #                 response['invoice'] = file_get(result[0]['all_attributes'].get('invoice', ""))
    #                 response['invoice_num'] = result[0]['all_attributes'].get('invoice_num', "")
    #                 response['qa_date'] = result[0]['all_attributes'].get('QA_date', "")
    #                 response['invoice_name'] = result[0]['all_attributes'].get('invoice', "").split("/")[-1] if \
    #                 result[0]['all_attributes'].get('invoice', "") else ""
    #                 response['invoice_photo'] = {i: file_get(result[0]['all_attributes']['photo'][i]) for i in
    #                                              result[0]['all_attributes']['photo']}
    #                 response['qa_test_document'] = file_get(result[0]['all_attributes'].get('QATest', ""))
    #                 response['qa_test_document_name'] = result[0]['all_attributes'].get('QATest', "").split("/")[-1] if \
    #                 result[0]['all_attributes'].get('QATest', "") else ""
    #                 # print(inventory)
    #                 for key in result[0]['all_attributes']['parts'].keys():
    #                     part_info = result[0]['all_attributes']['parts'][key]
    #                     cmpt_id = part_info['cmpt_id']
    #                     ctgr_id = part_info['ctgr_id']
    #                     if part_info['pass_qty'] != '0':
    #                         parts.append(
    #                             {
    #                                 "s_no": key.replace("part", ""),
    #                                 "cmpt_id": part_info['cmpt_id'],
    #                                 "ctgr_id": part_info['ctgr_id'],
    #                                 "manufacturer": inventory[part_info['cmpt_id']].get('mfr',
    #                                                                                     part_info['manufacturer']),
    #                                 "part_no": part_info['mfr_prt_num'],
    #                                 "part_name": category[ctgr_id]['sub_categories'][
    #                                     inventory[cmpt_id]["all_attributes"]['sub_ctgr']] if
    #                                 inventory[cmpt_id]["all_attributes"]['department'] == 'Electronic' else
    #                                 inventory[cmpt_id]["all_attributes"]['prdt_name'],
    #                                 "description": inventory[part_info['cmpt_id']].get('description',
    #                                                                                    part_info['description']),
    #                                 "packaging": inventory[part_info['cmpt_id']].get('package', part_info['packaging']),
    #                                 "quantity": part_info['qty'],
    #                                 "pass_qty": part_info['pass_qty'],
    #                                 "fail_qty": part_info['fail_qty'],
    #                                 "inventory_position": "",
    #                                 "batchId": part_info.get('batchId', ""),
    #                                 "lot_id": part_info.get("lot_id", "-")

    #                             }
    #                         )
    #                 response['parts'] = parts
    #                 return {'statusCode': 200, 'body': response}
    #             else:
    #                 return {'statusCode': 200, 'body': "No data found"}
    #         else:
    #             return {"statusCode": 400, "body": "something went wrong, please try agian"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {"statusCode": 400, "body": "Internal server error"}

    def CmsVendorGetDetailsById(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            vendor_id = data["vendor_id"]
            vendor_name = data["vendor_name"]
            gsipk_table = "Vendor"
            status = "Active"
            # MongoDB query construction
            query = {
                "gsipk_table": gsipk_table,
                "lsi_key": status,
                "all_attributes.vendor_id": vendor_id,
                "all_attributes.vendor_name": vendor_name
            }
            # Execute the query in MongoDB (assuming your MongoDB connection is set up)
            result = db_con[gsipk_table].find(query)
            if result:
                part_info = [part['parts'] for part in result['all_attributes'].values()]
                return {"statusCode": 200, "body": part_info}
            else:
                return {"statusCode": 400, "body": []}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}

    def CmsPurchaseOrderGetStatus(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            if data['status'] == 'Create':
                return {'statusCode': 200,'body': ["PO Generated", "PO Issued"]}
            else:
                try:
                    po_id = data["po_id"]
                    databaseTableName = f"PtgCms{data['env_type']}"
                    status_list = ["PO Generated", "PO Issued", "Vendor Acknowledged", "Partially Received", "Received",
                                   "Cancel"]
                    result = list(db_con.PurchaseOrder.find({"pk_id": po_id}, {"all_attributes.status": 1}))
                    if result:
                        order_status = result[0]["all_attributes"]['status']
                        inx = [inx for inx, item in enumerate(status_list) if order_status == item]
                        return {'statusCode': 200, 'body': status_list[inx[0] + 1:]}
                    else:
                        return {'statusCode': 400, 'body': "details not found for the order"}
                except:
                    return {'statusCode': 400, 'body': "Bad request"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}


    def CmsPurchaseOrderSaveInward(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            gsipk_table = "inward"
            inward_query = {"gsipk_table": gsipk_table}
            inward_data = db_con[gsipk_table].find_one(inward_query)
            inwardedId = data['inward_id'].split("IN")[-1]
            gate_id = data["inward_id"]
            
            # QUERY TO FETCH GATE ENTRY DATA
            gate_entry_query = {"gsipk_table": "GateEntry", "pk_id": gate_id}
            gate_entry_data = db_con["GateEntry"].find_one(gate_entry_query)
            gate_id_timestamp = gate_entry_data["sk_timeStamp"]
            
            gsipk_table1 = "QATest"
            QA_id = data["QA_id"]
            po_id = data["order_no"]
            
            # QUERY TO FETCH DATA FOR QA TEST
            QA_query = {"gsipk_table": gsipk_table1, "pk_id": QA_id, "all_attributes.po_id": po_id}
            poData = list(db_con[gsipk_table1].find(QA_query))
            
            activity = {}
            activity_id = (db_con.all_tables.find_one({"pk_id":"top_ids"},{"_id":0,"all_attributes.ActivityId":1}))
            activity_id = int(activity_id['all_attributes'].get('ActivityId','0')) + 1
            
            invent_data = list(db_con["Inventory"].find({}))
            invent_data = {item['pk_id']:item['all_attributes'] for item in invent_data}
            
            if poData:
                parts = []
                for po_item in poData:
                    po_parts = po_item.get("all_attributes", {}).get("parts", [])
                    for part_key, part_data in po_parts.items():
                        for data_part in data.get("parts", []):
                            if part_data.get("mfr_prt_num", "") == data_part.get("part_no", ""):
                                batchId = data_part.get("batchId", "")
                                part = {
                                    "mfr_prt_num": part_data.get("mfr_prt_num", "-"),
                                    "cmpt_id": part_data.get("cmpt_id", ""),
                                    "ctgr_id": part_data.get("ctgr_id", ""),
                                    "prdt_name": part_data.get("prdt_name", ""),
                                    "description": part_data.get("description", ""),
                                    "packaging": part_data.get("packaging", ""),
                                    "inventory_position": data_part.get("inventory_position", ""),
                                    "qty": data_part.get("quantity", ""),
                                    "pass_qty": data_part.get("pass_qty", ""),
                                    "fail_qty": data_part.get("fail_qty", ""),
                                    "batchId": data_part.get("batchId", ""),
                                    "lot_no": data_part.get("lot_no", "testlot"),
                                    "lot_id": data_part.get("lot_id", "-")
                                }
                                parts.append(part)
                                activity[part_data.get("cmpt_id", "")] = {
                                    "mfr_prt_num": part_data.get("mfr_prt_num", "-"),
                                    "date": str(date.today()),
                                    "action": "Purchased",
                                    "Description": "Purchased",
                                    "issued_to": "Peopletech Group",
                                    "po_no": po_id,
                                    "invoice_no": data["invoice_num"],
                                    "cmpt_id": part_data.get("cmpt_id", ""),
                                    "ctgr_id": part_data.get("ctgr_id", ""),
                                    "prdt_name": part_data.get("prdt_name", ""),
                                    "description": part_data.get("description", ""),
                                    "packaging": part_data.get("packaging", ""),
                                    "closing_qty": f"{int(invent_data[part_data['cmpt_id']]['qty']) + int(data_part.get('pass_qty', '0'))}",
                                    "qty": data_part.get("pass_qty", ""),
                                    "batchId": data_part.get("batchId", ""),
                                    "used_qty": "0",
                                    "lot_no": data_part.get("lot_no", "testlot")
                                }
                
                all_attributes = {
                    "parts": {f'part{i + 1}': parts[i] for i in range(len(parts))},
                    "vendor_id": data["vendor_id"],
                    "order_date": data["order_date"],
                    "description": data["description"],
                    "sk_timeStamp": sk_timeStamp,
                    "inward_date": sk_timeStamp[:10],
                    "po_id": po_id,
                    "gate_entry_date": poData[0]["all_attributes"]["gate_entry_date"],
                    "inwardId": poData[0]["all_attributes"]["inwardId"],
                    "QA_date": poData[0]["all_attributes"]["QA_date"],
                    "sender_contact_number": poData[0]["all_attributes"]["sender_contact_number"],
                    "sender_name": poData[0]["all_attributes"]["sender_name"],
                    "actions": 'inwarded',
                    "invoice_num": data["invoice_num"],
                    "invoice": file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, po_id, po_id.replace("OPTG", ''), "invoice.pdf", data["invoice"]),
                    "QATest": file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, po_id, po_id.replace("OPTG", ''), "QATest.pdf", data["qa_test_document"]),
                    "batchId": batchId
                }
                
                photo = {}
                for key, doc in data["invoice_photo"].items():
                    photo[key] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, po_id, po_id.replace("OPTG", ''), key, doc)
                
                all_attributes["photo"] = photo
                
                excel_files = []
                files = {}
                for excel_file in data.get("excel", []):
                    excel_files.append({
                        "name": excel_file["name"],
                        "url": excel_file["url"]
                    })
                    files[f'{excel_file["name"]}'] = excel_file["url"]
                
                all_attributes["excel"] = files
                # all_attributes["files"] = files
                
                item = {
                    "pk_id": po_id + "_INWARDId" + inwardedId,
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": all_attributes,
                    "gsipk_table": gsipk_table,
                    "gsisk_id": po_id,
                    "lsi_key": "status_inward"
                }
                
                # UPDATING INVENTORY QUANTITIES
                for part in parts:
                    cmpt_id = part["cmpt_id"]
                    invent_query = {"pk_id": cmpt_id}
                    invent_data = dict(db_con["Inventory"].find_one(invent_query))
                    qty = str(int(part["pass_qty"]) + int(invent_data["all_attributes"]["qty"]))
                    db_con["Inventory"].update_one(invent_query, {"$set": {"all_attributes.qty": qty}})
                
                # INSERTING INWARDED ITEM
                db_con[gsipk_table].insert_one(item)
                
                # UPDATING QA TEST AND GATE ENTRY RECORDS
                db_con["QATest"].update_one(
                    {"pk_id": QA_id, "sk_timeStamp": poData[0]["sk_timeStamp"]},
                    {"$set": {"lsi_key": "status_inward"}}
                )
                
                db_con["GateEntry"].update_one(
                    {"pk_id": gate_id, "sk_timeStamp": gate_id_timestamp},
                    {"$set": {"all_attributes.invoice_num": data["invoice_num"]}}
                )
                
                db_con['ActivityDetails'].insert_one(
                    {
                        "pk_id": f"ACTID{activity_id}",
                        "sk_timeStamp": sk_timeStamp,
                        "all_attributes": activity,
                        "gsipk_table": "ActivityDetails",
                        "gsisk_id": po_id,
                        "lsi_key": "Purchased"
                    }
                )
                
                db_con['all_tables'].update_one(
                    {"pk_id": 'top_ids'},
                    {"$set": {"all_attributes.ActivityId": str(activity_id)}}
                )
                
                response = {'statusCode': 200, 'body': 'inwarded added successfully'}
            else:
                response = {'statusCode': 404, 'body': 'data not found'}
            return response
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}




    # def CmsPurchaseOrderSaveInward(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         gsipk_table = "inward"
    #         inward_query = {"gsipk_table": gsipk_table}
    #         inward_data = db_con[gsipk_table].find_one(inward_query)
    #         inwardedId = data['inward_id'].split("IN")[-1]
    #         gate_id = data["inward_id"]
    #         # QUERY TO FETCH GATE ENTRY DATA
    #         gate_entry_query = {"gsipk_table": "GateEntry", "pk_id": gate_id}
    #         gate_entry_data = db_con["GateEntry"].find_one(gate_entry_query)
    #         gate_id_timestamp = gate_entry_data["sk_timeStamp"]
    #         gsipk_table1 = "QATest"
    #         QA_id = data["QA_id"]
    #         po_id = data["order_no"]
    #         # QUERY TO FETCH DATA FOR QA TEST
    #         QA_query = {"gsipk_table": gsipk_table1, "pk_id": QA_id, "all_attributes.po_id": po_id}
    #         poData = list(db_con[gsipk_table1].find(QA_query))
    #         activity = {}
    #         activity_id = (db_con.all_tables.find_one({"pk_id":"top_ids"},{"_id":0,"all_attributes.ActivityId":1}))
    #         activity_id = int(activity_id['all_attributes'].get('ActivityId','0'))+1
    #         invent_data = list(db_con["Inventory"].find({}))
    #         invent_data = {item['pk_id']:item['all_attributes'] for item in invent_data}
    #         if poData:
    #             parts = []
    #             for po_item in poData:
    #                 po_parts = po_item.get("all_attributes", {}).get("parts", [])
    #                 for part_key, part_data in po_parts.items():
    #                     for data_part in data.get("parts", []):
    #                         if part_data.get("mfr_prt_num", "") == data_part.get("part_no", ""):
    #                             batchId = data_part.get("batchId", "")
    #                             part = {
    #                                 "mfr_prt_num": part_data.get("mfr_prt_num", "-"),
    #                                 "cmpt_id": part_data.get("cmpt_id", ""),
    #                                 "ctgr_id": part_data.get("ctgr_id", ""),
    #                                 "prdt_name": part_data.get("prdt_name", ""),
    #                                 "description": part_data.get("description", ""),
    #                                 "packaging": part_data.get("packaging", ""),
    #                                 "inventory_position": data_part.get("inventory_position", ""),
    #                                 "qty": data_part.get("quantity", ""),
    #                                 "pass_qty": data_part.get("pass_qty", ""),
    #                                 "fail_qty": data_part.get("fail_qty", ""),
    #                                 "batchId": data_part.get("batchId", ""),
    #                                 "lot_no":data_part.get("lot_no", "testlot"),
    #                                 "lot_id":data_part.get("lot_id","-")
    #                             }
    #                             parts.append(part)
    #                             activity[part_data.get("cmpt_id", "")] = {
    #                                 "mfr_prt_num": part_data.get("mfr_prt_num", "-"),
    #                                 "date":str(date.today()),
    #                                 "action":"Purchased",
    #                                 "Description":"Purchased",
    #                                 "issued_to":"Peopletech Group",
    #                                 "po_no":po_id,
    #                                 'invoice_no':data["invoice_num"],
    #                                 "cmpt_id": part_data.get("cmpt_id", ""),
    #                                 "ctgr_id": part_data.get("ctgr_id", ""),
    #                                 "prdt_name": part_data.get("prdt_name", ""),
    #                                 "description": part_data.get("description", ""),
    #                                 "packaging": part_data.get("packaging", ""),
    #                                 # "inventory_position": data_part.get("inventory_position", ""),
    #                                 "closing_qty": f"{int(invent_data[part_data["cmpt_id"]]['qty'])+int(data_part.get("pass_qty", "0"))}",
    #                                 "qty": data_part.get("pass_qty", ""),
    #                                 # "pass_qty": data_part.get("pass_qty", ""),
    #                                 # "fail_qty": data_part.get("fail_qty", ""),
    #                                 "batchId": data_part.get("batchId", ""),
    #                                 "used_qty":"0",
    #                                 "lot_no":data_part.get("lot_no", "testlot")
    #                             }
    #             all_attributes = {
    #                 "parts": {f'part{i + 1}': parts[i] for i in range(len(parts))},
    #                 "vendor_id": data["vendor_id"],
    #                 "order_date": data["order_date"],
    #                 "description": data["description"],
    #                 "sk_timeStamp": sk_timeStamp,
    #                 'inward_date': sk_timeStamp[:10],
    #                 "po_id": po_id,
    #                 "gate_entry_date": poData[0]["all_attributes"]["gate_entry_date"],
    #                 "inwardId": poData[0]["all_attributes"]["inwardId"],
    #                 "QA_date": poData[0]["all_attributes"]["QA_date"],
    #                 "sender_contact_number": poData[0]["all_attributes"]["sender_contact_number"],
    #                 "sender_name": poData[0]["all_attributes"]["sender_name"],
    #                 "actions": 'inwarded',
    #                 "invoice_num": data["invoice_num"],
    #                 "invoice": file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, po_id,
    #                                                     po_id.replace("OPTG", ''), "invoice.pdf", data["invoice"]),
    #                 "QATest": file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, po_id,
    #                                                    po_id.replace("OPTG", ''), "QATest.pdf",
    #                                                    data["qa_test_document"]),
    #                 "batchId":batchId
    #             }
    #             photo = {}
    #             for key, doc in data["invoice_photo"].items():
    #                 photo[key] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, po_id,
    #                                                       po_id.replace("OPTG", ''), key, doc)
    #             all_attributes["photo"] = photo
    #             item = {
    #                 "pk_id": po_id + "_INWARDId" + inwardedId,
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": all_attributes,
    #                 "gsipk_table": gsipk_table,
    #                 "gsisk_id": po_id,
    #                 "lsi_key": "status_inward"
    #             }
    #             # UPDATING INVENTORY QUANTITIES
    #             for part in parts:
    #                 cmpt_id = part["cmpt_id"]
    #                 invent_query = {"pk_id": cmpt_id}
    #                 invent_data = dict(db_con["Inventory"].find_one(invent_query))
    #                 qty = str(int(part["pass_qty"]) + int(invent_data["all_attributes"]["qty"]))
    #                 db_con["Inventory"].update_one(invent_query, {"$set": {"all_attributes.qty": qty}})
    #             # INSERTING INWARDED ITEM
    #             db_con[gsipk_table].insert_one(item)
    #             # UPDATING QA TEST AND GATE ENTRY RECORDS
    #             db_con["QATest"].update_one(
    #                 {"pk_id": QA_id, "sk_timeStamp": poData[0]["sk_timeStamp"]},
    #                 {"$set": {"lsi_key": "status_inward"}}
    #             )
    #             db_con["GateEntry"].update_one(
    #                 {"pk_id": gate_id, "sk_timeStamp": gate_id_timestamp},
    #                 {"$set": {"all_attributes.invoice_num": data["invoice_num"]}}
    #             )
    #             db_con['ActivityDetails'].insert_one(
    #                 {
    #                   "pk_id":f"ACTID{activity_id}",
    #                   "sk_timeStamp": sk_timeStamp,
    #                   "all_attributes": activity,
    #                   "gsipk_table": "ActivityDetails",
    #                   "gsisk_id": po_id,
    #                   "lsi_key": "Purchased" 
    #                 }
    #                 )
    #             db_con['all_tables'].update_one(
    #                 {"pk_id": 'top_ids'},
    #                 {"$set": {"all_attributes.ActivityId": str(activity_id)}}
    #                 )
    #             response = {'statusCode': 200, 'body': 'inwarded added successfully'}
    #         else:
    #             response = {'statusCode': 404, 'body': 'data not found'}
    #         return response
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsPurchaseOrderGetPurchaseList(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            purchaseOrder = 'PurchaseOrder'
            status = "Received"
            vendorTableName = 'Vendor'
            # CONSTRUCT THE MONGODB QUERY
            query = {
                "gsipk_table": purchaseOrder,
                "all_attributes.status": status
            }
            # EXECUTE THE QUERY
            result = list(db_con[purchaseOrder].find(query))
            response = []
            if result:
                for item in result:
                    parts = item.get('all_attributes', {}).get('parts', {})  # Assuming 'parts' is a nested field
                    order_number = item['pk_id']
                    vendor_id = item['all_attributes']['vendor_id']
                    order_date = item['sk_timeStamp'].split("T")[0]
                    order_price = item['all_attributes']['total_price']
                    # QUERY VENDOR DETAILS
                    vendor = db_con[vendorTableName].find_one(
                        {"gsipk_table": vendorTableName, "pk_id": vendor_id})
                    if vendor:
                        vendor_name = vendor['all_attributes']['vendor_name']
                        vendor_contact = "+91" + vendor['all_attributes']['contact_number']
                        response.append({
                            "Order_no": order_number,
                            "Vendor_ID": vendor_id,
                            "vendor_name": vendor_name,
                            "Vendor_Contact": vendor_contact,
                            "Order_Date": order_date,
                            "Order_Price": order_price
                        })
            response=sorted(response, key=lambda x: x["Order_Date"], reverse=True)
            return {"statusCode": 200, "body": response}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
        
    def CmsActiveClientPurchaseorder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            query = {
                "gsipk_table":"ClientForcastPurchaseOrder" ,
                "gsisk_id":"open"
            }
            projection = {
                "all_attributes.Client_Purchaseorder_num": 1,
                "_id": 0
            }
            result = db_con["ForcastPurchaseOrder"].find(query, projection)
            lst = [{"client_po": i["all_attributes"]["Client_Purchaseorder_num"]} for i in result]

            # response=sorted(response, key=lambda x: x["Order_Date"], reverse=True)
            return {"statusCode": 200, "body": lst}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def CmsPurchaseOrderGetVendorDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            vendor_id = data.get("vendor_id")

            match_stage = {
                "$match": {
                    "gsipk_table": "Vendor",
                    "pk_id": vendor_id
                }
            }
            # Execute aggregation pipeline
            pipeline = [
                match_stage
            ]
            vendors = list(db_con.Vendor.aggregate(pipeline))
            # print(vendors)
            lst = sorted([
                {
                    'vendor_id': item.get('pk_id', ""),
                    'vendor_type': item["all_attributes"].get('vendor_type', ""),
                    "ship_to": {
                        "company_name": "People Tech IT Consultancy Pvt Ltd",
                        "gst_number": "36AAGCP2263H2ZE",
                        "pan_number": " AAGCP2263H",
                        "contact_details": "Sudheendra Soma",
                        "contact_number": "9885900909",
                        "address": "Plot No.14 & 15, RMZ Futura Building, Block B, Hitech City, Hyderabad,Telangana, India- 500081"
                    },
                    "kind_Attn": {
                        "company_name":item["all_attributes"].get('vendor_name', ""),
                        "gst_number": item["all_attributes"].get('gst_number', ""),
                        "pan_number": item["all_attributes"].get('pan_number', ""),
                        "contact_number": item["all_attributes"].get('contact_number', ""),
                        "address": item["all_attributes"].get('address1', "")
                    },
                    "req_line": """Dear Sir/Ma'am,
                                Please Supply the Items mentioned in Order subject to delivery, mode and other terms and conditions below and overleaf. Please confirm the acceptance of this order. If you expect any delay in supply,communicate the same immediately on receipt of this purchase order."""
                }
                for item in vendors
            ], key=lambda x: int(x['vendor_id'].replace("PTGVEN", "")), reverse=False)
            # # #print(lst)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst[0]}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'vendor deletion failed'}

    def CmsCreatePurchaseOrderSaveDraft(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            query = {
                "gsipk_table":"ClientForcastPurchaseOrder" ,
                "gsisk_id":"open"
            }
            projection = {
                "all_attributes.Client_puechaseorder_num": 1,
                "_id": 0
            }
            result = db_con["ForcastPurchaseOrder"].find(query, projection)

            # response=sorted(response, key=lambda x: x["Order_Date"], reverse=True)
            return {"statusCode": 200, "body": ""}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
        

    
    
    def cmsGetEditDraft(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            pk_id = data['po_id']
            draftpo = list(db_con.DraftPurchaseOrder.find({'all_attributes.po_id': pk_id}))
            output = [i['all_attributes'] for i in draftpo]
            response = {}
            for d in output:
                response.update(d)
            
            # Ensure purchase_list is returned as a list
            purchase_list_dict = response.get("purchase_list", {})
            purchase_list = [value for value in purchase_list_dict.values()]
            response["purchase_list"] = purchase_list

            return {'statusCode': 200, 'body': response}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Unable to Get Drafts'}

            



    # def cmsGetEditDraft(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         pk_id = data['po_id']
    #         draftpo = list(db_con.DraftPurchaseOrder.find({'all_attributes.po_id': pk_id}))
    #         output = [i['all_attributes'] for i in draftpo]
    #         response = {}
    #         for d in output:
    #             response.update(d)
    #         return {'statusCode': 200, 'body': response}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         return {'statusCode': 400, 'body': 'Unable to Get Drafts'}

    def cmsEditPODraft(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            update_query = data['update']
            pk_id = update_query['po_id']
            sk_timeStamp = (datetime.now()).isoformat()
            primary_doc_details = update_query.get("primary_document_details", {})
            po_date = primary_doc_details.get("po_date", "")
            # if po_date:
            #     try:
            #         po_date_obj = datetime.strptime(po_date, "%Y-%m-%d")
            #         po_month_year = po_date_obj.strftime("%m-%y")
            # Extract month and year from PO_Datedew
            if po_date:
                try:
                    po_date_obj = datetime.strptime(po_date, "%Y-%m-%d")
                    po_month = po_date_obj.strftime("%m")
                    po_year = po_date_obj.strftime("%y")
                    next_month_obj = po_date_obj + relativedelta(months=1)
                    next_month = next_month_obj.strftime("%m")
                    next_year = next_month_obj.strftime("%y")

                    next_year = str(int(po_year) + 1).zfill(2)
                    po_month_year = f"{po_month}/{po_year}-{next_year}"
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid PO_Date format'}
            else:
                return {'statusCode': 400, 'body': 'PO_Date is required'}
            purchase_order = list(db_con.DraftPurchaseOrder.find({}))
            bom_id = data.get('bom_id', '')
            ext = 1
            purchase_order_id = '1'
            if purchase_order:
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                # if update_id and "NewPurchaseOrder" in update_id[0]['all_attributes']:
                if update_id and "PurchaseOrder" in update_id[0]['all_attributes']:
                    # update_id = update_id[0]['all_attributes']['NewPurchaseOrder'][4:]
                    update_id = update_id[0]['all_attributes']['PurchaseOrder'][4:]
                    ext += int(update_id)
                else:
                    update_id = "1"
                purchase_order_id = str(int(update_id) + 1)
                last_client_po_nums = [i["all_attributes"]["po_id"] for i in purchase_order if
                                       "po_id" in i["all_attributes"]]
                if last_client_po_nums:
                    client_po_num = f"EPL/PO/{purchase_order_id}/{po_month_year}"
            update_query["po_id"] = f"EPL/PO/{ext}/{po_month_year}"
            # update_query["vendor_id"] = data["vendor_id"]
            purchase_data = {
                "pk_id": "OPTG" + purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": update_query,
                "gsisk_id": "open",
                "gsipk_table": "PurchaseOrder",
                "lsi_key": "Pending"
            }
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}
            db_con.NewPurchaseOrder.insert_one(purchase_data)
            update_data = {
                '$set': {
                    # 'all_attributes.NewPurchaseOrder': "OPTG" + purchase_order_id
                    'all_attributes.PurchaseOrder': "OPTG" + purchase_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            db_con.DraftPurchaseOrder.delete_one({'all_attributes.po_id': pk_id})
            return {'statusCode': 200, 'body': 'Updated and saved record successfully'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            error_message = f"Exception type: {exc_type}, File name: {f_name}, Line number: {line_no}, Error message: {err}"
            print(error_message)  # or use logging instead of print
            return {'statusCode': 400, 'body': f'Unable to Edit Draft: {error_message}'}

    def deleteDraft(request_body):
        try:
           data = request_body
           env_type = data['env_type']
           db_conct = conct.get_conn(env_type)
           db_con = db_conct['db']
           client = db_conct['client']
           pk_id = data['pk_id']
         
           allDatas = []
           if "DSO"  in pk_id:
                result = db_con.DraftServiceOrder.find({"all_attributes.so_id": pk_id})
                result_list = list(result)
                db_con.DraftServiceOrder.delete_one({"all_attributes.so_id":pk_id})
           elif "DPI" in pk_id:
               result = db_con.DraftProformaInvoice.find({"all_attributes.pi_id": pk_id})
               result_list = list(result)
               db_con.DraftProformaInvoice.delete_one({"all_attributes.pi_id":pk_id})    
           elif "DINV" in pk_id:
               result = db_con.DraftInvoice.find({"all_attributes.inv_id": pk_id})
               result_list = list(result)
               db_con.DraftInvoice.delete_one({"all_attributes.inv_id":pk_id})  
           elif "DPO" in pk_id:
               result = db_con.DraftPurchaseOrder.find({"all_attributes.po_id": pk_id})
               result_list = list(result)
               db_con.DraftPurchaseOrder.delete_one({"all_attributes.po_id":pk_id})
           elif "DCFPO" in pk_id:  
               result = db_con.DraftClientForcastPurchaseOrder.find({"all_attributes.Client_Purchaseorder_num": pk_id})
               result_list = list(result)
               db_con.DraftClientForcastPurchaseOrder.delete_one({"all_attributes.Client_Purchaseorder_num":pk_id})
           elif "DFCPO"in pk_id:
              result = db_con.DraftForcastPurchaseOrder.find({"all_attributes.dfcpo_id": pk_id})
              result_list = list(result)
              db_con.DraftForcastPurchaseOrder.delete_one({"all_attributes.dfcpo_id":pk_id})
           else:
              print("No valid pk_id format found.")  
 
           for documents in result_list:
               allDatas.append(documents)
       
           if len(allDatas)!=0:
               
             if (
                    allDatas[0]["all_attributes"].get("so_id") == pk_id or
                    allDatas[0]["all_attributes"].get("pi_id") == pk_id or
                    allDatas[0]["all_attributes"].get("inv_id") == pk_id or
                    allDatas[0]["all_attributes"].get("po_id") == pk_id or
                    allDatas[0]["all_attributes"].get("Client_Purchaseorder_num") == pk_id or
                    allDatas[0]["all_attributes"].get("dfcpo_id") == pk_id
                ):  
                 return {'statusCode': 200, 'body':'Draft Deleted Successfully'}
           
           else:
                   return {'statusCode': 400, 'body': 'Unable to delete draft'}        
                   
           
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            error_message = f"Unable to Get Drafts: {str(err)} at {f_name} line {line_no}"
            print(error_message)
            return {'statusCode': 400, 'body': 'Unable to delete draft'}
            
    def cmsDeleteDraft(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            pk_id = data['po_id']
            resp = db_con.DraftPurchaseOrder.delete_one({'all_attributes.po_id': pk_id})
            if resp:
                return {'statusCode': 200, 'body': 'Deleted record successfully'}
            else:
                return {'statusCode': 400, 'body': 'Unable to delete record'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': 'Unable to Delete Draft'}

    def cmsGetDraftList(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            draftpo = list(
                db_con.DraftPurchaseOrder.find({"gsipk_table": "DraftPurchaseOrder", "all_attributes": {"$exists": True}}))
            draftinvoice = list(
                db_con.DraftInvoice.find({"gsipk_table": "Draft_Invoice", "all_attributes": {"$exists": True}}))
            draftproformainvoice = list(
                db_con.DraftProformaInvoice.find({"gsipk_table": "DraftProformaInvoice", "all_attributes": {"$exists": True}}))
            draftserviceorder = list(
                db_con.DraftServiceOrder.find({"gsipk_table": "DraftServiceOrder", "all_attributes": {"$exists": True}}))
            draftclientpo = list(
                db_con.DraftClientForcastPurchaseOrder.find({"gsipk_table": "DraftClientForcastPurchaseOrder", "all_attributes": {"$exists": True}}))
            print(draftclientpo)
            draftforcast=list(db_con.DraftForcastPurchaseOrder.find({"gsipk_table": "DraftForcastPurchaseOrder", "all_attributes": {"$exists": True}}))
            print(draftclientpo)

            response = []
            for index, doc in enumerate(draftpo):
                # print(doc)
                if 'all_attributes' in doc:
                    all_attrs = doc['all_attributes']
                    sk_timeStamp = doc.get('sk_timeStamp', '')
                    sk_date = sk_timeStamp.split('T')[0] if sk_timeStamp else 'N/A'
                    response_item = {
                        "s.no": str(index + 1),
                        "company_name": all_attrs.get('ship_to', {}).get('company_name', 'N/A'),
                        "transaction_name": all_attrs.get('primary_document_details', {}).get('transaction_name',
                                                                                              'N/A'),
                        "document_number": all_attrs.get('primary_document_details', {}).get('po_id', 'N/A'),
                        "request_status": all_attrs.get('primary_document_details', {}).get('status', 'N/A'),
                        "modified_date": sk_date,
                        "payment_status": doc.get('gsisk_id', 'N/A'),
                        "ship_to": all_attrs.get('ship_to', {}),
                        "req_line": all_attrs.get('req_line', 'N/A'),
                        "po_terms_conditions": all_attrs.get('po_terms_conditions', 'N/A'),
                        "kind_attn": all_attrs.get('kind_attn', {}),
                        "primary_document_details": all_attrs.get('primary_document_details', {}),
                        "purchase_list": all_attrs.get('purchase_list', {}),
                        "total_amount": all_attrs.get('total_amount', {}),
                        "secondary_doc_details": all_attrs.get('secondary_doc_details', {}),
                        "po_id": all_attrs.get('po_id', {}),
                        "vendor_id": all_attrs.get('vendor_id', 'N/A'),
                        "status": doc['gsisk_id']
                    }
                    response.append(response_item)
            for index, doc in enumerate(draftinvoice):
                if 'all_attributes' in doc:
                    all_attrs = doc['all_attributes']
                    sk_timeStamp = doc.get('sk_timeStamp', '')
                    sk_date = sk_timeStamp.split('T')[0] if sk_timeStamp else 'N/A'
                    response_item = {
                        "s.no": str(index + 1),
                        "company_name": all_attrs.get('ship_to', {}).get('company_name', 'N/A'),
                        "transaction_name": all_attrs.get('primary_document_details', {}).get('transaction_name',
                                                                                              'N/A'),
                        "document_number": all_attrs.get('primary_document_details', {}).get('po_id', 'N/A'),
                        "request_status": all_attrs.get('primary_document_details', {}).get('status', 'N/A'),
                        "modified_date": sk_date,
                        "payment_status": doc.get('gsisk_id', 'N/A'),
                        "ship_to": all_attrs.get('ship_to', {}),
                        "req_line": all_attrs.get('req_line', 'N/A'),
                        "po_terms_conditions": all_attrs.get('po_terms_conditions', 'N/A'),
                        "kind_attn": all_attrs.get('kind_attn', {}),
                        "primary_document_details": all_attrs.get('primary_document_details', {}),
                        "purchase_list": all_attrs.get('purchase_list', {}),
                        "total_amount": all_attrs.get('total_amount', {}),
                        "secondary_doc_details": all_attrs.get('secondary_doc_details', {}),
                        "inv_id": all_attrs.get('inv_id', {}),
                        "vendor_id": all_attrs.get('vendor_id', 'N/A'),
                        "status": doc['gsisk_id']
                    }
                    response.append(response_item)


            for index, doc in enumerate(draftforcast):
                # print(doc)
                if 'all_attributes' in doc:
                    all_attrs = doc['all_attributes']
                    print(all_attrs)
                    sk_timeStamp = doc.get('sk_timeStamp', '')
                    sk_date = sk_timeStamp.split('T')[0] if sk_timeStamp else 'N/A'
                    response_item = {
                        "s.no": str(index + 1),
                        "company_name": all_attrs.get('primary_document_details', {}).get('client_name', 'N/A'),
                        "transaction_name": all_attrs.get('primary_document_details', {}).get('document_title',
                                                                                              'N/A'),
                        "document_number": all_attrs.get('dfcpo_id', {}),
                        "request_status": all_attrs.get('primary_document_details', {}).get('status', 'N/A'),
                        "modified_date": sk_date,
                        # "payment_status": doc.get('gsisk_id', 'N/A'),.get('Client_Purchaseorder_num', 'N/A')
                        "ship_to": all_attrs.get('buyer_details', {}),
                        # "req_line": all_attrs.get('req_line', 'N/A'),
                        # "po_terms_conditions": all_attrs.get('po_terms_conditions', 'N/A'),
                        # "kind_attn": all_attrs.get('kind_attn', {}),
                        "primary_document_details": all_attrs.get('primary_document_details', {}),
                        "purchase_list": all_attrs.get('forecast_details', {}),
                        "total_amount": all_attrs.get('total_amount', {}),
                        # "secondary_doc_details": all_attrs.get('secondary_doc_details', {}),
                        "dfcpo_id": all_attrs.get('dfcpo_id', {}),
                        # "vendor_id": all_attrs.get('vendor_id', 'N/A'),
                        "status": doc['gsisk_id']
                    }
                    response.append(response_item)


            for index, doc in enumerate(draftproformainvoice):
                if 'all_attributes' in doc:
                    all_attrs = doc['all_attributes']
                    sk_timeStamp = doc.get('sk_timeStamp', '')
                    sk_date = sk_timeStamp.split('T')[0] if sk_timeStamp else 'N/A'
                    response_item = {
                        "s.no": str(index + 1),
                        "company_name": all_attrs.get('ship_to', {}).get('company_name', 'N/A'),
                        "transaction_name": all_attrs.get('primary_document_details', {}).get('transaction_name',
                                                                                              'N/A'),
                        "document_number": all_attrs.get('primary_document_details', {}).get('po_id', 'N/A'),
                        "request_status": all_attrs.get('primary_document_details', {}).get('status', 'N/A'),
                        "modified_date": sk_date,
                        "payment_status": doc.get('gsisk_id', 'N/A'),
                        "ship_to": all_attrs.get('ship_to', {}),
                        "req_line": all_attrs.get('req_line', 'N/A'),
                        "po_terms_conditions": all_attrs.get('po_terms_conditions', 'N/A'),
                        "kind_attn": all_attrs.get('kind_attn', {}),
                        "primary_document_details": all_attrs.get('primary_document_details', {}),
                        "purchase_list": all_attrs.get('purchase_list', {}),
                        "total_amount": all_attrs.get('total_amount', {}),
                        "secondary_doc_details": all_attrs.get('secondary_doc_details', {}),
                        "pi_id": all_attrs.get('pi_id', {}),
                        "vendor_id": all_attrs.get('vendor_id', 'N/A'),
                        "status": doc['gsisk_id']
                    }
                    response.append(response_item)
            for index, doc in enumerate(draftserviceorder):
                if 'all_attributes' in doc:
                    all_attrs = doc['all_attributes']
                    sk_timeStamp = doc.get('sk_timeStamp', '')
                    sk_date = sk_timeStamp.split('T')[0] if sk_timeStamp else 'N/A'
                    response_item = {
                        "s.no": str(index + 1),
                        "company_name": all_attrs.get('ship_to', {}).get('company_name', 'N/A'),
                        "transaction_name": all_attrs.get('primary_document_details', {}).get('transaction_name',
                                                                                              'N/A'),
                        "document_number": all_attrs.get('primary_document_details', {}).get('po_id', 'N/A'),
                        "request_status": all_attrs.get('primary_document_details', {}).get('status', 'N/A'),
                        "modified_date": sk_date,
                        "payment_status": doc.get('gsisk_id', 'N/A'),
                        "ship_to": all_attrs.get('ship_to', {}),
                        "req_line": all_attrs.get('req_line', 'N/A'),
                        "po_terms_conditions": all_attrs.get('po_terms_conditions', 'N/A'),
                        "kind_attn": all_attrs.get('kind_attn', {}),
                        "primary_document_details": all_attrs.get('primary_document_details', {}),
                        "purchase_list": all_attrs.get('purchase_list', {}),
                        "total_amount": all_attrs.get('total_amount', {}),
                        "secondary_doc_details": all_attrs.get('secondary_doc_details', {}),
                        "so_id": all_attrs.get('so_id', {}),
                        "vendor_id": all_attrs.get('vendor_id', 'N/A'),
                        "status": doc['gsisk_id']
                    }
                    response.append(response_item)
            
            for index, doc in enumerate(draftclientpo):
                # print(doc)
                if 'all_attributes' in doc:
                    all_attrs = doc['all_attributes']
                    print(all_attrs)
                    sk_timeStamp = doc.get('sk_timeStamp', '')
                    sk_date = sk_timeStamp.split('T')[0] if sk_timeStamp else 'N/A'
                    response_item = {
                        "s.no": str(index + 1),
                        "company_name": all_attrs.get('primary_document_details', {}).get('client_name', 'N/A'),
                        "transaction_name": all_attrs.get('primary_document_details', {}).get('document_title',
                                                                                              'N/A'),
                        "document_number": all_attrs.get('Client_Purchaseorder_num', {}),
                        "request_status": all_attrs.get('primary_document_details', {}).get('status', 'N/A'),
                        "modified_date": sk_date,
                        # "payment_status": doc.get('gsisk_id', 'N/A'),.get('Client_Purchaseorder_num', 'N/A')
                        "ship_to": all_attrs.get('buyer_details', {}),
                        # "req_line": all_attrs.get('req_line', 'N/A'),
                        # "po_terms_conditions": all_attrs.get('po_terms_conditions', 'N/A'),
                        # "kind_attn": all_attrs.get('kind_attn', {}),
                        "primary_document_details": all_attrs.get('primary_document_details', {}),
                        "purchase_list": all_attrs.get('forecast_details', {}),
                        "total_amount": all_attrs.get('total_amount', {}),
                        # "secondary_doc_details": all_attrs.get('secondary_doc_details', {}),
                        "Client_Purchaseorder_num": all_attrs.get('Client_Purchaseorder_num', {}),
                        # "vendor_id": all_attrs.get('vendor_id', 'N/A'),
                        "status": doc['gsisk_id']
                    }
                    response.append(response_item)

            
            return {'statusCode': 200, 'body': response}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            error_message = f"Unable to Get Drafts: {str(err)} at {f_name} line {line_no}"
            return {'statusCode': 400, 'body': error_message}



    def cmsGetEditPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id = data['po_id']
            result = list(db_con.NewPurchaseOrder.find({'all_attributes.po_id':po_id, "gsipk_table":"PurchaseOrder"}))
            return {'statusCode': 200, 'body': result[0]["all_attributes"]}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Bad Request(check data): {err} (file: {f_name}, line: {line_no})'}
    def cmsGetAlldetailsForDocumentNumber(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id=data['document_id']
            query = {
                '$or': [
                    {'all_attributes.po_id': po_id, 'gsipk_table': 'PurchaseOrder'},
                    {'all_attributes.so_id': po_id, 'gsipk_table': 'ServiceOrder'},
                    {'all_attributes.inv_id': po_id, 'gsipk_table': 'Invoice'}
                ]
            }

            combined_data_po = list(db_con.NewPurchaseOrder.find(query, {'_id': 0,'all_attributes':1}))

            combined_ids=[]
            if combined_data_po:
                combined_ids = [
                    i['all_attributes']
                    for i in combined_data_po
                    if 'all_attributes' in i
                    for id_value in (
                        i['all_attributes'].get('po_id'),
                        i['all_attributes'].get('so_id'),
                        i['all_attributes'].get('inv_id')
                    )
                    if id_value is not None
                ][0]
            query1={
                '$or': [
                    {'all_attributes.fcpo_id': po_id, 'gsipk_table': 'ForcastPurchaseOrder'},
                    {'all_attributes.Client_Purchaseorder_num': po_id, 'gsipk_table': 'ClientForcastPurchaseOrder'}]
            }
            forecast_data=list(db_con.ForcastPurchaseOrder.find(query1, {'_id': 0,'all_attributes':1}))
            if forecast_data:
                combined_ids = [
                    i['all_attributes']
                    for i in forecast_data
                    if 'all_attributes' in i
                    for id_value in (
                        i['all_attributes'].get('fcpo_id'),
                        i['all_attributes'].get('Client_Purchaseorder_num'))
                    if id_value is not None
                ][0]
            pf_data = list(db_con.ProformaInvoice.find({'all_attributes.pi_id':po_id, "gsipk_table":"ProformaInvoice"},{"_id":0,'all_attributes':1}))
            if pf_data:
                combined_ids = [i['all_attributes'] for i in pf_data if 'all_attributes' in i][0]
            combined_data_po_draft = list(db_con.DraftPurchaseOrder.find({'all_attributes.po_id':po_id, "gsipk_table":"DraftPurchaseOrder"},{"_id":0,'all_attributes':1}))
            if combined_data_po_draft:
                combined_ids = [i['all_attributes'] for i in combined_data_po_draft if 'all_attributes' in i][0]
            combined_data_client_draft = list(db_con.DraftClientForcastPurchaseOrder.find({'all_attributes.Client_Purchaseorder_num':po_id, "gsipk_table":"DraftClientForcastPurchaseOrder"},{"_id":0,'all_attributes':1}))
            if combined_data_client_draft:
                combined_ids = [i['all_attributes'] for i in combined_data_client_draft if 'all_attributes' in i][0]
            combined_data_forecast_draft = list(db_con.DraftForcastPurchaseOrder.find({'all_attributes.dfcpo_id':po_id, "gsipk_table":"DraftForcastPurchaseOrder"},{"_id":0,'all_attributes':1}))
            if combined_data_forecast_draft:
                combined_ids = [i['all_attributes'] for i in combined_data_forecast_draft if 'all_attributes' in i][0]
            combined_data_invoice_draft = list(db_con.DraftInvoice.find({'all_attributes.inv_id':po_id, "gsipk_table":"Draft_Invoice"},{"_id":0,'all_attributes':1}))
            if combined_data_invoice_draft:
                combined_ids = [i['all_attributes'] for i in combined_data_invoice_draft if 'all_attributes' in i][0]
            combined_data_proforma_draft = list(db_con.DraftProformaInvoice.find({'all_attributes.pi_id':po_id, "gsipk_table":"DraftProformaInvoice"},{"_id":0,'all_attributes':1}))
            if combined_data_proforma_draft:
                combined_ids = [i['all_attributes'] for i in combined_data_proforma_draft if 'all_attributes' in i][0]
            combined_data_service_draft = list(db_con.DraftServiceOrder.find({'all_attributes.so_id':po_id, "gsipk_table":"DraftServiceOrder"},{"_id":0,'all_attributes':1}))
            if combined_data_service_draft:
                combined_ids = [i['all_attributes'] for i in combined_data_service_draft if 'all_attributes' in i][0]
            if combined_ids:
                mapping = {
                    'PO': 'purchase_list',
                    'SO': 'job_work_table',
                    'INV': 'purchase_list',
                    'CFPO': 'forecast_details',
                    'FCPO': 'forecast_details',
                    'PI': 'products_list',
                    "DFCPO":"forecast_details",
                    "DCFPO":"productlistDetails",
                    "DINV":"purchase_list",
                    "DPI":"products_list",
                    "DPO":"purchase_list",
                    "DSO":"job_work_table"

                }
                for doc_id, combined_key in mapping.items():
                    if doc_id == po_id.split("/")[1]:
                        print(doc_id)
                        temp_list = combined_ids.get(combined_key)
                        if isinstance(temp_list,dict):
                            combined_ids[combined_key] = [j for i, j in temp_list.items()]

               
                return {'statusCode': 200, 'body': combined_ids}
            else:
                return {'statusCode': 400, 'body': "There is no data for document id"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
    def cmsAddCommentsAndAttachmentsForPurchaseOrder(request_body):    
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            po_id = data["po_id"]
            time_atch = datetime.now().isoformat()
            result = list(db_con["NewPurchaseOrder"].find({"gsipk_table": "PurchaseOrder", "all_attributes.po_id": po_id},{'_id':0}))
            if result:
                
                attachment_list=[]

                all_attributes = result[0]["all_attributes"]
                pk_id = result[0]["pk_id"]
                sk_timeStamp = result[0]["sk_timeStamp"]
                comment_details = {
                    "comment": data.get("comment", ""),
                    "doc_time": time_atch
                }
                all_attributes.setdefault("cmts_atcmts", {})
                if "attachment" in data and data["attachment"]:
                    for attachment in data['attachment']:
                        document_body = attachment['doc_body']
                        document_name = attachment['doc_name']
                        extra_type = ""
                        
                        # Upload the file and get the URL
                        attachment_url = file_uploads.upload_file(
                            "NewPurchaseOrder",
                            "PtgCms" + env_type,
                            extra_type,
                            "NewPo" + pk_id,
                            document_name,
                            document_body
                        )
                        print(attachment_url)
                        
                        # Append the attachment details to the list
                        attachment_list.append({
                            "doc_body": attachment_url,
                            "doc_name": document_name
                        })
                        
                        # Update the all_attributes dictionary
                    existing_keys = all_attributes["cmts_atcmts"].keys()
                    max_index = max([int(k.split("_")[-1]) for k in existing_keys], default=0)
                    next_index = max_index + 1
                    all_attributes["cmts_atcmts"][f"cmts_atcmts_{next_index}"] = {
                        "comment": comment_details["comment"],
                        "doc_time": comment_details["doc_time"],
                        "Attachments": 
                            attachment_list,
                    }

                else:
                    existing_keys = all_attributes["cmts_atcmts"].keys()
                    max_index = max([int(k.split("_")[-1]) for k in existing_keys], default=0)
                    next_index = max_index + 1
                    all_attributes["cmts_atcmts"][f"cmts_atcmts_{next_index}"] = {
                        "comment": comment_details["comment"],
                        "doc_time": comment_details["doc_time"]
                    }
                # result[0]["all_attributes"] = all_attributes


                db_con["NewPurchaseOrder"].update_one(
                    {"pk_id": pk_id},
                    {"$set": {"all_attributes": all_attributes}}
                )
                return {"statusCode": 200, "body": "Comment added successfully"}
            else:
                return {"statusCode": 404, "body": "No  purchase order found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check event)'}
    def cmsGetCommentsAndAttachmentsForPurchaseOrder(request_body):    
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id=data['po_id']
            result = list(db_con.NewPurchaseOrder.find({'all_attributes.po_id':po_id, "gsipk_table":"PurchaseOrder"},{'_id':0,'all_attributes':1}))
            dates = [datetime.strptime(part['delivery_date'], "%Y-%m-%d") for part in result[0]['all_attributes']['purchase_list'].values() if 'delivery_date' in part]
            result[0]['all_attributes']['cmts_atcmts']['po_id']=data['po_id']
            result[0]['all_attributes']['cmts_atcmts']['grand_total']=result[0]['all_attributes']['total_amount']['grand_total']
            result[0]['all_attributes']['cmts_atcmts']['max_delivery_date'] = max(dates).strftime("%d/%m/%Y") if dates else None
            result[0]['all_attributes']['cmts_atcmts']['comment_count'] = sum(
                1 for c in result[0]["all_attributes"]["cmts_atcmts"].values() if isinstance(c, dict) and c.get("comment")
            )

            result[0]['all_attributes']['cmts_atcmts']['attachments_count'] = sum(
            len(c.get("Attachments", {})) for c in result[0]["all_attributes"]["cmts_atcmts"].values() if isinstance(c, dict)
                )

            return {'statuscode':200,'body':result[0]['all_attributes']['cmts_atcmts']}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
    
    def cmsGetGateEntryIdForNewPo(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id = data['po_id']
            result = db_con.GateEntry.find({"all_attributes.document_id": po_id},{'_id':0})
            output_result = list(result)
            listOfPkIds = []
            for i in range(len(output_result)):
              listOfPkIds.append(output_result[i]["pk_id"])
            if listOfPkIds:  
              return {"statusCode":200,"body": listOfPkIds}
            else:
              return {"statusCode":400,"body": "No data found"}
           
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
    
    def cmsNewPurchaseOrderQaTestGetDetails(request_body):
        # try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client'] 
            doc_po_id = data['po_id']
            inwardId = data['inwardId']
            po_tablename = 'PurchaseOrder'
            inward_tablename = 'GateEntry'

            category = {}
            for item in db_con['Metadata'].find():
                pk_id = item['pk_id'].replace("MDID", "CTID")
                if item['gsipk_id'] == 'Electronic':
                    sub_categories = {key: value for key, value in item['sub_categories'].items()}
                    category[pk_id] = {"ctgr_name": item['gsisk_id'], "sub_categories": sub_categories}
                else:
                    category[pk_id] = {"ctgr_name": item['gsisk_id']}
            inventory = {}
            d = list(db_con['Inventory'].find())

            for item in d:
                inventory[item['pk_id']] = item['all_attributes']

            result = db_con[inward_tablename].find_one(
                {"gsipk_table": inward_tablename, "all_attributes.document_id": doc_po_id, "pk_id": inwardId},{"_id":0}
            )
            result = dict(result) if result else {}
            po_id=result.get("gsisk_id")
            # response={}
            if result:
                response = {
                    'order_no': po_id,
                    'inwardId': result['all_attributes']['inwardId'],
                    'QA_date': str(datetime.today()),
                    'invoice_photo': {i: file_get(result['all_attributes']['photo'][i]) for i in
                                      result['all_attributes']['photo']},
                    'invoice_document': file_get(result['all_attributes']['invoice']),
                    'invoice_num': result['all_attributes']['invoice_num'],
                    'sender_name': result['all_attributes']['sender_name'],
                    'vendorId': result['all_attributes']['vendorId'],
                    'sender_contact_number': result['all_attributes']['sender_contact_number'],
                    'parts': []
                    }
                for key, value in result['all_attributes']['parts'].items():
                    if value['received_qty'] != '0':
                        part_data = {
                            "s_no": key.replace("part", ""),
                            "ctgr_id": value['ctgr_id'],
                            "cmpt_id": value['cmpt_id'],
                            "part_no": value['mfr_prt_num'],
                            "part_name": category[value['ctgr_id']]['sub_categories'][
                                inventory[value['cmpt_id']]['sub_ctgr']] if value['department'] == 'Electronic' else
                            inventory[value['cmpt_id']].get('prdt_name', ''),
                            "unit_price": value['unit_price'],
                            "department": value['department'],
                            "received_qty": value['received_qty'],
                            "price": value['price'],
                            "description": inventory[value['cmpt_id']].get('description', ''),
                            "packaging": inventory[value['cmpt_id']].get('package', ''),
                            "manufacturer": inventory[value['cmpt_id']].get('mfr', '-'),
                            "pass_qty": "0",
                            "fail_qty": "0"
                        }
                        response['parts'].append(part_data)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': response}

        # except Exception as err:
        #     exc_type, exc_obj, tb = sys.exc_info()
        #     f_name = tb.tb_frame.f_code.co_filename
        #     line_no = tb.tb_lineno
        #     #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
        #     return {'statusCode': 400, 'body': 'PO deletion failed'}
    def cmsNewPurchaseOrderSaveQATest(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            result = list(db_con.QATest.find({}))
            po_id = data["order_no"]
            gsipk_table = "QATest"
            qa_id = data['inwardId'].split('IN')[-1]
            gate_id = data["inwardId"]
            QA_test = "QA_test"
            poData = list(db_con.NewPurchaseOrder.find(
                {"pk_id": po_id}
                , {"_id": 0, "all_attributes": 1}))
            
            # po_id=poData
            gateEntry = list(db_con.GateEntry.find({
                "$and": [
                    {"pk_id": gate_id}]},
                {"_id": 0, "all_attributes": 1, "pk_id": 1, "sk_timeStamp": 1}))
            batch_id = db_con.all_tables.find_one({"pk_id":"top_ids"},{"_id":0,"all_attributes.batchId":1})
            if 'batchId' in batch_id['all_attributes']:
                batch_id = int(batch_id['all_attributes']['batchId'])+1
            else:
                batch_id = len(list(db_con.inward.find({})))
            if gateEntry:
                parts = gateEntry[0]['all_attributes']['parts']
                quant_ref = {part['cmpt_id']: int(part['received_qty']) for key, part in parts.items()}
                if any(1 for part in data['parts'] if
                       quant_ref[part['cmpt_id']] != int(part['pass_qty']) + int(part['fail_qty'])):
                    return {'statusCode': 404,
                            'body': 'pass qty and fail qty do not match the quantity for some components'}
                parts = [
                    {
                        "cmpt_id": part_data["cmpt_id"],
                        "ctgr_id": part_data['ctgr_id'],
                        "mfr_prt_num": part_data["item_no"],
                        "prdt_name": part_data["prdt_name"],
                        "description": part_data["description"],
                        "department": data["parts"][j]["department"],
                        "packaging": part_data["packaging"],
                        "qty": str(part_data["qty"]),
                        "price": data["parts"][j]["price"],
                        "price_per_piece": data["parts"][j]["unit_price"],
                        "manufacturer": part_data['manufacturer'] if 'manufacturer' in part_data else '-',
                        "pass_qty": data["parts"][j]["pass_qty"],
                        "fail_qty": data["parts"][j]["fail_qty"],
                        "lot_id": data["parts"][j]["lot_id"],
                        "batchId": "BTC" + str(batch_id)
                    }
                    for i in poData
                    for part_key, part_data in i.get("all_attributes", {}).get("purchase_list", {}).items()
                    for j in range(len(data.get("parts", [])))
                    if part_data["item_no"] == data["parts"][j].get("part_no")
                ]
                for part in data['parts']:
                    cmpt_id = part["cmpt_id"]
                    quant_ref[cmpt_id] += int(part['fail_qty'])
                    inventory_query = {
                        "gsipk_table": "Inventory",
                        "pk_id": cmpt_id
                    }
                    inventory_data = db_con["Inventory"].find_one(inventory_query)
                    fail_qty = int(inventory_data['all_attributes'].get("fail_qty", 0)) + int(part['fail_qty'])
                    db_con["Inventory"].update_one(
                        inventory_query,
                        {"$set": {"all_attributes.fail_qty": fail_qty}}
                    )
                docs1 = {}
                photo = {}
                for key, doc in data["invoice_photo"].items():
                    photo[key] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "", gate_id, key,doc)
                docs1["photo"] = photo
                if "invoice_document" in data.keys():
                    docs1["invoice"] = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "pdf",gate_id, "invoice.pdf", data["invoice_document"])
                # for doc in data["documents"]:
                #     image_path = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, doc["doc_type"],gate_id, doc["doc_name"], doc["doc_body"])
                #     docs1["QATest"] = image_path

                for excel in data.get("excle", []):
                    excel_path = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, excel["excle_type"], gate_id, excel["file_type"], excel["excle"])
                    docs1[excel["file_type"]] = excel_path

                # if "csv_document" in data.keys():
                #     csv_path = file_uploads.upload_file("purchaseOrder", "PtgCms" + env_type, "csv", gate_id, "SendFinalProducts.csv", data["csv_document"])
                #     docs1["SendFinalProducts.csv"] = csv_path
                
                vendor_id = gateEntry[0]["all_attributes"]["vendorId"]
                vendor_query = {
                    "gsipk_table": "Vendor",
                    "pk_id": vendor_id
                }
                vendor_data = db_con["Vendor"].find_one(vendor_query)
                all_attributes = {
                    "parts": {f'part{i + 1}': parts[i] for i in range(len(parts))},
                    "QA_date": data["QA_date"],
                    "vendorId": vendor_id,
                    "vendor_contact_number": vendor_data["all_attributes"]["contact_number"],
                    "vendor_name": vendor_data["all_attributes"]["vendor_name"],
                    'actions': 'inward',
                    "sender_name": data["sender_name"],
                    "invoice_num": data["invoice_num"],
                    "sender_contact_number": data["sender_contact_number"],
                    "description": data["description"],
                    "sk_timeStamp": sk_timeStamp,
                    "po_id": po_id,
                    "document_id":data['document_id'],
                    "inwardId": data["inwardId"],
                    "gate_entry_date": gateEntry[0]["all_attributes"]["gate_entry_date"]
                }
                all_attributes.update(docs1)

                qa_item = {
                    "pk_id": po_id + "_QAID" + qa_id,
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": all_attributes,
                    "gsipk_table": gsipk_table,
                    "gsisk_id": po_id,
                    "lsi_key": "status_QA-Test"
                }
                db_con[gsipk_table].insert_one(qa_item)
                db_con['all_tables'].update_one(
                    {"pk_id": 'top_ids'},
                    {"$set": {"all_attributes.batchId": str(batch_id)}}
                    )
                db_con["GateEntry"].update_one(
                    {"pk_id": gate_id},
                    {"$set": {
                        "all_attributes.pending": "Inward",
                        "all_attributes.actions": "Inward"
                    }}
                )
                conct.close_connection(client)
                return {'statusCode': 200, 'body': 'QA added successfully'}

            else:
                return {"statusCode": 400, "body": "No record found for Gate Entry"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'PO deletion failed'}
        
    def cmsGetPOGateEntry(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            return_id = data.get("return_id", "")
            filter = {"all_attributes.po_id": data["po_id"]}
            projection = {
                "_id": 0
            }
            result = (db_con.NewPurchaseOrder.find_one(filter, projection))
            if result:
                bom_id = result['all_attributes'].get('bom_id','')
                category = db_con["Metadata"].find()
                category = {
                    item['pk_id'].replace("MDID", "CTID"): (
                        {
                            "ctgr_name": item['gsisk_id'],
                            "sub_categories": {
                                key: value for key, value in item['sub_categories'].items()
                            }
                        }
                        if item['gsipk_id'] == 'Electronic'
                        else {"ctgr_name": item['gsisk_id']}
                    )
                    for item in category
                }
                filter = {"gsipk_table": "Inventory"}
                projection = {
                    "_id": 0,
                    "all_attributes": 1
                }
                inventory = list(db_con["Inventory"].find(filter, projection))
                inventory = {item["all_attributes"]['cmpt_id']: item["all_attributes"] for item in inventory}
                part_info = {}
                if data.get('status', '') == "PurchaseReturn":
                    return_ref = {}
                    return_inventory = list(db_con.GateEntry.find({"all_attributes.return_id": return_id}))
                    for item in return_inventory:
                        for part_key, part_attributes in item["all_attributes"]['parts'].items():
                            cmpt_id = part_attributes['cmpt_id']
                            received_qty = part_attributes['received_qty']
                            return_ref[cmpt_id] = received_qty if cmpt_id not in return_ref else str(
                                int(return_ref[cmpt_id]) + int(received_qty))
                    # return return_ref
                    return_data = db_con["PurchaseReturn"].find_one(
                        {"gsipk_table": "PurchaseReturn", "pk_id": return_id})
                    part_info["parts"] = {
                        key: {
                            "cmpt_id": value['cmpt_id'],
                            "ctgr_id": value['ctgr_id'],
                            "unit_price": value['price_per_piece'],
                            "received_qty": '0' if not return_ref and value[
                                'cmpt_id'] not in return_ref else return_ref.get(value['cmpt_id'], '0'),
                            "balance_qty": str(int(value['qty']) - abs(
                                int('0' if not return_ref and value['cmpt_id'] not in return_ref else return_ref[
                                    value['cmpt_id']]))),
                            "description": inventory[value['cmpt_id']].get('description', '-'),
                            "packaging": inventory[value['cmpt_id']].get('packaging', '-'),
                            "mfr_prt_num": value['mfr_prt_num'],
                            "manufacturer": inventory[value['cmpt_id']].get('manufacturer', '-'),
                            "price": value['price'],
                            "qty": value['qty'],
                            "delivery_date": value.get('delivery_date', ''),
                            "ctgr_name": category[value['ctgr_id']]['ctgr_name'],
                            "department": value['department'],
                            "prdt_name": category[value['ctgr_id']]['sub_categories'][
                                inventory[value['cmpt_id']]['sub_ctgr']]
                            if value['department'] != 'Mechanic' else inventory[value['cmpt_id']]['prdt_name']
                        }
                        for key, value in return_data['all_attributes']['parts'].items()
                        if str(int(value['qty']) - int(
                            '0' if not return_ref and value['cmpt_id'] not in return_ref else return_ref.get(
                                value['cmpt_id'], '0'))) != '0'
                    }
                    part_info["order_id"] = result["pk_id"]
                    part_info['return_id'] = data['return_id']
                    part_info["order_date"] = result["sk_timeStamp"][:10]
                    part_info['total_ordered_quantity'] = result['all_attributes']['total_qty']
                    return {"statusCode": 200, "body": part_info}
                else:
                    gate_entry = list(db_con["GateEntry"].find({"gsipk_table": "GateEntry", "gsisk_id": data["po_id"]}))
                    ref = {}
                    for item in gate_entry:
                        # if item['all_attributes'].get("return_id","")=="":
                        for key, value in item['all_attributes']['parts'].items():
                            ref[value['cmpt_id']] = int(value['received_qty']) if value['cmpt_id'] not in ref else ref[value['cmpt_id']] + int(value['received_qty'])
                    part_info["parts"] = {
                        key: {
                            "cmpt_id": value['cmpt_id'],
                            "ctgr_id": value['ctgr_id'],
                            "received_qty": value.get('received_qty', '0'),
                            "description": inventory[value['cmpt_id']].get('description', ''),
                            "packaging": inventory[value['cmpt_id']].get('packaging', ''),
                            "unit_price": value['rate'],
                            "mfr_prt_num": value['item_no'],
                            "manufacturer": inventory[value['cmpt_id']].get('manufacturer', '-'),
                            "price": str(float(value['basic_amount']) + float(value['gst_amount'])),
                            "qty": value['qty'],
                            "delivery_date": value.get('delivery_date', ''),
                            "ctgr_name": category[value['ctgr_id']]['ctgr_name'],
                            "department": value['department'],
                            "prdt_name": category[value['ctgr_id']]['sub_categories'][
                                inventory[value['cmpt_id']]['sub_ctgr']]
                            if value['department'] != 'Mechanic' else inventory[value['cmpt_id']]['prdt_name'],
                            "balance_qty": str(
                                abs(int(value['qty']) - abs(ref[value['cmpt_id']]) if gate_entry else int(
                                    value['qty'])))
                        }
                        for key, value in result['all_attributes']['purchase_list'].items()
                        if (not gate_entry or value['cmpt_id'] in ref) and (
                            str(int(value['qty']) - ref[value['cmpt_id']]) if gate_entry else value['qty']) != "0"
                    }
                    ven_id=result['all_attributes']['vendor_id']
                    query=list(db_con.Vendor.find({'pk_id':ven_id},{'_id':0,'all_attributes':1}))
                    part_info["order_id"] = result["pk_id"]
                    part_info["order_date"] = result["sk_timeStamp"][:10]
                    part_info['total_ordered_quantity'] = result['all_attributes'].get('total_qty', '-')
                    part_info['vendor_poc_name'] = query[0]['all_attributes'].get('vendor_poc_name', '-')
                    part_info['vendor_poc_contact_num'] = query[0]['all_attributes'].get('vendor_poc_contact_num', '-')
                    part_info['receiver'] = result['all_attributes']['ship_to'].get('company_name', '-')
                    part_info['receiver_contact'] = result['all_attributes']['ship_to'].get('phone_number', '-')
                    part_info['po_id'] = result['all_attributes']['po_id']
 
                    return {"statusCode": 200, "body": part_info}
 
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Gate Entry Failed'}
        
    def cmsPOCardDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            result = db_con.NewPurchaseOrder.find_one({'all_attributes.po_id': data['po_id']})
            if not result:
                return {'statusCode': 404, 'body': 'Purchase Order not found'}

            po_id = result['pk_id']
            responses = []

            # Fetch all inward records based on gsisk_id
            inwards = db_con.GateEntry.find({'gsisk_id': po_id})

            for inward in inwards:
                tick = 0
                inwardId = inward['all_attributes']['inwardId']

                response = {
                    'GateEntry': {},
                    'QATest': {},
                    'inward': {}
                }

                # Fetch GateEntry data
                gate_entry = db_con.GateEntry.find_one({'all_attributes.inwardId': inwardId})
                if gate_entry:
                    tick += 1
                    dt = datetime.fromisoformat(gate_entry['sk_timeStamp'])
                    ge_time = dt.strftime("%d/%m/%Y, %I:%M %p")

                    # Component count
                    part_count = len(gate_entry['all_attributes']['parts'])

                    # Get the sum of all prices
                    total_price = sum(float(part['price']) for part in gate_entry['all_attributes']['parts'].values())

                    dates = [datetime.strptime(part['delivery_date'], "%Y-%m-%d") for part in
                             gate_entry['all_attributes']['parts'].values()]

                    doc_list = []
                    image_list = []
                    for key, value in gate_entry['all_attributes']['documents'].items():
                        doc_list.append({
                            'doc_name': key,
                            'doc_url': value
                        })
                    for key, value in gate_entry['all_attributes']['photo'].items():
                        image_list.append({
                            'doc_name': key,
                            'doc_url': value
                        })

                    response['GateEntry'] = {
                        'gate_entry_id': gate_entry['pk_id'],
                        'date_time': ge_time,
                        'items': part_count,
                        'total_price': total_price,
                        'documents': doc_list,
                        'images': image_list,
                        'invoice_num': gate_entry['all_attributes']['invoice_num'],
                        'due_date': max(dates).strftime("%d/%m/%Y")
                    }

                # Fetch QATest data
                qa_test = db_con.QATest.find_one({'all_attributes.inwardId': inwardId})
                if qa_test:
                    tick += 1
                    dt = datetime.fromisoformat(qa_test['sk_timeStamp'])
                    qa_time = dt.strftime("%d/%m/%Y, %I:%M %p")

                    dates = [datetime.strptime(part['delivery_date'], "%Y-%m-%d") for part in
                             qa_test['all_attributes']['parts'].values()]

                    doc_list = []
                    image_list = []
                    for key, value in qa_test['all_attributes'].get('documents', {}).items():
                        doc_list.append({
                            'doc_name': key,
                            'doc_url': value
                        })
                    for key, value in qa_test['all_attributes']['photo'].items():
                        image_list.append({
                            'doc_name': key,
                            'doc_url': value
                        })

                    response['QATest'] = {
                        'iqc_id': qa_test['pk_id'],
                        'date_time': qa_time,
                        'items': len(qa_test['all_attributes']['parts']),
                        'total_price': sum(float(part['price']) for part in qa_test['all_attributes']['parts'].values()),
                        'documents': doc_list,
                        'images': image_list,
                        'due_date': max(dates).strftime("%d/%m/%Y"),
                        'invoice_num': qa_test['all_attributes']['invoice_num'],
                    }

                # Fetch inward data
                inward_data = db_con.inward.find_one({'all_attributes.inwardId': inwardId})
                if inward_data:
                    tick += 1
                    dt = datetime.fromisoformat(inward_data['sk_timeStamp'])
                    inw_time = dt.strftime("%d/%m/%Y, %I:%M %p")
                    response['inward'] = {
                        'inw_id': inward_data['pk_id'],
                        'date_time': inw_time,
                        'invoice_num': inward_data['all_attributes']['invoice_num'],
                    }
                    
                # Retrieve comments
                comments_data = gate_entry['all_attributes'].get('comments', {})
                comment_list = []
                for comment_id, comment in comments_data.items():
                    attachments = comment.get('attachments', {})
                    attachment_list = [{
                        'file_name': att_name,
                        'file_url': att_url
                    } for att_name, att_url in attachments.items()]

                    comment_list.append({
                        'comment_id': comment_id,
                        'comment_text': comment.get('comment', ''),
                        'created_time': datetime.fromisoformat(comment.get('created_time', '')).strftime("%d/%m/%Y, %I:%M %p"),
                        'attachments': attachment_list
                    })

                response['comments'] = comment_list
                response['comment_count'] = len(comment_list)

                # Count total attachments across all comments
                total_attachments = sum(len(comment['attachments']) for comment in comment_list)
                response['attachment_count'] = total_attachments

                response['tick'] = tick
                responses.append(response)

            return {'statusCode': 200, 'body': responses}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check event)'}
        
    def cmsCreatePOGateEntry(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            time = (datetime.now()).isoformat()
            purchaseorder_id = data['order_id']
            # sender_name = data['sender_name']
            # sender_contact_number = data['sender_contact_number']
            sender_name = data['vendor_poc_name']
            sender_contact_number = data['vendor_poc_contact_num']
            receiver_name = data.get('receiver_name', '')
            receiver_contact = data.get('receiver_contact', '')
            parts = data['parts']
            po_tablename = "NewPurchaseOrder"
            purchase_order_query = {"gsipk_table": "PurchaseOrder", "pk_id": purchaseorder_id}
            result = db_con[po_tablename].find_one(purchase_order_query)
            if result:
                # Query to fetch inventory data
                inventory_query = {"gsipk_table": 'Inventory'}
                invent_data = list(db_con.Inventory.find(inventory_query))
                invent_data = {item['pk_id']: item for item in invent_data}
                # Query to fetch QA Test data
                qa_test_query = {"gsipk_table": 'GateEntry', "gsisk_id": purchaseorder_id}
                qatest = list(db_con.GateEntry.find(qa_test_query))
                qa_ref = {}
                for entry in qatest:
                    part = entry["all_attributes"]['parts']
                    for part_key, value in part.items():
                        qa_ref[value['cmpt_id']] = int(value['qty']) if value['cmpt_id'] not in qa_ref else qa_ref[
                                                                                                                value[
                                                                                                                    'cmpt_id']] + int(
                            value['qty'])
                vendorId = result['all_attributes']['vendor_id']
                parts = (result)['all_attributes']['purchase_list']
                part_ref = {part['cmpt_id']: int(part['qty']) for key, part in parts.items()}
                part_ref = {key: part_ref[key] + qa_ref.get(key, 0) for key in part_ref.keys()}
                if any(int(part['qty']) > part_ref[part['cmpt_id']] for part in data['parts']):
                    return {"statusCode": 400, "body": "Gate entry quantity should be less than ordered amount"}
                if any(int(part['received_qty']) > int(part['qty']) for part in data['parts']):
                    return {"statusCode": 400,
                            "body": "Please ensure the received quantity is less than or equal to the ordered amount"}
                total_qty = sum(int(part['received_qty']) for part in data['parts'])
                if not total_qty:
                    return {"statusCode": 400, "body": "Cannot create record without components"}
                inward_tablename = 'GateEntry'
                status = 'Entry'
                pending = 'QA_test'
                # Query to fetch existing inward details
                inward_query = {"gsipk_table": inward_tablename, "gsisk_id": purchaseorder_id}
                inward_details = list(db_con[inward_tablename].find(inward_query))
                inward_id = '01'
                inward_ids = []
                if inward_details:
                    inward_ids = sorted([i["all_attributes"]["inwardId"].split("_IN")[-1] for i in inward_details],
                                        reverse=True)
                    inward_id = str(((2 - len(str(int(inward_ids[0]) + 1)))) * "0") + str(
                        int(inward_ids[0]) + 1) if len(
                        str(int(inward_ids[0]))) <= 2 else str(int(inward_ids[0]) + 1)
                part_key_reference = {}
                for key in result['all_attributes']['purchase_list'].keys():
                    part_key_reference[result['all_attributes']['purchase_list'][key]['item_no']] = key
                if not part_key_reference:
                    return {"statusCode": 400, "body": "Something went wrong while fetching parts for the order"}
                parts_data, component_twi = {}, []
                for part in data['parts']:
                    part_number = part_key_reference[part['mfr_prt_num']]
                    parts_data[part_number] = part
                    pk_id = part['cmpt_id']
                    sk_timeStamp = invent_data[part['cmpt_id']]['sk_timeStamp']
                    qty = int(float(part['received_qty'])) + int(
                        float(invent_data[part['cmpt_id']]["all_attributes"]['qty']))
                    rcd = int(float(part['received_qty'])) + int(
                        float(invent_data[part['cmpt_id']]["all_attributes"].get('rcd_qty', 0)))
                    # Update quantity and received quantity in inventory
                    db_con.Inventory.update_one(
                        {"pk_id": pk_id, "sk_timeStamp": sk_timeStamp},
                        {"$set": {"all_attributes.rcd_qty": str(rcd)}}
                    )
                if not parts_data:
                    return {"statusCode": 400, "body": "Cannot create gate entry without parts"}

                documents = data.get('documents', [])
                images = data.get('images', [])
                doc = {}
                for idx, docs in enumerate(documents):
                    doc_path = file_uploads.upload_file("GateEntry", "PtgCms" + env_type, purchaseorder_id,
                                                        "invoice",
                                                        docs["doc_name"], docs['doc_body'])
                    doc[docs["doc_name"]] = doc_path
                image_upload = {}
                for idx, docs in enumerate(images):
                    image_path = file_uploads.upload_file("GateEntry", "PtgCms" + env_type, purchaseorder_id,
                                                          "images",
                                                          docs["doc_name"], docs['doc_body'])
                    image_upload[docs["doc_name"]] = image_path
                if documents and images:
                    all_attributes = {
                        'inwardId': purchaseorder_id + "_IN" + inward_id,
                        'status': inward_tablename,
                        'total_recieved_quantity': total_qty,
                        'actions': pending,
                        'purchaseorder_id': purchaseorder_id,
                        'invoice': '',
                        'invoice_num': data.get('invoice_num'),
                        'partner_name': data.get('partner_name', ''),
                        'tracking_id': data.get('tracking_id', ''),
                        'photo': image_upload,
                        'gate_entry_date': time[:10],
                        'sender_name': sender_name,
                        'sender_contact_number': sender_contact_number,
                        'parts': parts_data,
                        'documents': doc,
                        'document_id': data['po_id'],
                        'vendorId': vendorId,
                        'rec_name': receiver_name,
                        'rec_cont': receiver_contact
                    }

                    if data.get('return_id', ''):
                        all_attributes['return_id'] = data['return_id']

                    item = {
                        "pk_id": purchaseorder_id + "_IN" + inward_id,
                        "sk_timeStamp": time,
                        "all_attributes": all_attributes,
                        "gsipk_table": inward_tablename,
                        "gsisk_id": purchaseorder_id,
                        "lsi_key": '--'
                    }

                    response = db_con.GateEntry.insert_one(item)
                    return {"statusCode": 200, "body": "Record for gate entry created successfully"}
                else:
                    return {"statusCode": 400, "body": "Failed while uploading documents and images"}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Gate Entry creation failed'}
        
    def getGateEntryPopUp(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            get_gate_entry_data = db_con.GateEntry.find_one({"all_attributes.inwardId": data["gate_entry_id"]}, {"_id": 0, 'all_attributes': 1})
            if get_gate_entry_data is not None:
                gate_entry_all_attributes_data = get_gate_entry_data['all_attributes']
                return {'statusCode': 200, 'body': gate_entry_all_attributes_data}
            else:
                return {'statusCode': 400, 'body': 'No record found'}
                        
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Getting Gate Entry Popup Failed'}
        
    def getInwardPopUp(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            inward_data = db_con.inward.find_one({"all_attributes.inwardId": data["inward_id"]}, {"_id": 0, 'all_attributes': 1})
            if inward_data is not None:
                inward_all_attributes_data = inward_data['all_attributes']
                return {'statusCode': 200, 'body': inward_all_attributes_data}
            else:
                return {'statusCode': 400, 'body': 'No record found'}
            
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Getting Inward Popup Failed'}
    
    def getIQCPopUp(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            iqc_data = db_con.QATest.find_one({"all_attributes.inwardId": data["iqc_id"]}, {"_id": 0, 'all_attributes': 1})
            if iqc_data is not None:
                iqc_all_attributes_data = iqc_data["all_attributes"]
                return {'statusCode': 200, 'body': iqc_all_attributes_data}
            else:
                return {'statusCode': 400, 'body': 'No record found'}
            
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Getting IQC Popup Failed'}
        
    def saveCommentsForPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            
            pod_id = data['po_id']
            inward_id = data['inward_id']
            attachment_dict = {}
            if "attachment" in data.keys() and data["attachment"]:
                for attachment in data['attachment']:
                    document_body = attachment['doc_body']
                    document_name = attachment['doc_name']
                    extra_type = ""
                    attachment_url = file_uploads.upload_file("GateEntry", "PtgCms" + env_type, extra_type, "GateEntry" + pod_id, document_name, document_body)
                    attachment_dict[document_name] = attachment_url  # Adds or updates the dictionary entry for each attachment
            else:
                attachment_dict = {}

            comment_data = {
                "created_time": datetime.now().isoformat(),
                "comment": data["comment"],
                "attachments": attachment_dict  # This dictionary now contains all attachments
            }
            gate_entry_result = db_con.GateEntry.find_one({"pk_id": inward_id}, {"_id": 0, "all_attributes": 1})
            comments_dict = gate_entry_result.get('all_attributes', {}).get('comments', {})
            if not isinstance(comments_dict, dict):
                if isinstance(comments_dict, list):
                    comments_dict = {f"comment{i + 1}": v for i, v in enumerate(comments_dict)}
                else:
                    comments_dict = {}
            new_comment_key = f"comment{len(comments_dict) + 1}"
            # Add the new comment to the dictionary
            comments_dict[new_comment_key] = comment_data
            db_con.GateEntry.update_one(
                    {"pk_id": inward_id},
                    {"$set": {"all_attributes.comments": comments_dict}}
            )
            # db_con.inward.update_one(
            #         {"inward_id": inward_id},
            #         {"$set": {"all_attributes": comment_attachement_data}}
            # )
            # db_con.IQTest.update_one(
            #         {"inward_id": inward_id},
            #         {"$set": {"all_attributes": comment_attachement_data}}
            # )
            result = list(db_con.GateEntry.find({"pk_id": inward_id}, {"_id": 0}))
            return{'statusCode': 200, 'body': 'Comment added successfully'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Comment adding failed'}
        
        




    def cmsNewInwardGetQatestId(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            po_id = data['po_id']
            result = db_con.QATest.find({"all_attributes.document_id": po_id})
            output_result = list(result)
            listOfPkIds = []
            for i in range(len(output_result)):
              listOfPkIds.append(output_result[i]["pk_id"])
            if listOfPkIds:  
              return {"statusCode":200,"body": listOfPkIds}
            else:
              return {"statusCode":400,"body": "No data found"}
           
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
    def cmsNewPurchaseOrdersInwardGetById(request_body):
        try:
            data = request_body  
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            po_id = data['document_id']
            inward_id = data['inward_id']
            result = list(db_con.QATest.find({"all_attributes.inwardId": inward_id},{'_id':0}))
            po_id=result[0]['gsisk_id']
            parts = []
            result = list(db_con.QATest.find({"all_attributes.inwardId": inward_id},{'_id':0}))

            if result:
                category = list(
                    db_con.Metadata.find({}, {"pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1}))
                category = {
                    item['pk_id'].replace("MDID", "CTID"): (
                        {
                            "ctgr_name": item['gsisk_id'],
                            "sub_categories": {
                                key: value for key, value in item['sub_categories'].items()
                            }
                        }
                        if item['gsipk_id'] == 'Electronic'
                        else {"ctgr_name": item['gsisk_id']}
                    )
                    for item in category
                }

                inventory = list(db_con.Inventory.find({}, {"pk_id": 1, "all_attributes.description": 1,
                                                            "all_attributes.package": 1, "all_attributes.mfr": 1,
                                                            "all_attributes.cmpt_id": 1,
                                                            "all_attributes.prdt_name": 1,
                                                            "all_attributes.department": 1,
                                                            "all_attributes.sub_ctgr": 1}))
                inventory = {item['pk_id']: item for item in inventory}
                response = {}
                response['order_no'] = po_id
                response['QA_id'] = result[0]['pk_id']
                response['inward_id'] = result[0]['all_attributes'].get('inwardId', "")
                response['vendor_id'] = result[0]['all_attributes'].get('vendorId', "")
                response['order_date'] = result[0]['all_attributes'].get('gate_entry_date', "")
                response['description'] = result[0]['all_attributes'].get('description', "")
                response['invoice'] = file_get(result[0]['all_attributes'].get('invoice', ""))
                response['invoice_num'] = result[0]['all_attributes'].get('invoice_num', "")
                response['qa_date'] = result[0]['all_attributes'].get('QA_date', "")
                response['invoice_name'] = result[0]['all_attributes'].get('invoice', "").split("/")[-1] if \
                    result[0]['all_attributes'].get('invoice', "") else ""
                response['invoice_photo'] = {i: file_get(result[0]['all_attributes']['photo'][i]) for i in
                                            result[0]['all_attributes']['photo']}
                response['qa_test_document'] = file_get(result[0]['all_attributes'].get('QATest', ""))
                response['qa_test_document_name'] = result[0]['all_attributes'].get('QATest', "").split("/")[-1] if \
                    result[0]['all_attributes'].get('QATest', "") else ""

                for key in result[0]['all_attributes']['parts'].keys():
                    part_info = result[0]['all_attributes']['parts'][key]
                    cmpt_id = part_info['cmpt_id']
                    ctgr_id = part_info['ctgr_id']
                    if part_info['pass_qty'] != '0':
                        parts.append(
                            {
                                "s_no": key.replace("part", ""),
                                "cmpt_id": part_info['cmpt_id'],
                                "ctgr_id": part_info['ctgr_id'],
                                "manufacturer": inventory[part_info['cmpt_id']].get('mfr',
                                                                                    part_info['manufacturer']),
                                "part_no": part_info['mfr_prt_num'],
                                "part_name": category[ctgr_id]['sub_categories'][
                                    inventory[cmpt_id]["all_attributes"]['sub_ctgr']] if
                                inventory[cmpt_id]["all_attributes"]['department'] == 'Electronic' else
                                inventory[cmpt_id]["all_attributes"]['prdt_name'],
                                "description": inventory[part_info['cmpt_id']].get('description',
                                                                                part_info['description']),
                                "packaging": inventory[part_info['cmpt_id']].get('package', part_info['packaging']),
                                "quantity": part_info['qty'],
                                "pass_qty": part_info['pass_qty'],
                                "fail_qty": part_info['fail_qty'],
                                "inventory_position": "",
                                "batchId": part_info.get('batchId', ""),
                                "lot_id": part_info.get("lot_id", "-")
                            }
                        )
                response['parts'] = parts

                # Add excel files
                excel_files = []
                for key, value in result[0]['all_attributes'].items():
                    if key.endswith('.csv') or key.endswith('.pdf')or key.endswith('.xls')or key.endswith('.xlsx'):
                        excel_files.append({
                            "name": key,
                            "url": value
                        })
                response['excel'] = excel_files

                return {'statusCode': 200, 'body': response}
            else:
                return {'statusCode': 200, 'body': "No data found"}
        # else:
        #     return {"statusCode": 400, "body": "Something went wrong, please try again"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {"statusCode": 400, "body": "Internal server error"}
