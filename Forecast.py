import json
from datetime import datetime,timedelta
import base64
from db_connection import db_connection_manage
import sys
import os
from bson import ObjectId
import base64
from base64 import b64decode, b64encode
from cms_utils import file_uploads
 
# print('all_qqwjhyqgrqjhekf')
conct = db_connection_manage()
 
class ForcastPurchaseOrder():
    def CmsCreateForcastPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
            document_name = data['forecastInvoice']["doc_name"]
            document_body = data['forecastInvoice']['doc_body']
            # Fetching existing forecast purchase orders
            ForcastPurchaseOrder_data = list(db_con.ForcastPurchaseOrder.find({}, {
                "pk_id": 1,
                "all_attributes.documents": 1,
                "all_attributes.primary_document_details.document_title": 1
            }))
            document_title = [i['all_attributes']['primary_document_details']['document_title'] for i in
                            ForcastPurchaseOrder_data]
            documents = [k for i in ForcastPurchaseOrder_data for k, j in i['all_attributes']['documents'].items()]
            if data["primaryDocumentDetails"]['document_date'] in ["N/A", "NA"]:
                data["primaryDocumentDetails"]['document_date'] = "0000-00-00"
            if data["primaryDocumentDetails"]['delivery_date'] in ["N/A", "NA"]:
                data["primaryDocumentDetails"]['delivery_date'] = "0000-00-00"
            if any(int(i['quantity']) <= 0 for i in data["forecastDetails"]):
                return {"statusCode": 400, "body": "Should not upload quantity less or equal to 0"}
            if any(float(i['order_value']) <= 0 for i in data["forecastDetails"]):
                return {"statusCode": 400, "body": "Should not upload order_value less than or equal 0"}
            if document_name[:-4] in documents:
                return {'statusCode': 400, "body": "Cannot upload duplicate file name"}
            draft_ForcastPurchaseOrder = list(db_con.DraftForcastPurchaseOrder.find({}, {
                "pk_id": 1,
                "all_attributes.documents": 1,
                "all_attributes.primary_document_details.document_title": 1
            }))
            document_title_draft = [i['all_attributes']['primary_document_details']['document_title'] for i in
                                    draft_ForcastPurchaseOrder]
            documents_draft = [k for i in draft_ForcastPurchaseOrder for k, j in
                            i['all_attributes']['documents'].items()]
            # Generate new forecast purchase order ID
            forecast_purchase_order_id = '1'
            if ForcastPurchaseOrder_data:
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                if "ForcastPurchaseOrder" in update_id[0]['all_attributes']:
                    update_id = (update_id[0]['all_attributes']['ForcastPurchaseOrder'][4:])
                else:
                    update_id = "1"
                forecast_purchase_order_id = str(int(update_id) + 1)
            print(forecast_purchase_order_id)
            filesLst = {"documents": {}}
            extra_type = ''
            if "forecastInvoice" in data and data["forecastInvoice"].get('doc_body') and data["forecastInvoice"].get(
                    'doc_name'):
                doc_name = data["forecastInvoice"]["doc_name"][:-4]
                doc_body = data["forecastInvoice"]["doc_body"]
                file_key = file_uploads.upload_file("Forecast", "PtgCms" + env_type, extra_type,
                                                    "forecastpurchaseOrder_" + forecast_purchase_order_id,
                                                    data["forecastInvoice"]["doc_name"], doc_body)
                filesLst["documents"][doc_name] = file_key
            all_attributes = {}
            buyer_details = data['buyerDetails']
            delivery_location = data['deliveryLocation']
            supplier_details = data['supplierDetails']
            supplierLocation = data['supplierLocation']
            primary_document_details = data['primaryDocumentDetails']
            if primary_document_details['document_title'] in document_title:
                return {'statusCode': 400, "body": "Cannot upload duplicate document title"}
            if primary_document_details['document_title'] in document_title_draft:
                return {'statusCode': 200,
                        "message": "Cannot upload duplicate document title which is already present in drafts"}
            if document_name[:-4] in documents_draft:
                return {'statusCode': 200,
                        "message": "Cannot upload duplicate document file name which is already present in drafts"}
            forecastDetails = {f"forecast{inx + 1}": value.update(
                {"order_status": "", "payment_status": "", "po_name": "__",
                "cmts_atcmts": {}}) or value for inx, value in enumerate(data['forecastDetails'])}
            # document_month_year = datetime.strptime(primary_document_details['document_date'], '%Y-%m-%d').strftime(
            #     '%m-%y')

            document_date = primary_document_details['document_date']
            document_month = datetime.strptime(document_date, '%Y-%m-%d').strftime('%m')
            document_year = datetime.strptime(document_date, '%Y-%m-%d').strftime('%y')
            next_year = str(int(document_year) + 1).zfill(2)
            document_month_year = f"{document_month}/{document_year}-{next_year}"


            all_attributes["fcpo_id"] = f"EPL/FCPO/{forecast_purchase_order_id}/{document_month_year}"
            all_attributes['buyer_details'] = buyer_details
            all_attributes["delivery_location"] = delivery_location
            all_attributes["supplier_details"] = supplier_details
            all_attributes["supplierLocation"] = supplierLocation
            all_attributes["time_line_status"] = "PO"
            all_attributes["primary_document_details"] = primary_document_details
            all_attributes["forecast_details"] = forecastDetails
            all_attributes['last_modified_date'] = sk_timeStamp[:10]
            all_attributes.update(filesLst)
            item = {
                "pk_id": "FCPO" + forecast_purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": all_attributes,
                "gsipk_table": "ForcastPurchaseOrder",
                "gsisk_id": "open",
                "lsi_key": "Pending"
            }
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}
            db_con.ForcastPurchaseOrder.insert_one(item)
            update_data = {
                '$set': {
                    'all_attributes.ForcastPurchaseOrder': "FCPO" + forecast_purchase_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            response = {'statusCode': 200, 'body': 'Forecast Purchase Order created successfully'}
            return response
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
    
    def CmsGetClientIdForcastPurchaseOrderDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']       
            client = db_conct['client']
            bom_name = list(db_con.Clients.find({}, {'_id': 0, 'client_id': '$all_attributes.client_id', 'client_name': '$all_attributes.client_name'}))
            if bom_name:
                
                return {"statusCode":200,
                    "body":bom_name
                }
            else: 
                return{"statusCode":404,
                        "body":"No data found "}
                        
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
    def cmsForecastPOGetBomsForClientName(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']       
            client = db_conct['client']
            client_name = data['client_name']
            if client_name:
                
                boms=list(db_con.BOM.find({},{'_id':0,'all_attributes.bom_name':1,'all_attributes.bom_id':1}))
                boms = {item['all_attributes']['bom_id']:item['all_attributes']['bom_name'] for item in boms}  
                client_boms=list(db_con.Clients.find({},{'_id':0,'all_attributes.client_name':1,'all_attributes.boms':1}))
                client_boms = [item for item in client_boms if item['all_attributes']['client_name'].strip().lower()==data['client_name'].strip().lower()]
                if client_boms:
                    client_boms = client_boms[0]['all_attributes']['boms']
                    for key in client_boms:
                        print(key)
                    client_boms  = [{"bom_id":client_boms[key]['bom_id'],"bom_name": boms[client_boms[key]['bom_id']]} for key in client_boms.keys()]
                    return {'statusCode': 200,'body': client_boms}
                else:
                    return {'statusCode': 200,'body': "No BOMS found for the client"}
            else:
                return {'statusCode': 200,'body': "Please provide a valid client name"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}
    def CmsForcastPurchaseOrderPostComment(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            databaseTableName = f"PtgCms{data['env_type']}"
           
            pk_id = data["fc_po_id"]
            time_atch = datetime.now().isoformat()
           
            # Query MongoDB for the forecast purchase order details
            result = list(db_con["ForcastPurchaseOrder"].find({"gsipk_table": "ForcastPurchaseOrder", "pk_id": pk_id}))
           
            if result:
                fo_data = result[0]["all_attributes"]["forecast_details"]
                pk_id = result[0]["pk_id"]
                sk_timeStamp = result[0]["sk_timeStamp"]
               
                for key, value in fo_data.items():
                    if key.startswith('forecast') and value.get('po_name') == data['po_name']:
                        comment_details = {
                            "comment": data.get("comment", ""),
                            "doc_time": time_atch
                        }
                       
                        if "attachment" in data.keys() and data["attachment"]:
                            for attachment in data['attachment']:
                                document_body = attachment['doc_body']
                                document_name = attachment['doc_name']
                                extra_type = ""
                                attachment_url = file_uploads.upload_file("Forecast", "PtgCms"+env_type, extra_type, "forecastpurchaseOrder_" + pk_id, document_name, document_body)
                               
                                # Create cmts_atcmts entry if not exists
                                value.setdefault("cmts_atcmts", {})
                               
                                # Calculate the next available index for cmts_atcmts
                                max_index = max([int(k.split("_")[-1]) for k in value.get("cmts_atcmts", {}).keys()], default=0)
                                next_index = max_index + 1
                               
                                # Create the key with the next available index and set its value to comment_details
                                value["cmts_atcmts"][f"cmts_atcmts_{next_index}"] = {
                                    "comment": comment_details["comment"],
                                    "doc_time": comment_details["doc_time"],
                                    "doc_body": attachment_url,
                                    "doc_name": document_name
                                }
                        else:
                            # If no attachments provided, add comment details without attachments
                            # Create cmts_atcmts entry if not exists
                            value.setdefault("cmts_atcmts", {})
                           
                            # Calculate the next available index for cmts_atcmts
                            max_index = max([int(k.split("_")[-1]) for k in value.get("cmts_atcmts", {}).keys()], default=0)
                            next_index = max_index + 1
                           
                            # Create the key with the next available index and set its value to comment_details
                            value["cmts_atcmts"][f"cmts_atcmts_{next_index}"] = {
                                "comment": comment_details["comment"],
                                "doc_time": comment_details["doc_time"]
                            }
               
                # Update the document in MongoDB
                db_con["ForcastPurchaseOrder"].update_one(
                    {"pk_id": pk_id},
                    {"$set": {"all_attributes.forecast_details": fo_data}}
                )
               
                return {"statusCode": 200, "body": "Comment added successfully"}
            else:
                return {"statusCode": 404, "body": "No forecast purchase order found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check event)'}
 
    def CmsGetInnerForcastPurchaseOrderDetails(request_body):
            # try:
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        databaseTableName = f"PtgCms{data['env_type']}"
        collection_name = "ForcastPurchaseOrder"
        pk_id = data["fc_po_id"]
        # Query MongoDB for the forecast purchase order details
        result = list(db_con[collection_name].find({"gsipk_table": collection_name, "pk_id": pk_id}))
        if result:
            fo_data = result[0]["all_attributes"]["forecast_details"]
            bom_name = result[0]["all_attributes"]["primary_document_details"]["bom_name"]
            df = [
                {
                    "month": value["month"],
                    "date": value["due_date"],
                    "bom_name": bom_name,
                    "quantity": value["quantity"],
                    "order_value": value["order_value"],
                    "payment_status": value["payment_status"],
                    "order_status": value["order_status"],
                    "doc_count": sum('doc_name' in value for value in value["cmts_atcmts"].values()),
                    "comment": sum('comment' in value for value in value["cmts_atcmts"].values()),
                    "attachments_cmnts": {
                        key: {
                            "comment": value.get("comment", ""),
                            "doc_body": ForcastPurchaseOrder.get_file_single_image(value.get("doc_body", "")),
                            "doc_name": value.get("doc_name", ""),
                            "doc_time": value.get("doc_time", "")
                        }
                        for key, value in sorted(value["cmts_atcmts"].items(), key=lambda x: x[1]["doc_time"], reverse=False)
                    },
                    # "attachments_cmnts": dict(sorted(value["cmts_atcmts"].items(), key=lambda x: x[1]["doc_time"], reverse=False)),
                    "documents": {
                        "content": ForcastPurchaseOrder.get_file_single_image(value.get("forecast_document", "")),
                        "document_name": data["po_name"]
                    }
                    # "forecast_document": value.get("forecast_document", "")
                    # "forecast_document": value.get("forecast_document", "")
                }
                for key, value in fo_data.items()
                if key.startswith("forecast") and value["po_name"] == data["po_name"]
            ]
            if df:
                return {"statusCode": 200, "body": df[0]}
            else:
                return {"statusCode": 404, "body": "No data found"}
        else:
            return {"statusCode": 404, "body": "No data found"}
        

    
    def CmsGetForcastPurchaseOrderDetailsList(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            collection_name = "ForcastPurchaseOrder"

            # Query MongoDB for the forecast purchase orders
            result = list(db_con[collection_name].find({'gsipk_table':'ForcastPurchaseOrder', 'lsi_key': 'Approved'}, {'_id': 0}))
            cfpo = list(db_con[collection_name].find({'gsipk_table':'ClientForcastPurchaseOrder', 'lsi_key': 'Approved'}, {'_id': 0}))
            result += cfpo

            # Transform the results to the desired structure
            response_body = []
            for i in result:
                document_date_str = i["all_attributes"]["primary_document_details"].get("document_date")
                delivery_date_str = i["all_attributes"]["primary_document_details"].get("delivery_date")
                sk_timeStamp_str = i.get("sk_timeStamp", "")[:10]

                # Ensure date fields are strings
                if document_date_str and delivery_date_str and sk_timeStamp_str:
                    delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
                    sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
                    document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
                    days_left = max(0, (delivery_date - document_date).days)
                else:
                    delivery_date = sk_timeStamp = document_date = None
                    days_left = 0

                docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
                        i["all_attributes"].get("documents", {}).items()]
                document_url = docs[0]["content"] if docs else ""

                formatted_order = {
                    "fcpo_id": i['all_attributes'].get("fcpo_id", ""),
                    # "Client_Purchaseorder_num":i['all_attributes'].get("Client_Purchaseorder_num",""),
                    "buyer_details": i['all_attributes'].get("buyer_details", ""),
                    "delivery_location": i['all_attributes'].get("delivery_location", ""),
                    "delivery_date": f"{days_left} days left",
                    "supplier_details": i['all_attributes'].get("supplier_details", ""),
                    "supplierLocation": i['all_attributes'].get("supplierLocation", ""),
                    "payment_status": i.get('gsisk_id', ''),
                    "modified_date": sk_timeStamp_str,
                    "fc_po_ids": i.get('pk_id', ""),
                    "primary_document_details": i['all_attributes'].get("primary_document_details", {}),
                    "forecast_details": [],
                    "last_modified_date": i['all_attributes'].get("last_modified_date", ""),
                    "documents_url": document_url
                }

                # Get forecast details
                forecast_details = i['all_attributes'].get("forecast_details", {})
                # Check if Client_puechaseorder_num starts with "EPL/FCPO"
                if formatted_order["fcpo_id"].startswith("EPL/FCPO"):
                    for forecast_key, forecast_value in forecast_details.items():
                        monthly_status = False if forecast_value.get("po_name", "__") == "__" else True
                        forecast_value["monthly_status"] = monthly_status
                        if forecast_value.get("po_name", "")[-4:] == '.pdf':
                            forecast_value["forecast_document"] = forecast_value.get("po_name", "")
                        formatted_order["forecast_details"].append({forecast_key: forecast_value})
                    # Only add total_amount and grand_total if they are not empty
                    total_amount = i['all_attributes'].get("total_amount", {})
                    
                    grand_total = i['all_attributes'].get("grand_total", {})
                    if total_amount:
                        formatted_order["total_amount"] = total_amount
                    if grand_total:
                        formatted_order["grand_total"] = grand_total
                else:
                    formatted_order["Client_Purchaseorder_num"] = i['all_attributes'].get("Client_Purchaseorder_num", {})
                    formatted_order["forecast_details"] = forecast_details
                    formatted_order["total_amount"] = i['all_attributes'].get("total_amount", {})
                    formatted_order["grand_total"] = i['all_attributes'].get("grand_total", {})

                response_body.append(formatted_order)

            # Query MongoDB for approved purchase orders
            po_list = list(db_con.NewPurchaseOrder.find({'lsi_key': 'Approved'}, {"_id": 0}))
            po_list1 = [i['all_attributes'] for i in po_list]
            l2 = []
            for po in po_list1:
                l1 = []
                for part in (po.get('purchase_list',{}) or po.get('job_work_table', {})).values():
                    delivery_date = part.get('delivery_date')
                    if delivery_date:
                        l1.append(delivery_date)
                l2.append(max(l1) if l1 else None)

            po_date_list = [i['primary_document_details'].get('po_date') for i in po_list1]
            l2 = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in l2]
            po_date_list = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in po_date_list]

            days_difference = [max(0, (delivery_date - po_date).days) if delivery_date and po_date else 0 for
                            delivery_date, po_date in zip(l2, po_date_list)]

            for i in range(len(po_list1)):
                po_list1[i]['due_date'] = f"{days_difference[i]} days left"
                po_list1[i]['modified_date'] = po_list[i].get('sk_timeStamp', '')[:10]
                po_list1[i]['payment_status'] = po_list[i].get('gsisk_id', '')

            response_body.extend(po_list1)

            # Query MongoDB for service orders
            # so_list = list(db_con.NewPurchaseOrder.find({'gsipk_table': 'ServiceOrder'}, {"_id": 0}))
            # so_list1 = [i['all_attributes'] for i in so_list]
            # l3 = []
            # for so in so_list1:
            #     l1 = []
            #     for part in so['job_work_table'].values():
            #         delivery_date = part.get('delivery_date')
            #         if delivery_date:
            #             l1.append(delivery_date)
            #     l3.append(max(l1) if l1 else None)

            # so_date_list = [i['primary_document_details'].get('so_date') for i in so_list1]
            # l3 = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in l3]
            # so_date_list = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in so_date_list]

            # so_days_difference = [max(0, (delivery_date - so_date).days) if delivery_date and so_date else 0 for
            #                     delivery_date, so_date in zip(l3, so_date_list)]

            # for i in range(len(so_list1)):
            #     so_list1[i]['due_date'] = f"{so_days_difference[i]} days left"
            #     so_list1[i]['modified_date'] = so_list[i].get('sk_timeStamp', '')[:10]
            #     so_list1[i]['payment_status'] = so_list[i].get('gsisk_id', '')
            
            # response_body.extend(so_list1)
            # inv_list = list(db_con.NewPurchaseOrder.find({'gsipk_table': 'Invoice'}, {"_id": 0}))
            # inv_list1 = [i['all_attributes'] for i in inv_list]


            # inv_list = list(db_con.NewPurchaseOrder.find({'gsipk_table': 'Invoice'}, {"_id": 0}))
            # inv_list1 = [i['all_attributes'] for i in inv_list]
            # inv_list1 = [
            #             {**i['all_attributes'], 'payment_status': i['gsisk_id'], 'modified_date': i['sk_timeStamp'][:10]}
            #             for i in inv_list
            #             ]
            # print(inv_list1)

            # l4 = []
            # for inv in inv_list1:
            #     l1 = []
            #     for part in inv['purchase_list'].values():
            #         delivery_date = part.get('delivery_date')
            #         if delivery_date:
            #             l1.append(delivery_date)
            #     l4.append(max(l1) if l1 else None)

            # inv_date_list = [i['primary_doc_details'].get('invoice_date') for i in inv_list1]
            # l4 = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in l4]
            # inv_date_list = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in inv_date_list]

            # inv_days_difference = [max(0, (delivery_date - invoice_date).days) if delivery_date and invoice_date else 0 for
            #                     delivery_date, invoice_date in zip(l4, inv_date_list)]

            # for i in range(len(inv_list1)):
            #     inv_list1[i]['due_date'] = f"{inv_days_difference[i]} days left"
            #     inv_list1[i]['modified_date'] = inv_list[i].get('sk_timeStamp', '')[:10]
            #     inv_list1[i]['payment_status'] = inv_list[i].get('gsisk_id', '')

            # response_body.extend(inv_list1)





            proinv_list = list(db_con.ProformaInvoice.find({'gsipk_table': 'ProformaInvoice', 'lsi_key':'Approved'}, {"_id": 0}))
            print(proinv_list)
            # proinv_list1 = [i['all_attributes'] for i in proinv_list]
            proinv_list1 = [
                        {**i['all_attributes'], 'payment_status': i['gsisk_id'], 'modified_date': i['sk_timeStamp'][:10]}
                        for i in proinv_list
                        ]
            # l5 = []
            # for inv in proinv_list1:
            #     l1 = []
            #     for part in inv['purchase_list'].values():
            #         delivery_date = part.get('delivery_date')
            #         if delivery_date:
            #             l1.append(delivery_date)
            #     l5.append(max(l1) if l1 else None)

            # proinv_date_list = [i['primary_doc_details'].get('invoice_date') for i in proinv_list1]
            # l5 = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in l4]
            # proinv_date_list = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in proinv_date_list]

            # inv_days_difference = [max(0, (delivery_date - invoice_date).days) if delivery_date and invoice_date else 0 for
            #                     delivery_date, invoice_date in zip(l4, proinv_date_list)]

            # for i in range(len(proinv_list1)):
            #     # proinv_list1[i]['due_date'] = f"{inv_days_difference[i]} days left"
            #     # proinv_list1[i]['modified_date'] = inv_list[i].get('sk_timeStamp', '')[:10]
            #     # proinv_list1[i]['payment_status'] = inv_list[i].get('gsisk_id', '')
            # for i in proinv_list:
            #     proinv_list1[i]['modified_date'] = i.get('sk_timeStamp', '')[:10]
            #     proinv_list1[i]['payment_status'] = i.get('gsisk_id', '')

            response_body.extend(proinv_list1)

            return {"statusCode": 200, "body": response_body}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check event)'}




    # def CmsGetForcastPurchaseOrderDetailsList(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         collection_name = "ForcastPurchaseOrder"

    #         # Query MongoDB for the forecast purchase orders
    #         result = list(db_con[collection_name].find({}, {'_id': 0}))

    #         # Transform the results to the desired structure
    #         response_body = []
    #         for i in result:
    #             document_date_str = i["all_attributes"]["primary_document_details"].get("document_date")
    #             delivery_date_str = i["all_attributes"]["primary_document_details"].get("delivery_date")
    #             sk_timeStamp_str = i.get("sk_timeStamp", "")[:10]

    #             # Ensure date fields are strings
    #             if document_date_str and delivery_date_str and sk_timeStamp_str:
    #                 delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
    #                 sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
    #                 document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
    #                 days_left = max(0, (delivery_date - document_date).days)
    #             else:
    #                 delivery_date = sk_timeStamp = document_date = None
    #                 days_left = 0

    #             docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
    #                     i["all_attributes"].get("documents", {}).items()]
    #             document_url = docs[0]["content"] if docs else ""

    #             formatted_order = {
    #                 "Client_Purchaseorder_num": i['all_attributes'].get("Client_Purchaseorder_num", ""),
    #                 "buyer_details": i['all_attributes'].get("buyer_details", ""),
    #                 "delivery_location": i['all_attributes'].get("delivery_location", ""),
    #                 "delivery_date": f"{days_left} days left",
    #                 "supplier_details": i['all_attributes'].get("supplier_details", ""),
    #                 "supplierLocation": i['all_attributes'].get("supplierLocation", ""),
    #                 "payment_status": i.get('gsisk_id', ''),
    #                 "modified_date": sk_timeStamp_str,
    #                 "fc_po_ids": i.get('pk_id', ""),
    #                 "primary_document_details": i['all_attributes'].get("primary_document_details", {}),
    #                 "forecast_details": [],
    #                 "last_modified_date": i['all_attributes'].get("last_modified_date", ""),
    #                 "documents_url": document_url
    #             }

    #             # Get forecast details
    #             forecast_details = i['all_attributes'].get("forecast_details", {})
    #             # Check if Client_puechaseorder_num starts with "EPL/FCPO"
    #             if formatted_order["Client_Purchaseorder_num"].startswith("EPL/FCPO"):
    #                 for forecast_key, forecast_value in forecast_details.items():
    #                     monthly_status = False if forecast_value.get("po_name", "__") == "__" else True
    #                     forecast_value["monthly_status"] = monthly_status
    #                     if forecast_value.get("po_name", "")[-4:] == '.pdf':
    #                         forecast_value["forecast_document"] = forecast_value.get("po_name", "")
    #                     formatted_order["forecast_details"].append({forecast_key: forecast_value})
    #                 # Only add total_amount and grand_total if they are not empty
    #                 total_amount = i['all_attributes'].get("total_amount", {})
    #                 grand_total = i['all_attributes'].get("grand_total", {})
    #                 if total_amount:
    #                     formatted_order["total_amount"] = total_amount
    #                 if grand_total:
    #                     formatted_order["grand_total"] = grand_total
    #             else:
    #                 formatted_order["forecast_details"] = forecast_details
    #                 formatted_order["total_amount"] = i['all_attributes'].get("total_amount", {})
    #                 formatted_order["grand_total"] = i['all_attributes'].get("grand_total", {})

    #             response_body.append(formatted_order)

    #         # Query MongoDB for approved purchase orders
    #         po_list = list(db_con.NewPurchaseOrder.find({'lsi_key': 'Approved'}, {"_id": 0}))
    #         po_list1 = [i['all_attributes'] for i in po_list]
    #         l2 = []
    #         for po in po_list1:
    #             l1 = []
    #             for part in po['purchase_list'].values():
    #                 delivery_date = part.get('delivery_date')
    #                 if delivery_date:
    #                     l1.append(delivery_date)
    #             l2.append(max(l1) if l1 else None)

    #         po_date_list = [i['primary_document_details'].get('po_date') for i in po_list1]
    #         l2 = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in l2]
    #         po_date_list = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in po_date_list]

    #         days_difference = [max(0, (delivery_date - po_date).days) if delivery_date and po_date else 0 for
    #                            delivery_date, po_date in zip(l2, po_date_list)]

    #         for i in range(len(po_list1)):
    #             po_list1[i]['due_date'] = f"{days_difference[i]} days left"
    #             po_list1[i]['modified_date'] = po_list[i].get('sk_timeStamp', '')[:10]
    #             po_list1[i]['payment_status'] = po_list[i].get('gsisk_id', '')

    #         response_body.extend(po_list1)

            # po_list1 = list(db_con.NewPurchaseOrder.find({'gsipk_table': 'ServiceOrder'}, {"_id": 0}))
            # po_list2 = [i['all_attributes'] for i in po_list1]
            # l2 = []
            # for po in po_list2:
            #     l1 = []
            #     for part in po['job_work_table'].values():
            #         delivery_date = part.get('delivery_date')
            #         if delivery_date:
            #             l1.append(delivery_date)
            #     l2.append(max(l1) if l1 else None)

            # po_date_list = [i['primary_document_details'].get('po_date') for i in po_list2]
            # l2 = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in l2]
            # po_date_list = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in po_date_list]

            # days_difference = [max(0, (delivery_date - po_date).days) if delivery_date and po_date else 0 for
            #                    delivery_date, po_date in zip(l2, po_date_list)]

            # for i in range(len(po_list2)):
            #     po_list2[i]['due_date'] = f"{days_difference[i]} days left"
            #     po_list2[i]['modified_date'] = po_list[i].get('sk_timeStamp', '')[:10]
            #     po_list2[i]['payment_status'] = po_list[i].get('gsisk_id', '')

            # response_body.extend(po_list2)

            # conct.close_connection(client)
        #     return {"statusCode": 200, "body": response_body}

        # except Exception as err:
        #     exc_type, exc_obj, tb = sys.exc_info()
        #     f_name = tb.tb_frame.f_code.co_filename
        #     line_no = tb.tb_lineno
        #     print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
        #     return {'statusCode': 400, 'body': 'Bad Request (check event)'}



    # def CmsGetForcastPurchaseOrderDetailsList(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']       
    #         client = db_conct['client']
    #         collection_name = "ForcastPurchaseOrder"
            
    #         # Query MongoDB for the forecast purchase orders
    #         result = list(db_con[collection_name].find({}, {'_id': 0}))
            
    #         # Transform the results to the desired structureq
    #         response_body = []
    #         for i in result:
    #             document_date_str = i["all_attributes"]["primary_document_details"]["document_date"]
    #             delivery_date_str = i["all_attributes"]["primary_document_details"]["delivery_date"]
    #             sk_timeStamp_str = i["sk_timeStamp"][:10]
    #             delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
    #             sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
    #             document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
    #             days_left = max(0, (delivery_date - document_date).days)
    #             docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in i["all_attributes"]["documents"].items()]
    #             document_url = docs[0]["content"] if docs else ""

    #             formatted_order = {
    #                 "Client_Purchaseorder_num": i['all_attributes'].get("Client_Purchaseorder_num", ""),
    #                 "buyer_details": i['all_attributes'].get("buyer_details", ""),
    #                 "delivery_location": i['all_attributes'].get("delivery_location", ""),
    #                 "delivery_date": f"{days_left} days left",
    #                 "supplier_details": i['all_attributes'].get("supplier_details", ""),
    #                 "supplierLocation": i['all_attributes'].get("supplierLocation", ""),
    #                 "payment_status": i.get('gsisk_id', ''),
    #                 "modified_date":i.get("sk_timeStamp", "")[:10],
    #                 "fc_po_ids": i['pk_id'],
    #                 "primary_document_details": i['all_attributes'].get("primary_document_details", {}),
    #                 "forecast_details": [],
    #                 "last_modified_date": i['all_attributes'].get("last_modified_date", ""),
    #                 "documents_url": document_url
    #             }

    #             # Get forecast details
    #             forecast_details = i['all_attributes'].get("forecast_details", {})
    #             # Check if Client_puechaseorder_num starts with "EPL/FCPO"
    #             if formatted_order["Client_Purchaseorder_num"].startswith("EPL/FCPO"):
    #                 for forecast_key, forecast_value in forecast_details.items():
    #                     monthly_status = False if forecast_value.get("po_name", "__") == "__" else True
    #                     forecast_value["monthly_status"] = monthly_status
    #                     if forecast_value.get("po_name", "")[-4:] == '.pdf':
    #                         forecast_value["forecast_document"] = forecast_value.get("po_name", "")
    #                     formatted_order["forecast_details"].append({forecast_key: forecast_value})
    #                 # Only add total_amount and grand_total if they are not empty
    #                 total_amount = i['all_attributes'].get("total_amount", {})
    #                 grand_total = i['all_attributes'].get("grand_total", {})
    #                 if total_amount:
    #                     formatted_order["total_amount"] = total_amount
    #                 if grand_total:
    #                     formatted_order["grand_total"] = grand_total
    #             else:
    #                 formatted_order["forecast_details"] = forecast_details
    #                 formatted_order["total_amount"] = i['all_attributes'].get("total_amount", {})
    #                 formatted_order["grand_total"] = i['all_attributes'].get("grand_total", {})

    #             response_body.append(formatted_order)

    #         # Query MongoDB for approved purchase orders
    #         po_list = list(db_con.NewPurchaseOrder.find({'lsi_key': 'Approved'}, {"_id": 0}))
    #         po_list1 = [i['all_attributes'] for i in po_list]
    #         l2 = []
    #         for po in po_list1:
    #             l1 = []
    #             for part in po['purchase_list'].values():
                    
    #                 delivery_date = part.get('delivery_date')
    #                 l1.append(delivery_date)
    #             l2.append(max(l1))
    #         po_date_list = [i['primary_document_details'].get('po_date') for i in po_list1]
    #         l2 = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in l2]
    #         po_date_list = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in po_date_list]
    #         days_difference = [max(0, (delivery_date - po_date).days) for delivery_date, po_date in zip(l2, po_date_list)]
    #         # days_difference = [(delivery_date - po_date).days for delivery_date, po_date in zip(l2, po_date_list)]
    #         for i in range(len(po_list1)):
    #             po_list1[i]['due_date'] = f"{days_difference[i]} days left" #  f"{days_left} days left",
    #             po_list1[i]['modified_date'] = po_list[i].get('sk_timeStamp', '')[:10]
    #             po_list1[i]['payment_status'] = po_list[i].get('gsisk_id', '')

    #         response_body.extend(po_list1)
            
    #         return {"statusCode": 200, "body": response_body}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check event)'}


    # def CmsGetForcastPurchaseOrderDetailsList(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         collection_name = "ForcastPurchaseOrder"
            
    #         # Query MongoDB for the forecast purchase orders
    #         result = list(db_con[collection_name].find({}, {'_id': 0}))
            
    #         # Transform the results to the desired structure
    #         response_body = []
    #         for i in result:
    #             document_date_str = i["all_attributes"]["primary_document_details"]["document_date"]
    #             delivery_date_str = i["all_attributes"]["primary_document_details"]["delivery_date"]
    #             sk_timeStamp_str = i["sk_timeStamp"][:10]
    #             delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
    #             sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
    #             document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
    #             days_left = max(0, (delivery_date - document_date).days)
    #             docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in i["all_attributes"]["documents"].items()]
    #             document_url = docs[0]["content"] if docs else ""

    #             formatted_order = {
    #                 "Client_Purchaseorder_num": i['all_attributes'].get("Client_Purchaseorder_num", ""),
    #                 "buyer_details": i['all_attributes'].get("buyer_details", ""),
    #                 "delivery_location": i['all_attributes'].get("delivery_location", ""),
    #                 "delivery_date": f"{days_left} days left",
    #                 "supplier_details": i['all_attributes'].get("supplier_details", ""),
    #                 "supplierLocation": i['all_attributes'].get("supplierLocation", ""),
    #                 "status": i['gsisk_id'],
    #                 "fc_po_ids": i['pk_id'],
    #                 "primary_document_details": i['all_attributes'].get("primary_document_details", {}),
    #                 "forecast_details": [],
    #                 "last_modified_date": i['all_attributes'].get("last_modified_date", ""),
    #                 "documents_url": document_url
    #             }

    #             # Get forecast details
    #             forecast_details = i['all_attributes'].get("forecast_details", {})
    #             # Check if Client_puechaseorder_num starts with "EPL/FCPO"
    #             if formatted_order["Client_Purchaseorder_num"].startswith("EPL/FCPO"):
    #                 for forecast_key, forecast_value in forecast_details.items():
    #                     monthly_status = False if forecast_value.get("po_name", "__") == "__" else True
    #                     forecast_value["monthly_status"] = monthly_status
    #                     if forecast_value.get("po_name", "")[-4:] == '.pdf':
    #                         forecast_value["forecast_document"] = forecast_value.get("po_name", "")
    #                     formatted_order["forecast_details"].append({forecast_key: forecast_value})
    #                 # Only add total_amount and grand_total if they are not empty
    #                 total_amount = i['all_attributes'].get("total_amount", {})
    #                 grand_total = i['all_attributes'].get("grand_total", {})
    #                 if total_amount:
    #                     formatted_order["total_amount"] = total_amount
    #                 if grand_total:
    #                     formatted_order["grand_total"] = grand_total
    #             else:
    #                 formatted_order["forecast_details"] = forecast_details
    #                 formatted_order["total_amount"] = i['all_attributes'].get("total_amount", {})
    #                 formatted_order["grand_total"] = i['all_attributes'].get("grand_total", {})

    #             response_body.append(formatted_order)

    #         po_list = list(db_con.PurchaseOrder.find({'lsi_key': 'Approved'}, {"_id": 0, "all_attributes": 1}))
    #         po_list1 = [i['all_attributes'] for i in po_list]
    #         l2 = []
    #         for po in po_list1:
    #             l1 = []
    #             for part in po['purchase_list'].values():
    #                 delivery_date = part.get('delivery_date')
    #                 l1.append(delivery_date)
    #             l2.append(max(l1))
    #         po_date_list = [i['primary_document_details'].get('po_date') for i in po_list1]
    #         l2 = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in l2]
    #         po_date_list = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in po_date_list]
    #         days_difference = [(delivery_date - po_date).days for delivery_date, po_date in zip(l2, po_date_list)]
    #         for i in range(len(po_list1)):
    #             po_list1[i]['due_date'] = days_difference[i]

    #         response_body.extend(po_list1)
            
    #         return {"statusCode": 200, "body": response_body}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check event)'}

        
    # def CmsGetForcastPurchaseOrderDetailsList(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         collection_name = "ForcastPurchaseOrder"
    #         # Query MongoDB for the forecast purchase orders
    #         result = list(db_con[collection_name].find({}, {'_id': 0}))
    #         #print(result)
    #         # Transform the results to the desired structure
    #         response_body = []
    #         for i in result:
    #             document_date_str = i["all_attributes"]["primary_document_details"]["document_date"]
    #             delivery_date_str = i["all_attributes"]["primary_document_details"]["delivery_date"]
    #             sk_timeStamp_str = i["sk_timeStamp"][:10]
    #             delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
    #             sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
    #             document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
    #             days_left = max(0, (delivery_date - document_date).days)

    #             # delivery_date_str = i["all_attributes"]["primary_document_details"]["delivery_date"]
    #             # document_date_str = i["all_attributes"]["primary_document_details"]["document_date"]
    #             # # sk_timeStamp_str = i["sk_timeStamp"][:10]
    #             # delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
    #             # document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
    #             # # sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
    #             # days_left = max(0, (delivery_date - document_date).days)
    #             docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
    #                     i["all_attributes"]["documents"].items()]
    #             document_url = docs[0]["content"] if docs else ""
    #             formatted_order = {
    #                 "Client_Purchaseorder_num": i['all_attributes'].get("Client_Purchaseorder_num", ""),
    #                 "buyer_details": i['all_attributes'].get("buyer_details", ""),
    #                 "delivery_location": i['all_attributes'].get("delivery_location", ""),
    #                 "delivery_date": f"{days_left} days left",
    #                 "supplier_details": i['all_attributes'].get("supplier_details", ""),
    #                 "supplierLocation": i['all_attributes'].get("supplierLocation", ""),
    #                 "status": i['gsisk_id'],
    #                 "fc_po_ids": i['pk_id'],
    #                 "primary_document_details": i['all_attributes'].get("primary_document_details", {}),
    #                 "forecast_details": [],
    #                 "last_modified_date": i['all_attributes'].get("last_modified_date", ""),
    #                 "documents_url": document_url
    #             }
    #             # Get forecast details
    #             forecast_details = i['all_attributes'].get("forecast_details", {})
    #             # Check if Client_puechaseorder_num starts with "EPL/FCPO"
    #             if formatted_order["Client_Purchaseorder_num"].startswith("EPL/FCPO"):
    #                 for forecast_key, forecast_value in forecast_details.items():
    #                     monthly_status = False if forecast_value.get("po_name", "__") == "__" else True
    #                     forecast_value["monthly_status"] = monthly_status
    #                     if forecast_value.get("po_name", "")[-4:] == '.pdf':
    #                         forecast_value["forecast_document"] = forecast_value.get("po_name", "")
    #                     formatted_order["forecast_details"].append({forecast_key: forecast_value})
    #                 # Only add total_amount and grand_total if they are not empty
    #                 total_amount = i['all_attributes'].get("total_amount", {})
    #                 grand_total = i['all_attributes'].get("grand_total", {})
    #                 if total_amount:
    #                     formatted_order["total_amount"] = total_amount
    #                 if grand_total:
    #                     formatted_order["grand_total"] = grand_total
    #             else:
    #                 formatted_order["forecast_details"] = forecast_details
    #                 formatted_order["total_amount"] = i['all_attributes'].get("total_amount", {})
    #                 formatted_order["grand_total"] = i['all_attributes'].get("grand_total", {})

 
    #             po_list=list(db_con.PurchaseOrder.find({'lsi_key':'Approved'},{"_id":0,"all_attributes":1}))
    #             po_list1=[i['all_attributes'] for i in po_list]
    #             l2=[]
    #             for po in po_list1:
    #                 l1=[]
    #                 for part in po['purchase_list'].values():
    #                     delivery_date = part.get('delivery_date')
    #                     l1.append(delivery_date)
    #                 l2.append(max(l1))         
    #             po_date_list=[i['primary_document_details'].get('po_date') for i in po_list1]  
    #             l2 = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in l2]
    #             po_date_list = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in po_date_list]
    #             days_difference = [(delivery_date - po_date).days for delivery_date, po_date in zip(l2, po_date_list)]
    #             for i in range(0,len(po_list1)):
    #                 po_list1[i]['due_date']=days_difference[i]

    #             #response_body.insert(formatted_order)
    #             response_body.append(formatted_order)
    #             response_body.append(po_list1)
    #         return {"statusCode": 200, "body": response_body}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check event)'}
        
        
    # def CmsGetForcastPurchaseOrderDetailsList(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         collection_name = "ForcastPurchaseOrder"
    #         # Query MongoDB for the forecast purchase orders
    #         result = list(db_con[collection_name].find({}, {'_id': 0}))
    #         print(result)
    #         # Transform the results to the desired structure
    #         response_body = []
    #         for i in result:

    #             document_date_str = i["all_attributes"]["primary_document_details"]["document_date"]
    #             delivery_date_str = i["all_attributes"]["primary_document_details"]["delivery_date"]
    #             sk_timeStamp_str = i["sk_timeStamp"][:10]
    #             delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
    #             sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
    #             document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
    #             days_left = max(0, (delivery_date - document_date).days)



    #             # delivery_date_str = i["all_attributes"]["primary_document_details"]["delivery_date"]
    #             # document_date_str = i["all_attributes"]["primary_document_details"]["document_date"]
    #             # # sk_timeStamp_str = i["sk_timeStamp"][:10]
    #             # delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
    #             # document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
    #             # # sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
    #             # days_left = max(0, (delivery_date - document_date).days)
    #             docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
    #                     i["all_attributes"]["documents"].items()]
    #             document_url = docs[0]["content"] if docs else ""
    #             formatted_order = {
    #                 "Client_Purchaseorder_num": i['all_attributes'].get("Client_Purchaseorder_num", ""),
    #                 "buyer_details": i['all_attributes'].get("buyer_details", ""),
    #                 "delivery_location": i['all_attributes'].get("delivery_location", ""),
    #                 "delivery_date": f"{days_left} days left",
    #                 "supplier_details": i['all_attributes'].get("supplier_details", ""),
    #                 "supplierLocation": i['all_attributes'].get("supplierLocation", ""),
    #                 "status": i['gsisk_id'],
    #                 "fc_po_ids": i['pk_id'],
    #                 "primary_document_details": i['all_attributes'].get("primary_document_details", {}),
    #                 "forecast_details": [],
    #                 "last_modified_date": i['all_attributes'].get("last_modified_date", ""),
    #                 "documents_url": document_url
    #             }
    #             # Get forecast details
    #             forecast_details = i['all_attributes'].get("forecast_details", {})
    #             # Check if Client_puechaseorder_num starts with "EPL/FCPO"
    #             if formatted_order["Client_Purchaseorder_num"].startswith("EPL/FCPO"):
    #                 for forecast_key, forecast_value in forecast_details.items():
    #                     monthly_status = False if forecast_value.get("po_name", "__") == "__" else True
    #                     forecast_value["monthly_status"] = monthly_status
    #                     if forecast_value.get("po_name", "")[-4:] == '.pdf':
    #                         forecast_value["forecast_document"] = forecast_value.get("po_name", "")
    #                     formatted_order["forecast_details"].append({forecast_key: forecast_value})
    #                 # Only add total_amount and grand_total if they are not empty
    #                 total_amount = i['all_attributes'].get("total_amount", {})
    #                 grand_total = i['all_attributes'].get("grand_total", {})
    #                 if total_amount:
    #                     formatted_order["total_amount"] = total_amount
    #                 if grand_total:
    #                     formatted_order["grand_total"] = grand_total
    #             else:
    #                 formatted_order["forecast_details"] = forecast_details
    #                 formatted_order["total_amount"] = i['all_attributes'].get("total_amount", {})
    #                 formatted_order["grand_total"] = i['all_attributes'].get("grand_total", {})
    #             response_body.append(formatted_order)
    #         return {"statusCode": 200, "body": response_body}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check event)'}
 
    
    def CmsForcastPurchaseOrderUploadPO(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            
            forecast_id = data['fc_id']
            sk_timeStamp = (datetime.now()).isoformat()
            date_str = data['fc_date']
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            date_iso = date_obj.isoformat()
            date_iso_parts = date_iso.split('T')[0].split('-')
            date_iso = '-'.join(date_iso_parts)
            month_name = date_obj.strftime('%B')
            
            document_name = data["doc_name"]
            document_body = data['doc_body']
            gsipk_table = "ForcastPurchaseOrder"
            
            # Find the forecast info by forecast_id
            forecast_info = db_con[gsipk_table].find_one({"pk_id": forecast_id})
            
            if forecast_info:
                forecast_details = forecast_info['all_attributes']['forecast_details']
                forecast_key = None
                
                # Check for the matching month
                for key, value in forecast_details.items():
                    if value["month"] == month_name:
                        forecast_key = key
                        break
                f_name = "PtgCms" + env_type
                ff_name = "ForcastPO"
                d_name = ''
                if forecast_key:
                    # Correct the call to upload_file with 6 arguments
                    upload_doc = file_uploads.upload_file(ff_name, f_name, d_name, forecast_id, document_name, document_body)
                    if upload_doc:
                        forecast_record = forecast_details[forecast_key]
                        forecast_record['forecast_document'] = upload_doc
                        forecast_record['po_name'] = document_name
                        forecast_record['fc_date'] = date_iso
                        db_con[gsipk_table].update_one(
                            {"pk_id": forecast_id},
                            {"$set": {f"all_attributes.forecast_details.{forecast_key}": forecast_record}}
                        )
                        return {"statusCode": 200, "body": "Forecast record updated successfully"}
                    else:
                        return {"statusCode": 404, "body": "Failed while uploading document"}
                else:
                    return {"statusCode": 404, "body": f"No data found for the given month ({month_name}) in forecast record"}
            else:
                return {"statusCode": 404, "body": "No forecast record found in the database"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
   
    def CmsSaveDraftForecastPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
 
            if 'forecastInvoice' in data and isinstance(data['forecastInvoice'], dict):
                document_name = data['forecastInvoice']["doc_name"]
                document_body = data['forecastInvoice']['doc_body']
            else:
                return {'statusCode': 400, 'body': 'Forecast Invoice data missing'}
 
            if not document_name:
                return {'statusCode': 400, 'body': 'Document name is empty'}
 
            buyer_details = data.get('buyerDetails', {})
            delivery_location = data.get('deliveryLocation', {})
            supplier_details = data.get('supplierDetails', {})
            supplier_location = data.get('supplierLocation', {})
            primary_document_details = data.get('primaryDocumentDetails', {})
 
            gsipk_table = "DraftForcastPurchaseOrder"
 
            documents = [item['document_number'] for item in data.get('documents', [])]
            document_number = primary_document_details.get('document_number')
 
            if document_name[:-4] in documents:
                return {'statusCode': 400, 'body': 'Cannot upload duplicate file name'}
 
            forcast_purchase_order_id = '1'
            forcast_purchase_order = list(db_con.DraftForcastPurchaseOrder.find({}))
            result = list(db_con.DraftForcastPurchaseOrder.find({"gsipk_table": gsipk_table, "pk_id": "DFCPO"+str(forcast_purchase_order_id)}))
            if forcast_purchase_order:
                forcast_purchase_order_ids = [i[("pk_id")] for i in forcast_purchase_order]
                forcast_purchase_order_ids = sorted(forcast_purchase_order_ids,
                                                    key=lambda x: int(''.join(filter(str.isdigit, x[4:]))),
                                                    reverse=True)
                numeric_part = int(forcast_purchase_order_ids[0].split("O")[1]) + 1
                forcast_purchase_order_id = str(numeric_part)
 
            filesLst = {}
            type = 'PDF'
            if document_name[:-4]:
                key = document_name[:-4]
                filename = document_name
                document_content = data["forecastInvoice"]["doc_body"]
                feature_name = "ForcastPO"
                environ = "PtgCms" + env_type
                type_value = ''
                forcast_purchase_order_id = forcast_purchase_order_id
 
                filesLst["documents"] = {
                    key: file_uploads.upload_file(feature_name, environ, type_value, "DFCPO"+forcast_purchase_order_id, filename, document_content)}
 
            if primary_document_details.get('document_title') in documents or document_number in documents:
                return {'statusCode': 400, 'body': 'Cannot upload duplicate document title or number'}
 
            all_attributes = {
                "fc_po_id": "DFCPO" + forcast_purchase_order_id,
                'buyer_details': buyer_details,
                "delivery_location": delivery_location,
                "supplier_details": supplier_details,
                "place_of_supply": supplier_location,
                'time_line_status': "PO",
                "primary_document_details": primary_document_details
            }
            all_attributes.update(filesLst)
 
            item = {
                "pk_id": "DFCPO" + forcast_purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": all_attributes,
                "gsipk_table": gsipk_table,
                "gsisk_id": "__",
                "lsi_key": "__"
            }
            db_con.DraftForcastPurchaseOrder.insert_one(item)
 
            return {'statusCode': 200, 'body': 'Draft Forecast Purchase Order created successfully'}
        except Exception as err:
            exc_type, _, tb = sys.exc_info()
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
 
    def CmsForecastPOGetBomPriceForBomName(request_body):
        try:
            data = request_body
            # print(data)
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # gsipk_table = "BOM"
            bom = list(db_con.BOM.find({}))
            # print(bom)
            clients = list(db_con.Clients.find({}))
            # print(clients)
            client_name = data["client_name"]
            bom_name = data["bom_name"]
            # print(client_name)
            # print(bom_name)
            if client_name:
                bom_query = {
                    "all_attributes.bom_name": bom_name
                }
                boms_cursor = db_con.BOM.find(bom_query, {"all_attributes.bom_name": 1, "all_attributes.bom_id": 1})
                # print(boms_cursor)
                boms = list(boms_cursor)
                # print(boms)
                client_boms_query = {
                    "gsipk_table": "Clients",
                    "all_attributes.client_name": client_name
                }
                client_boms_cursor = db_con.Clients.find(client_boms_query)
                client_boms = list(client_boms_cursor)
                # print(client_boms)
                client_boms = [item for item in client_boms if
                            item['all_attributes']['client_name'].strip().lower() == data['client_name'].strip().lower()]
                print(client_boms)
                if client_boms:
                    client_boms = client_boms[0]['all_attributes']['boms']
                    bom_ids = [bom['all_attributes']['bom_id'] for bom in boms]
                    print(bom_ids) # PTGBOM06
                    # client_bom_prices = [{"bom_price": client_boms[key]['bom1']['price']} for key in client_boms.keys() if
                    #                      client_boms[key]['bom1']['bom_id'] in bom_ids]
                    client_bom_prices = []
                    # for key, value in client_boms.items():
                    #     bom_id = value['bom_id']
                    #     if bom_id in bom_ids:
                    #         client_bom_prices.append({"bom_price": value['price']})
                    client_bom_prices = [{"bom_price": value['price']} for key, value in client_boms.items() if
                                        value['bom_id'] in bom_ids]
                    return {'statusCode': 200, 'body': client_bom_prices[0]}
                else:
                    return {'statusCode': 200, 'body': "No BOMS found for the client"}
            else:
                return {'statusCode': 200, 'body': "Please provide a valid client name"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Internal server error'}
        
    def CmsCreateClientForcastPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
            document_name = data['productlistdoc']["doc_name"]
            document_body = data['productlistdoc']['doc_body']
            # Fetch existing forecast purchase orders
            ClientForcastPurchaseOrder_data = list(db_con.ForcastPurchaseOrder.find({}, {
                "pk_id": 1,
                "all_attributes.documents": 1,
                "all_attributes.primary_document_details.document_title": 1
            }))
            document_title = [i['all_attributes']['primary_document_details']['document_title'] for i in
                            ClientForcastPurchaseOrder_data]
            documents = [k for i in ClientForcastPurchaseOrder_data for k, j in
                        i['all_attributes']['documents'].items()]
            # Validate primary document details
            primary_document_details = data["primary_document_details"]
            if primary_document_details['document_date'] in ["N/A", "NA"]:
                primary_document_details['document_date'] = "0000-00-00"
            if primary_document_details['delivery_date'] in ["N/A", "NA"]:
                primary_document_details['delivery_date'] = "0000-00-00"
            # Add client_name and bom_name to primary_document_details
            primary_document_details['client_name'] = data['primary_document_details']['client_name']
            primary_document_details['bom_name'] = data['primary_document_details']['bom_name']
            # Validate product list details
            for product in data["productlistDetails"]:
                if int(product['qty']) <= 0:
                    return {"statusCode": 400, "body": "Quantity should not be less or equal to 0"}
                if float(product['total_price']) <= 0:
                    return {"statusCode": 400, "body": "Order value should not be less than or equal to 0"}
            # Check for duplicate document name
            if document_name[:-4] in documents:
                return {'statusCode': 400, "body": "Cannot upload duplicate file name"}
            # Fetch draft client forecast purchase orders
            draft_ClientForcastPurchaseOrder = list(db_con.DraftClientForcastPurchaseOrder.find({}, {
                "pk_id": 1,
                "all_attributes.productlistdoc": 1,
                "all_attributes.primary_document_details.document_title": 1
            }))
            document_title_draft = [i['all_attributes']['primary_document_details'] for i in
                                    draft_ClientForcastPurchaseOrder]
            documents_draft = [k for i in draft_ClientForcastPurchaseOrder for k, j in
                            i['all_attributes']['productlistdoc'].items()]
            # Generate forecast purchase order ID
            if ClientForcastPurchaseOrder_data:
                last_order = ClientForcastPurchaseOrder_data[-1]
                last_order_id = int(last_order['pk_id'][4:])
                forecast_purchase_order_id = str(last_order_id + 1)
            else:
                forecast_purchase_order_id = '0'
            print(forecast_purchase_order_id)
            # Handle file upload
            filesLst = {"documents": {}}
            if "productlistdoc" in data and data["productlistdoc"].get('doc_body') and data["productlistdoc"].get(
                    'doc_name'):
                doc_name = data["productlistdoc"]["doc_name"][:-4]
                doc_body = data["productlistdoc"]["doc_body"]
                file_key = file_uploads.upload_file("Forecast", "PtgCms" + env_type, "",
                                                    "forecastpurchaseOrder_" + forecast_purchase_order_id,
                                                    data["productlistdoc"]["doc_name"], doc_body)
                filesLst["documents"][doc_name] = file_key
            # Validate duplicate document title and number
            if primary_document_details['document_title'] in document_title:
                return {'statusCode': 400, "body": "Cannot upload duplicate document title"}
            if primary_document_details['document_title'] in document_title_draft:
                return {'statusCode': 200,
                        "message": "Cannot upload duplicate document title already present in drafts"}
            if document_name[:-4] in documents_draft:
                return {'statusCode': 200,
                        "message": "Cannot upload duplicate document file name already present in drafts"}
            # Prepare all attributes
            primary_document_details['status'] = "Not dispatched"
            # document_month_year = datetime.strptime(primary_document_details['document_date'], '%Y-%m-%d').strftime(
            #     '%m-%y')
            document_date = primary_document_details['document_date']
            document_month = datetime.strptime(document_date, '%Y-%m-%d').strftime('%m')
            document_year = datetime.strptime(document_date, '%Y-%m-%d').strftime('%y')
            next_year = str(int(document_year) + 1).zfill(2)
            document_month_year = f"{document_month}/{document_year}-{next_year}"


            productlistDetails = {f"forecast{inx + 1}": value.update({"cmts_atcmts": {}}) or value for inx, value in
                                enumerate(data['productlistDetails'])}
            all_attributes = {
                "Client_Purchaseorder_num": f"EPL/CFPO/{forecast_purchase_order_id}/{document_month_year}",
                'buyer_details': data['buyerDetails'],
                "delivery_location": data['deliveryLocation'],
                "supplier_details": data['supplierDetails'],
                "supplierLocation": data['supplierLocation'],
                "time_line_status": "PO",
                "primary_document_details": primary_document_details,
                "forecast_details": productlistDetails,
                'last_modified_date': sk_timeStamp[:10],
                "total_amount": data["total_amount"],
                "grand_total": data["grand_total"],
            }
            all_attributes.update(filesLst)
            item = {
                "pk_id": "CFPO" + forecast_purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": all_attributes,
                "gsipk_table": "ClientForcastPurchaseOrder",
                "gsisk_id": "open",
                "lsi_key": "Pending"
            }
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}
            db_con.ForcastPurchaseOrder.insert_one(item)
            update_data = {
                '$set': {
                    'all_attributes.ClientForcastPurchaseOrder': "CFPO" + forecast_purchase_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            if item:
                return {'statusCode': 200, 'body': 'Client Forecast Purchase Order created successfully'}
            else:
                return {"statusCode": 404, "body": "No ClientForcastPurchaseOrder found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
    def CmsGetClientForcastPurchaseOrderDetailsList(request_body):
        try:
            data = request_body
            print(data)
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            result = list(db_con.ForcastPurchaseOrder.find({"gsipk_table": "ClientForcastPurchaseOrder"}, {"_id": 0}))
            print(result)
            # return {'statusCode': 200, 'body': result}
            formatted_data = []
            for item in result:
                delivery_date_str = item["all_attributes"]["primary_document_details"]["delivery_date"]
                sk_timeStamp_str = item["sk_timeStamp"][:10]
                delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
                sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
                days_left = max(0, (delivery_date - sk_timeStamp).days)
                docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
                        item["all_attributes"]["documents"].items()]
                formatted_item = {
                    "document_title": item["all_attributes"]["primary_document_details"]["document_title"],
                    "document_date": item["all_attributes"]["primary_document_details"]["document_date"],
                    "bom_name": item["all_attributes"]["primary_document_details"]["bom_name"],
                    "note": item["all_attributes"]["primary_document_details"]["note"],
                    "document_url": docs[0],
                    "delivery_date": f"{days_left} days left",
                    "payment_terms": item["all_attributes"]["primary_document_details"]["payment_terms"],
                    "Client_puechaseorder_num": item["all_attributes"]["Client_puechaseorder_num"],
                    "sk_timeStamp": item["sk_timeStamp"][:10],
                    "status": item["gsisk_id"],  # Set status here
                    "last_modified_date": item["all_attributes"]["last_modified_date"],
                    "client_name": item["all_attributes"]["primary_document_details"]["client_name"],
                    "productlist_Details": []
                }
                for forecast_key, forecast_value in item["all_attributes"]["productlist_Details"].items():
                    # print(forecast_value)
                    for key, value in forecast_value['cmts_atcmts'].items():
                        if 'doc_body' in value:
                            pass
                        else:
                            forecast_value['cmts_atcmts']['doc_body'] = file_uploads.get_file(value['doc_body'])
                            # monthly_status = False if forecast_value["po_name"] == "__" else True
                    # forecast_value["monthly_status"] = monthly_status
                    formatted_item["productlist_Details"].append({forecast_key: forecast_value})
                formatted_data.append(formatted_item)
            formatted_data_sorted = sorted(formatted_data, key=lambda x: int(x['pk_id'].replace
                                                                             ("CFPO", "")) if isinstance(x,
                                                                                                         dict) and 'pk_id' in x else 0,
                                           reverse=False)
            del formatted_data_sorted["_id"]
            print(formatted_data_sorted)
            if formatted_data_sorted:
                return {"statusCode": 200, "body": formatted_data_sorted}
            else:
                return {"statusCode": 404, "body": "No data found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Exception occurred at line {line_no} in file {f_name}: {err}")
            return {'statusCode': 400, 'body': 'Unable to filter data'}
        

    def cmsGetPurchaseOrderApprovals(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            status = data['status']
            pk_id = data['po_id']
            id = pk_id.split('/')[1]
            print(id)
            if id.startswith('PO'):
                query = list(db_con.NewPurchaseOrder.find({'all_attributes.po_id': pk_id}))
                for i in query:
                    db_con.NewPurchaseOrder.update_one(i, {'$set': {'lsi_key': status}})
                return {"statusCode": 200, "body": "{action} successfully".format(action=status)}
            elif id.startswith('SO'):
                query = list(db_con.NewPurchaseOrder.find({'all_attributes.so_id': pk_id}))
                for i in query:
                    db_con.NewPurchaseOrder.update_one(i, {'$set': {'lsi_key': status}})
                return {"statusCode": 200, "body": "{action} successfully".format(action=status)}
            elif id.startswith('INV'):
                query = list(db_con.NewPurchaseOrder.find({'all_attributes.inv_id': pk_id}))
                for i in query:
                    db_con.NewPurchaseOrder.update_one(i, {'$set': {'lsi_key': status}})
                return {"statusCode": 200, "body": "{action} successfully".format(action=status)}
            elif id.startswith('PI'):
                query = list(db_con.ProformaInvoice.find({'all_attributes.pi_id': pk_id}))
                for i in query:
                    db_con.ProformaInvoice.update_one(i, {'$set': {'lsi_key': status}})
                return {"statusCode": 200, "body": "{action} successfully".format(action=status)}
            elif id.startswith('CFPO'):
                query = list(db_con.ForcastPurchaseOrder.find({'all_attributes.Client_Purchaseorder_num': pk_id}))
                for i in query:
                    db_con.ForcastPurchaseOrder.update_one(i, {'$set': {'lsi_key': status}})
                return {"statusCode": 200, "body": "{action} successfully".format(action=status)}
            elif id.startswith('FCPO'):
                query = list(db_con.ForcastPurchaseOrder.find({'all_attributes.fcpo_id': pk_id}))
                for i in query:
                    db_con.ForcastPurchaseOrder.update_one(i, {'$set': {'lsi_key': status}})
                return {"statusCode": 200, "body": "{action} successfully".format(action=status)}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check event)'}

    # def cmsGetPurchaseOrderApprovals(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         status=data['status']
    #         pk_id=data['po_id']
    #         query=list(db_con.NewPurchaseOrder.find({'all_attributes.po_id':pk_id}))
    #         for i in query:
    #             po_list=db_con.NewPurchaseOrder.update_one(i,{'$set':{'lsi_key':status}})
    #         return {"statusCode": 200, "body": "{action} successfully".format(action=status)}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check event)'}
    
    # def cmsGetPurchaseOrderApprovals(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         status = data['status']
    #         # pk_id = data['po_id']
    #         # Fetching documents from MongoDB where lsi_key is 'Pending' and pk_id matches
    #         result = list(db_con.ForcastPurchaseOrder.update_one({'lsi_key': status}, {'_id': 0}))
    #         # return {'statusCode': 200, 'body': result}
    #         # Processing the results to change the keys as requested and updating the status
    #         processed_result = []
    #         for item in result:
    #             # Update the status from 'Pending' to 'Approved'
    #             db_con.ForcastPurchaseOrder.update_one({'pk_id': item['pk_id']}, {'$set': {'lsi_key': 'Approved'}})
    #             # Update the local item status as well
    #             item['lsi_key'] = 'Approved'
    #             # Process the item to change the keys as requested
    #             processed_item = {
    #                 "po_id": item["pk_id"],
    #                 "sk_timeStamp": item["sk_timeStamp"],
    #                 "all_details": item["all_attributes"],  # Changing 'all_attributes' to 'all_details'
    #                 "tablename": item["gsipk_table"],  # Changing 'gsipk_table' to 'tablename'
    #                 "status": item["lsi_key"],  # Changing 'lsi_key' to 'status'
    #                 "status1": item["gsisk_id"]  # Changing 'gsisk_id' to 'status1'
    #             }
    #             processed_result.append(processed_item)
    #         return {'statusCode': 200, 'body': processed_result}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         return {'statusCode': 400, 'body': 'Unable to Fetch data'}
        
    # def cmsGetPurchaseOrderApprovalsDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         status = data['status']
    #         results = []

    #         documents = list(db_con.NewPurchaseOrder.find({"gsipk_table": "PurchaseOrder", "lsi_key": status}, {"_id": 0}))
    #         # print(documents)
            
    #         for document in documents:
    #             # Extracting necessary fields from 'all_attributes'
    #             all_attributes = document["all_attributes"]
    #             primary_document_details = all_attributes["primary_document_details"]
    #             po_date = datetime.strptime(primary_document_details["po_date"], "%Y-%m-%d")
    #             print(po_date)
    #             # Find the longest delivery date
    #             purchase_list = all_attributes["purchase_list"]
    #             max_delivery_date = max(datetime.strptime(item["delivery_date"], "%Y-%m-%d") for item in purchase_list.values())
                
    #             # Calculate the difference in days
    #             days_difference = (max_delivery_date - po_date).days
                
    #             extracted_data = {
    #                 "primary_document_details": primary_document_details,
    #                 "ship_to": all_attributes["ship_to"],
    #                 "req_line": all_attributes["req_line"],
    #                 "kind_attn": all_attributes["kind_attn"],
    #                 "po_terms_conditions": all_attributes["po_terms_conditions"],
    #                 "status": document["lsi_key"],
    #                 "purchase_list": purchase_list,
    #                 "total_amount": all_attributes["total_amount"],
    #                 "secondary_doc_details": all_attributes["secondary_doc_details"],
    #                 "po_id": all_attributes["po_id"],
    #                 "vendor_id": all_attributes["vendor_id"],
    #                 "days_difference": f"{days_difference} days left",
    #             }
    #             results.append(extracted_data)

    #         return {'statusCode': 200, 'body': results}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         return {'statusCode': 400, 'body': 'Unable to Get Purchase Order Approval Details'}

    def cmsGetPurchaseOrderApprovalsDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            status = data['status']
            results = []
            if status in ['Approved', 'Rejected']:
                documents = list(db_con.NewPurchaseOrder.find(
                    {"gsipk_table": {"$in": ["PurchaseOrder", "ServiceOrder", "Invoice"]}, "lsi_key": status},
                    {"_id": 0}))
                pi = list(db_con.ProformaInvoice.find({"gsipk_table": {"$in": ["ProformaInvoice"]}, "lsi_key": status},
                                                                                                        {"_id": 0}))
                cfpo = list(db_con.ForcastPurchaseOrder.find(
                    {"gsipk_table": {"$in": ["ClientForcastPurchaseOrder", "ForcastPurchaseOrder"]}, "lsi_key": status},
                    {"_id": 0}))
                documents += pi + cfpo
            else:
                documents = list(db_con.NewPurchaseOrder.find(
                    {"gsipk_table": {"$in": ["PurchaseOrder", "ServiceOrder", "Invoice"]},
                     "lsi_key": {"$nin": ['Approved', 'Rejected', 'Cancel']}}, {"_id": 0}
                ))
                pi = list(db_con.ProformaInvoice.find({"gsipk_table": {"$in": ["ProformaInvoice"]},
                           "lsi_key": {"$nin": ['Approved', 'Rejected', 'Cancel']}}, {"_id": 0}
                   ))
                cfpo = list(db_con.ForcastPurchaseOrder.find(
                    {"gsipk_table": {"$in": ["ClientForcastPurchaseOrder", "ForcastPurchaseOrder"]},
                     "lsi_key": {"$nin": ['Approved', 'Rejected', 'Cancel']}}, {"_id": 0}
                ))
                documents += pi + cfpo
            for document in documents:
                all_attributes = document.get("all_attributes", {})
                primary_document_details = all_attributes.get("primary_document_details", {})
                po_date_str = (primary_document_details.get("po_date") or
                               primary_document_details.get("so_date") or
                               primary_document_details.get("invoice_date") or
                               primary_document_details.get("Pi_date") or
                               primary_document_details.get("document_date"))
                po_date = datetime.strptime(po_date_str, "%Y-%m-%d") if po_date_str else None
                purchase_list = (all_attributes.get("purchase_list", {}) or
                                 all_attributes.get("job_work_table", {}) or
                                 all_attributes.get("products_list", {}) or
                                 all_attributes.get("forecast_details", {}))

                # Calculate max_delivery_date only if purchase_list is not empty
                if purchase_list:
                    max_delivery_date_str = max(
                        item.get("delivery_date", primary_document_details.get("delivery_date", ""))
                        for item in purchase_list.values())
                    max_delivery_date = datetime.strptime(max_delivery_date_str,
                                                          "%Y-%m-%d") if max_delivery_date_str else None
                else:
                    max_delivery_date = None
                days_difference = (max_delivery_date - po_date).days if max_delivery_date and po_date else None
                extracted_data = {
                    "primary_document_details": primary_document_details,
                    "ship_to": all_attributes.get("ship_to", {}) or primary_document_details,
                    "req_line": all_attributes.get("req_line", ""),
                    "kind_attn": all_attributes.get("kind_attn", {}),
                    "po_terms_conditions": (all_attributes.get("po_terms_conditions", "") or
                                            all_attributes.get("so_terms_conditions", "") or
                                            all_attributes.get("pi_terms_conditions", "")),
                    "status": document["lsi_key"],
                    "purchase_list": purchase_list,
                    "total_amount": all_attributes.get("total_amount", {}),
                    "grand_total": all_attributes.get("grand_total", {}).get("balance_to_pay"),
                    "secondary_doc_details": all_attributes.get("secondary_doc_details", {}),
                    "po_id": (all_attributes.get("po_id", "") or
                              all_attributes.get("so_id", "") or
                              all_attributes.get("inv_id", "") or
                              all_attributes.get("pi_id", "") or
                              all_attributes.get("fcpo_id", "") or
                              all_attributes.get("Client_Purchaseorder_num", "")),
                    "vendor_id": (all_attributes.get("vendor_id", "") or
                                  all_attributes.get("partner_id", "") or
                                  all_attributes.get("client_id", "")),
                    "days_difference": f"{days_difference} days left" if days_difference is not None else ""
                }
                results.append(extracted_data)
            return {'statusCode': 200, 'body': results}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': 'Unable to Get Purchase Order Approval Details'}



    # def getPurchaseOrderPdfDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         status = data['status']

    #         po_id = data['po_id']
 
    #         document = db_con.NewPurchaseOrder.find_one({'lsi_key':status,'all_attributes.po_id':po_id}, {'_id': 0})
    #         print(document)
    #         if not document:
    #             return {'statusCode': 404, 'body': 'No purchase order found for the given status'}
 
    #         # Extracting necessary fields from 'all_attributes'
    #         all_attributes = document["all_attributes"]
    #         primary_document_details = all_attributes["primary_document_details"]
    #         po_date = datetime.strptime(primary_document_details["po_date"], "%Y-%m-%d")
           
    #         # Find the longest delivery date
    #         purchase_list = all_attributes["purchase_list"]
    #         max_delivery_date = max(datetime.strptime(item["delivery_date"], "%Y-%m-%d") for item in purchase_list.values())
           
    #         # Convert purchase_list dictionary to a list of part details
    #         purchase_list_details = list(purchase_list.values())
 
    #         # Calculate the difference in days
    #         days_difference = (max_delivery_date - po_date).days
           
    #         extracted_data = {
    #             "primary_document_details": primary_document_details,
    #             "ship_to": all_attributes["ship_to"],
    #             "req_line": all_attributes["req_line"],
    #             "kind_attn": all_attributes["kind_attn"],
    #             "po_terms_conditions": all_attributes["po_terms_conditions"],
    #             "status": document["lsi_key"],
    #             "purchase_list": purchase_list_details,
    #             "total_amount": all_attributes["total_amount"],
    #             "secondary_doc_details": all_attributes["secondary_doc_details"],
    #             "po_id": all_attributes["po_id"],
    #             "vendor_id": all_attributes["vendor_id"],
    #             "days_difference": f"{days_difference} days left",
    #         }
 
    #         return {'statusCode': 200, 'body': extracted_data}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         return {'statusCode': 400, 'body': f'Unable to Get Purchase Order Approval Details: {err} (file: {f_name}, line: {line_no})'}




    def getPurchaseOrderPdfDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            status = data['status']
            po_id = data['po_id']


            document = db_con.NewPurchaseOrder.find_one({'all_attributes.po_id': po_id,'lsi_key': status}, {'_id': 0})
            

            if not document:
                return {'statusCode': 404, 'body': 'No purchase order found for the given status and po_id'}
            all_attributes = document["all_attributes"]
            primary_document_details = all_attributes.get("primary_document_details", {})
            po_date_str = primary_document_details.get("po_date", "")
            if not po_date_str:
                return {'statusCode': 400, 'body': 'PO date is missing or invalid'}

            po_date = datetime.strptime(po_date_str, "%Y-%m-%d")

            
            purchase_list = all_attributes.get("purchase_list", {})
            if not purchase_list:
                return {'statusCode': 400, 'body': 'Purchase list is missing or invalid'}

            max_delivery_date = max(datetime.strptime(item["delivery_date"], "%Y-%m-%d") for item in purchase_list.values())

           
            purchase_list_details = list(purchase_list.values())

           
            days_difference = (max_delivery_date - po_date).days

            extracted_data = {
                "primary_document_details": primary_document_details,
                "ship_to": all_attributes.get("ship_to", {}),
                "req_line": all_attributes.get("req_line", ""),
                "kind_attn": all_attributes.get("kind_attn", {}),
                "po_terms_conditions": all_attributes.get("po_terms_conditions", ""),
                "status": document.get("lsi_key", ""),
                "purchase_list": purchase_list_details,
                "total_amount": all_attributes.get("total_amount", {}),
                "secondary_doc_details": all_attributes.get("secondary_doc_details", {}),
                "po_id": all_attributes.get("po_id", ""),
                "vendor_id": all_attributes.get("vendor_id", ""),
                "days_difference": f"{days_difference} days left",
            }

            return {'statusCode': 200, 'body': extracted_data}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Unable to Get Purchase Order Approval Details: {err} (file: {f_name}, line: {line_no})'}



    # def cmsGetPurchaseOrderApprovalsDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         status = data['status']
    #         # pk_id= data['po_id']
    #         # Fetching documents from MongoDB where lsi_key is 'Pending'
    #         results = []
    #         documents = list(db_con.PurchaseOrder.find({"gsipk_table": "PurchaseOrder", "lsi_key": status},
    #                                             {"_id": 0}))
    #         # return {'statusCode': 200, 'body': documents}
    #         for document in documents:
    #             # Extracting necessary fields from 'all_attributes'
    #             extracted_data = {
    #                 "primary_document_details": document["all_attributes"]["primary_document_details"],
    #                 "ship_to":document["all_attributes"]["ship_to"],
    #                 "req_line":document["all_attributes"]["req_line"],
    #                 "kind_attn":document["all_attributes"]["kind_attn"],
    #                 "po_terms_conditions":document["all_attributes"]["po_terms_conditions"],
    #                 "status":document["lsi_key"],
                    
    #                 "purchase_list": document["all_attributes"]["purchase_list"],
    #                 "total_amount": document["all_attributes"]["total_amount"],
    #                 "secondary_doc_details": document["all_attributes"]["secondary_doc_details"],
    #                 "po_id": document["all_attributes"]["po_id"],
    #                 "vendor_id": document["all_attributes"]["vendor_id"]
    #             }
    #             results.append(extracted_data)

    #         return {'statusCode': 200, 'body': results}
    # def cmsGetPurchaseOrderApprovalsDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         status = data['status']
    #         # pk_id= data['po_id']
    #         # Fetching documents from MongoDB where lsi_key is 'Pending'
    #         result = list(db_con.PurchaseOrder.find({"gsipk_table":"PurchaseOrder","lsi_key": status},{"all_attributes":1,"_id":0}))

    #         return {'statusCode': 200, 'body': result}
        # #     # Processing the results to change the keys as requested
        #     if result:
        #         processed_result = []
        #         for item in result:
        #             processed_item = {
        #                 "po_id": item["pk_id"],
        #                 "sk_timeStamp": item["sk_timeStamp"],
        #                 "all_details": item["all_attributes"],  # Changing 'all_attributes' to 'all_details'
        #                 "tablename": item["gsipk_table"],  # Changing 'gsipk_table' to 'tablename'
        #                 "status": item["lsi_key"],  # Changing 'lsi_key' to 'status'
        #                 "status1": item["gsisk_id"]  # Changing 'gsisk_id' to 'status1'
        #             }
        #             processed_result.append(processed_item)
        #         return {'statusCode': 200, 'body': processed_result}
        #     else:
        #         result = list(db_con.ForcastPurchaseOrder.find({"lsi_key": status}, {"_id": 0}))
        #         processed_result = []
        #         for item in result:
        #             processed_item = {
        #                 "po_id": item["pk_id"],
        #                 "sk_timeStamp": item["sk_timeStamp"],
        #                 "all_details": item["all_attributes"],  # Changing 'all_attributes' to 'all_details'
        #                 "tablename": item["gsipk_table"],  # Changing 'gsipk_table' to 'tablename'
        #                 "status": item["lsi_key"],  # Changing 'lsi_key' to 'status'
        #                 "status1": item["gsisk_id"]  # Changing 'gsisk_id' to 'status1'
        #             }
        #             processed_result.append(processed_item)
        #         return {'statusCode': 200, 'body': processed_result}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': 'Unable to Fetch data'}


    def cmsGetDraftList(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            
            # Assuming conct.get_conn is a function that returns the database connection
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            
            # Fetch documents from the database
            draftpo = list(db_con.PurchaseOrder.find({"gsipk_table": "DraftPurchaseOrder", "all_attributes": {"$exists": True}}))
            
            # Initialize the response list
            response = []
            
            # Iterate over each document and construct the response
            for index, doc in enumerate(draftpo):
                if 'all_attributes' in doc:
                    all_attrs = doc['all_attributes']
                    sk_timeStamp = doc.get('sk_timeStamp', '')
                    sk_date = sk_timeStamp.split('T')[0] if sk_timeStamp else 'N/A'
                    response_item = {
                        "s.no": str(index + 1),  # Serial number
                        "company_name": all_attrs.get('ship_to', {}).get('company_name', 'N/A'),
                        "transaction_name": all_attrs.get('primary_document_details', {}).get('transaction_name', 'N/A'),
                        "document_number": all_attrs.get('primary_document_details', {}).get('po_id', 'N/A'),
                        "request_status": all_attrs.get('primary_document_details', {}).get('status', 'N/A'),
                        "tracking": "Received",
                        "sk_timeStamp": sk_date,
                        "gsisk_id": doc.get('gsisk_id', 'N/A'),
                        "ship_to": all_attrs.get('ship_to', {}),
                        "req_line": all_attrs.get('req_line', 'N/A'),
                        "po_terms_conditions": all_attrs.get('po_terms_conditions', 'N/A'),
                        "kind_attn": all_attrs.get('kind_attn', {}),
                        "primary_document_details": all_attrs.get('primary_document_details', {}),
                        "purchase_list": all_attrs.get('purchase_list', {}),
                        "total_amount": all_attrs.get('total_amount', {}),
                        "secondary_doc_details": all_attrs.get('secondary_doc_details', {}),
                        "po_id": all_attrs.get('primary_document_details', {}).get('po_id', 'N/A'),
                        "vendor_id": all_attrs.get('vendor_id', 'N/A')
                    }
                    response.append(response_item)
            
            return {'statusCode': 200, 'body': response}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            error_message = f"Unable to Get Drafts: {str(err)} at {f_name} line {line_no}"
            return {'statusCode': 400, 'body': error_message}
    # def cmsGetDraftList(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         response = {}
    #         draftpo = list(db_con.PurchaseOrder.find({"gsipk_table": "DraftPurchaseOrder", "all_attributes": {"$exists": True}}))
    #         boxbuilding = list(db_con.BoxBuilding.find({"all_attributes": {"$exists": True}}))
    #         # for i in draftpo:
    #         #     response = {
    #         #     "s.no": "1",
    #         #     "company_name": "ABC",
    #         #     "transaction_name": "Transaction",
    #         #     "document_number": "Doc",
    #         #     "request_status": "Requested",
    #         #     "tracking": "Recieved",
                    
    #         # }
    #         # result = draftpo + boxbuilding
    #         response = [i['all_attributes'] for i in draftpo]
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
            pk_id = data['pk_id']
            update_query = {}
            update_query = data['update']
            # resp = db_con.DraftForcastPurchaseOrder.update_one({"pk_id": pk_id}, {"$set": update_query})
            sk_timeStamp = (datetime.now()).isoformat()

            primary_doc_details = update_query.get("primary_document_details", {})
            po_date = primary_doc_details.get("PO_Date", "")

            if po_date:
                try:
                    po_date_obj = datetime.strptime(po_date, "%Y-%m-%d")
                    po_month_year = po_date_obj.strftime("%m-%y")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid PO_Date format'}
            else:
                return {'statusCode': 400, 'body': 'PO_Date is required'}

            purchase_order = list(db_con.PurchaseOrder.find({}))
            bom_id = data.get('bom_id', '')
            purchase_order_id = "1"

            client_po_num = ""
            ext = 1
            purchase_order_id = '1'
            if purchase_order:
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                if "PurchaseOrder" in update_id[0]['all_attributes']:
                    update_id = (update_id[0]['all_attributes']['PurchaseOrder'][4:])
                    ext = ext + int(update_id)
                else:
                    update_id = "1"
                purchase_order_id = str(int(update_id) + 1)

                last_client_po_nums = [i["all_attributes"]["po_id"] for i in purchase_order if
                                    "po_id" in i["all_attributes"]]
                if last_client_po_nums:
                    client_po_num = f"EPL/PO/{purchase_order_id}/{po_month_year}"
            update_query["po_id"] = f"EPL/PO/{ext}/{po_month_year}"
            update_query["vendor_id"] = data["vendor_id"]
            purchase_data = {
                "pk_id": "OPTG" + purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": update_query,
                "gsisk_id": "open",
                "gsipk_table": "PurchaseOrder",
                "lsi_key": "Pending"
            }
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}
            db_con.PurchaseOrder.insert_one(purchase_data)
            update_data = {
                '$set': {
                    'all_attributes.PurchaseOrder': "FCPO" + purchase_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            return {'statusCode': 200, 'body': 'Updated and saved record successfully'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': 'Unable to Edit Draft'}
    # def CmsClientForcastPurchaseOrderEdit(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         PI_no=data["Client_Purchaseorder_num"]
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         pi_data = db_con.DraftClientForcastPurchaseOrder.find_one({"all_attributes.Client_Purchaseorder_num": PI_no})
    #         if not pi_data:
    #             return {'statusCode': 404, 'body': 'client forecast not found'}
    #         filesLst = {}
    #         if "productlistdoc" in data and data["productlistdoc"].get('doc_body') and data["productlistdoc"].get(
    #                 'doc_name'):
    #             doc_name = data["productlistdoc"]["doc_name"][:-4]
    #             doc_body = data["productlistdoc"]["doc_body"]
    #             file_key = file_uploads.upload_file("ClientForecast", "PtgCms" + env_type, "",
    #                                                 "ClientforecastpurchaseOrder_" + PI_no,
    #                                                 data["productlistdoc"]["doc_name"], doc_body)
    #             filesLst['doc_body'] = file_key
    #             filesLst['doc_name']=doc_name
    #         update_fields = {
    #             "buyerDetails": data.get("buyerDetails", pi_data["all_attributes"].get("buyerDetails", {})),
    #             "deliveryLocation": data.get("deliveryLocation", pi_data["all_attributes"].get("deliveryLocation", "")),
    #             "supplierDetails": data.get("supplierDetails", pi_data["all_attributes"].get("supplierDetails", "")),
    #             "supplierLocation": data.get("supplierLocation", pi_data["all_attributes"].get("supplierLocation", {})),
    #             "primary_document_details": data.get("primary_document_details", pi_data["all_attributes"].get("primary_document_details", {})),
    #             "productlistDetails": data.get("productlistDetails", pi_data["all_attributes"].get("productlistDetails", {})),
    #             "total_amount": data.get("total_amount", pi_data["all_attributes"].get("total_amount", {})),
    #             "productlistdoc": filesLst,
    #             "grand_total": data.get("grand_total", pi_data["all_attributes"].get("grand_total", "")),
    #             "Client_Purchaseorder_num": PI_no 
    #         }
    #         # Update the service order in the database
    #         db_con.DraftClientForcastPurchaseOrder.update_one(
    #             {"all_attributes.Client_Purchaseorder_num": PI_no},
    #             {"$set": {
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": update_fields
    #             }}
    #         )

    #         conct.close_connection(client)
    #         return {'statusCode': 200, 'body': 'client forecast updated successfully'}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'internal server error'} 

    # def CmsClientForcastPurchaseOrderEditGet(request_body):
    #     try:
    #         data = request_body
    #         # print(request_body)
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         pi_id = data['Client_Purchaseorder_num']
    #         proforma_record = db_con.DraftClientForcastPurchaseOrder.find_one({"all_attributes.Client_Purchaseorder_num":pi_id},{"_id":0,"all_attributes":1})
    #         print(proforma_record)
    #         return proforma_record
    #         # proforma_record['']
    #         if proforma_record:
    #             return {'statusCode': 400,'body': proforma_record['all_attributes']}
    #         else:
    #             return {'statusCode': 400,'body': 'No record found for this pi id'}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400,'body': 'Internal server error'}

    
    def CmsGetForcastPurchaseOrderDetailsList1(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            poall_id = data.get('poall_id', None)

            response_body = []

            # Query MongoDB for the forecast purchase orders
            forecast_query = {} if not poall_id else {'all_attributes.Client_Purchaseorder_num': poall_id}
            forecast_list = list(db_con.ForcastPurchaseOrder.find(forecast_query, {'_id': 0}))

            for forecast in forecast_list:
                document_date_str = forecast["all_attributes"]["primary_document_details"].get("po_date")
                delivery_date_str = forecast["all_attributes"]["primary_document_details"].get("delivery_date")
                sk_timeStamp_str = forecast.get("sk_timeStamp", "")[:10]

                if document_date_str and delivery_date_str and sk_timeStamp_str:
                    delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
                    sk_timeStamp = datetime.strptime(sk_timeStamp_str, "%Y-%m-%d")
                    document_date = datetime.strptime(document_date_str, "%Y-%m-%d")
                    days_left = max(0, (delivery_date - document_date).days)
                else:
                    delivery_date = sk_timeStamp = document_date = None
                    days_left = 0

                docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
                        forecast["all_attributes"].get("documents", {}).items()]
                document_url = docs[0]["content"] if docs else ""

                # purchase_list_dict = forecast.get("purchase_list", {})
                # purchase_list = [
                #     {
                #         "item_no": part.get("item_no", ""),
                #         "rev": part.get("rev", ""),
                #         "description": part.get("description", ""),
                #         "delivery_date": part.get("delivery_date", ""),
                #         "qty": part.get("qty", ""),
                #         "unit": part.get("unit", ""),
                #         "rate": part.get("rate", ""),
                #         "gst": part.get("gst", ""),
                #         "basic_amount": part.get("basic_amount", ""),
                #         "gst_amount": part.get("gst_amount", "")
                #     }
                #     for part in purchase_list_dict.values()
                # ]

                formatted_order = {
                    "Client_Purchaseorder_num": forecast['all_attributes'].get("Client_Purchaseorder_num", ""),
                    "buyer_details": forecast['all_attributes'].get("buyer_details", ""),
                    "delivery_location": forecast['all_attributes'].get("delivery_location", ""),
                    "delivery_date": f"{days_left} days left",
                    "supplier_details": forecast['all_attributes'].get("supplier_details", ""),
                    "supplierLocation": forecast['all_attributes'].get("supplierLocation", ""),
                    "payment_status": forecast.get('gsisk_id', ''),
                    "modified_date": sk_timeStamp_str,
                    "fc_po_ids": forecast.get('pk_id', ""),
                    "primary_document_details": forecast['all_attributes'].get("primary_document_details", {}),
                    "forecast_details": [],
                    "last_modified_date": forecast['all_attributes'].get("last_modified_date", ""),
                    "documents_url": document_url,
                    # "purchase_list": purchase_list
                }

                forecast_details = forecast['all_attributes'].get("forecast_details", {})
                if formatted_order["Client_Purchaseorder_num"].startswith("EPL/FCPO"):
                    for forecast_key, forecast_value in forecast_details.items():
                        monthly_status = False if forecast_value.get("po_name", "__") == "__" else True
                        forecast_value["monthly_status"] = monthly_status
                        if forecast_value.get("po_name", "")[-4:] == '.pdf':
                            forecast_value["forecast_document"] = forecast_value.get("po_name", "")
                        formatted_order["forecast_details"].append(forecast_value)
                    if total_amount := forecast['all_attributes'].get("total_amount", {}):
                        formatted_order["total_amount"] = total_amount
                    if grand_total := forecast['all_attributes'].get("grand_total", {}):
                        formatted_order["grand_total"] = grand_total
                else:
                    formatted_order["forecast_details"] = [forecast_value for forecast_key, forecast_value in forecast_details.items()]
                    formatted_order["total_amount"] = forecast['all_attributes'].get("total_amount", {})
                    formatted_order["grand_total"] = forecast['all_attributes'].get("grand_total", {})

                response_body.append(formatted_order)

            # Query MongoDB for approved purchase orders
            po_query = {'lsi_key': 'Approved'}
            if poall_id:
                po_query['all_attributes.po_id'] = poall_id
            po_list = list(db_con.NewPurchaseOrder.find(po_query, {"_id": 0}))
            po_list1 = [i['all_attributes'] for i in po_list]

            l2 = []
            for po in po_list1:
                purchase_list_dict = po.get("purchase_list", {})
                purchase_list = [
                    {
                        "item_no": part.get("item_no", ""),
                        "rev": part.get("rev", ""),
                        "description": part.get("description", ""),
                        "delivery_date": part.get("delivery_date", ""),
                        "qty": part.get("qty", ""),
                        "unit": part.get("unit", ""),
                        "rate": part.get("rate", ""),
                        "gst": part.get("gst", ""),
                        "basic_amount": part.get("basic_amount", ""),
                        "gst_amount": part.get("gst_amount", "")
                    }
                    for part in purchase_list_dict.values()
                ]
                po['purchase_list'] = purchase_list
                l1 = []
                for part in po['purchase_list']:
                    delivery_date = part.get('delivery_date')
                    if delivery_date:
                        l1.append(delivery_date)
                l2.append(max(l1) if l1 else None)

            po_date_list = [i['primary_document_details'].get('po_date') for i in po_list1]
            l2 = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in l2]
            po_date_list = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in po_date_list]
            days_difference = [max(0, (delivery_date - po_date).days) if delivery_date and po_date else 0 for
                            delivery_date, po_date in zip(l2, po_date_list)]

            for i in range(len(po_list1)):
                po_list1[i]['due_date'] = f"{days_difference[i]} days left"
                po_list1[i]['modified_date'] = po_list[i].get('sk_timeStamp', '')[:10]
                po_list1[i]['payment_status'] = po_list[i].get('gsisk_id', '')
                terms_conditions_str = po_list1[i].get('secondary_doc_details', {}).get('terms_conditions', "")
                terms_conditions_list = terms_conditions_str.split('\n')
                po_list1[i]['secondary_doc_details']['terms_conditions'] = terms_conditions_list
                response_body.extend(po_list1)

            # Query MongoDB for service orders
            so_query = {'gsipk_table': 'ServiceOrder'}
            if poall_id:
                so_query['all_attributes.so_id'] = poall_id
            so_list = list(db_con.NewPurchaseOrder.find(so_query, {"_id": 0}))
            so_list1 = [i['all_attributes'] for i in so_list]

            l3 = []
            for so in so_list1:
                l1 = []
                for part in so['job_work_table'].values():
                    delivery_date = part.get('delivery_date')
                    if delivery_date:
                        l1.append(delivery_date)
                l3.append(max(l1) if l1 else None)

            so_date_list = [i['primary_document_details'].get('so_date') for i in so_list1]
            l3 = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in l3]
            so_date_list = [datetime.strptime(date_str, "%Y-%m-%d") if date_str else None for date_str in so_date_list]
            so_days_difference = [max(0, (delivery_date - so_date).days) if delivery_date and so_date else 0 for
                                delivery_date, so_date in zip(l3, so_date_list)]

            for i in range(len(so_list1)):
                so_list1[i]['due_date'] = f"{so_days_difference[i]} days left"
                so_list1[i]['modified_date'] = so_list[i].get('sk_timeStamp', '')[:10]
                so_list1[i]['payment_status'] = so_list[i].get('gsisk_id', '')

                # Reformat job_work_table from dictionary to list
                job_work_table_dict = so_list1[i].get("job_work_table", {})
                job_work_table = [
                    {
                        "sn_no": part.get("sn_no", ""),
                        "scope_of_job_work": part.get("scope_of_job_work", ""),
                        "qty": part.get("qty", ""),
                        "rate": part.get("rate", ""),
                        "gst%": part.get("gst%", ""),
                        "gst": part.get("gst", ""),
                        "basic_amount": part.get("basic_amount", ""),
                        "delivery_date": part.get("delivery_date", "")
                    }
                    for part in job_work_table_dict.values()
                ]
                so_list1[i]['job_work_table'] = job_work_table

            response_body.extend(so_list1)

            # Query MongoDB for invoices
            invoice_query = {} if not poall_id else {'all_attributes.inv_id': poall_id}
            print(invoice_query)
            invoice_list = list(db_con.NewPurchaseOrder.find(invoice_query, {'_id': 0}))
            print(invoice_list)
            # if not invoice_list:
            #     return {"message": "No matching invoices found."}
            for invoice in invoice_list:
                invoice_data = invoice.get('all_attributes', {})
                purchase_list_dict = invoice_data.get("purchase_list", {})
                purchase_list = [
                    {
                        "item_no": part.get("item_no", ""),
                        "rev": part.get("rev", ""),
                        "description": part.get("description", ""),
                        "delivery_date": part.get("delivery_date", ""),
                        "qty": part.get("qty", ""),
                        "unit": part.get("unit", ""),
                        "rate": part.get("rate", ""),
                        "gst": part.get("gst", ""),
                        "basic_amount": part.get("basic_amount", ""),
                        "gst_amount": part.get("gst_amount", "")
                    }
                    for part in purchase_list_dict.values()
                ]
                invoice_data['purchase_list'] = purchase_list
                response_body.append(invoice_data)

            # Query MongoDB for proforma invoices
            proforma_invoice_query = {} if not poall_id else {'all_attributes.pi_id': poall_id}
            print(proforma_invoice_query)
            proforma_invoice_list = list(db_con.ProformaInvoice.find(proforma_invoice_query, {'_id': 0}))
            print(proforma_invoice_list)
            for proforma_invoice in proforma_invoice_list:
                proforma_invoice_data = proforma_invoice.get('all_attributes', {})
                products_list_dict = proforma_invoice_data.get("products_list", {})
                products_list = [
                    {
                        "s_no": part.get("s_no", ""),
                        "item_no": part.get("item_no", ""),
                        "description": part.get("description", ""),
                        "qty": part.get("qty", ""),
                        "unit": part.get("unit", ""),
                        "rate": part.get("rate", ""),
                        "gst": part.get("gst", ""),
                        "basic_amount": part.get("basic_amount", ""),
                        "gst_amount": part.get("gst_amount", "")
                    }
                    for part in products_list_dict.values()
                ]
                proforma_invoice_data['products_list'] = products_list
                response_body.append(proforma_invoice_data)

            client.close()
            # return response_body
            # response_body.extend(proinv_list1)
            # return response_body

            return {"statusCode": 200, "body": response_body}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check event)'}


        
    
    
    
    def CmsDraftCreateClientForcastPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
            document_name = data['productlistdoc']["doc_name"]
            document_body = data['productlistdoc']['doc_body']
            # Fetch existing forecast purchase orders
            ClientForcastPurchaseOrder_data = list(db_con.DraftClientForcastPurchaseOrder.find({}, {
                "pk_id": 1,
                "all_attributes.productlistdoc": 1,
                "all_attributes.primary_document_details.document_title": 1
            }))
            document_title = [i['all_attributes']['primary_document_details']['document_title'] for i in
                            ClientForcastPurchaseOrder_data]
            documents = [k for i in ClientForcastPurchaseOrder_data for k, j in
                        i['all_attributes']['productlistdoc'].items()]
            # Validate primary document details
            primary_document_details = data["primary_document_details"]
            if primary_document_details['document_date'] in ["N/A", "NA"]:
                primary_document_details['document_date'] = "0000-00-00"
            if primary_document_details['delivery_date'] in ["N/A", "NA"]:
                primary_document_details['delivery_date'] = "0000-00-00"
            # Add client_name and bom_name to primary_document_details
            primary_document_details['client_name'] = data['primary_document_details']['client_name']
            primary_document_details['bom_name'] = data['primary_document_details']['bom_name']
            # Validate product list details
            for product in data["productlistDetails"]:
                if int(product['qty']) <= 0:
                    return {"statusCode": 400, "body": "Quantity should not be less or equal to 0"}
                if float(product['total_price']) <= 0:
                    return {"statusCode": 400, "body": "Order value should not be less than or equal to 0"}
            # Check for duplicate document name
            if document_name[:-4] in documents:
                return {'statusCode': 400, "body": "Cannot upload duplicate file name"}
            # Fetch draft client forecast purchase orders
            draft_ClientForcastPurchaseOrder = list(db_con.DraftClientForcastPurchaseOrder.find({}, {
                "pk_id": 1,
                "all_attributes.productlistdoc": 1,
                "all_attributes.primary_document_details.document_title": 1
            }))
            document_title_draft = [i['all_attributes']['primary_document_details'] for i in
                                    draft_ClientForcastPurchaseOrder]
            documents_draft = [k for i in draft_ClientForcastPurchaseOrder for k, j in
                            i['all_attributes']['productlistdoc'].items()]
            # Generate forecast purchase order ID
            if ClientForcastPurchaseOrder_data:
                last_order = ClientForcastPurchaseOrder_data[-1]
                last_order_id = int(last_order['pk_id'][5:])
                forecast_purchase_order_id = str(last_order_id + 1)
            else:
                forecast_purchase_order_id = '0'
            print(forecast_purchase_order_id)
            # Handle file upload
            filesLst = {"productlistdoc": {}}
            if "productlistdoc" in data and data["productlistdoc"].get('doc_body') and data["productlistdoc"].get(
                    'doc_name'):
                doc_name = data["productlistdoc"]["doc_name"][:-4]
                doc_body = data["productlistdoc"]["doc_body"]
                file_key = file_uploads.upload_file("draftForecast", "PtgCms" + env_type, "",
                                                    "draftforecastpurchaseOrder_" + forecast_purchase_order_id,
                                                    data["productlistdoc"]["doc_name"], doc_body)
                filesLst["productlistdoc"]['doc_body'] = file_key
                filesLst["productlistdoc"]['doc_name'] = data["productlistdoc"]["doc_name"]
            # Validate duplicate document title and number
            if primary_document_details['document_title'] in document_title:
                return {'statusCode': 400, "body": "Cannot upload duplicate document title"}
            if primary_document_details['document_title'] in document_title_draft:
                return {'statusCode': 200,
                        "message": "Cannot upload duplicate document title already present in drafts"}
            if document_name[:-4] in documents_draft:
                return {'statusCode': 200,
                        "message": "Cannot upload duplicate document file name already present in drafts"}
            # Prepare all attributes
            primary_document_details['status'] = "Not dispatched"
            # document_month_year = datetime.strptime(primary_document_details['document_date'], '%Y-%m-%d').strftime(
            #     '%m-%y')
            document_date = primary_document_details['document_date']
            document_month = datetime.strptime(document_date, '%Y-%m-%d').strftime('%m')
            document_year = datetime.strptime(document_date, '%Y-%m-%d').strftime('%y')
            next_year = str(int(document_year) + 1).zfill(2)
            document_month_year = f"{document_month}/{document_year}-{next_year}"


            # productlistDetails = {f"productlist{inx + 1}": value.update({"cmts_atcmts": {}}) or value for inx, value in
            productlistDetails = {f"product{inx + 1}": value.update({"cmts_atcmts": {}}) or value for inx, value in
                                enumerate(data['productlistDetails'])}
            all_attributes = {
                "Client_Purchaseorder_num": f"EPL/DCFPO/{forecast_purchase_order_id}/{document_month_year}",
                'buyer_details': data['buyerDetails'],
                "delivery_location": data['deliveryLocation'],
                "supplier_details": data['supplierDetails'],
                "supplierLocation": data['supplierLocation'],
                # "time_line_status": "PO",
                "primary_document_details": primary_document_details,
                # "productlist_details": productlistDetails,
                "productlistDetails": productlistDetails,
                'last_modified_date': sk_timeStamp[:10],
                "total_amount": data["total_amount"],
                "grand_total": data["grand_total"],
            }
            all_attributes.update(filesLst)
            item = {
                "pk_id": "DCFPO" + forecast_purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": all_attributes,
                "gsipk_table": "DraftClientForcastPurchaseOrder",
                "gsisk_id": "open",
                "lsi_key": "Pending"
            }
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}
            db_con.DraftClientForcastPurchaseOrder.insert_one(item)
            update_data = {
                '$set': {
                    'all_attributes.DraftClientForcastPurchaseOrder': "DCFPO" + forecast_purchase_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            if item:
                return {'statusCode': 200, 'body': 'Draft Client Forecast Purchase Order created successfully'}
            else:
                return {"statusCode": 404, "body": "No ClientForcastPurchaseOrder found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
        

    
    def CmsDraftClientForcastPurchaseOrderEdit(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            PI_no = data["Client_Purchaseorder_num"]
            sk_timeStamp = (datetime.now()).isoformat()

            # Generate the pk_id similar to CmsDraftUpdateEditForecastPurchaseOrder function
            pk_ids = list(db_con.ForcastPurchaseOrder.find({'pk_id': {'$regex': '^CF'}}, {'pk_id': 1}))
            if len(pk_ids) == 0:
                pk_id = "CFPO1"
                max_pk = 1
            else:
                pk_filter = [int(x['pk_id'][4:]) for x in pk_ids]
                max_pk = max(pk_filter) + 1
                pk_id = "CFPO" + str(max_pk)

            # Fetch existing draft forecast purchase order data
            pi_data = db_con.DraftClientForcastPurchaseOrder.find_one({"all_attributes.Client_Purchaseorder_num": PI_no})
            if not pi_data:
                return {'statusCode': 404, 'body': 'client forecast not found'}

            # Prepare the file upload if productlistdoc is present
            documents = {}
            if "productlistdoc" in data and data["productlistdoc"].get('doc_body') and data["productlistdoc"].get('doc_name'):
                doc_name = data["productlistdoc"]["doc_name"]
                doc_body = data["productlistdoc"]["doc_body"]
                file_key = file_uploads.upload_file(
                    "ClientForecast", "PtgCms" + env_type, "",
                    "ClientforecastpurchaseOrder_" + PI_no,
                    doc_name, doc_body
                )
                documents[doc_name] = file_key  # Store in the desired format

            # Update fields with the incoming data or use existing data from the database
            update_fields = {
                "buyer_details": data.get("buyer_details", pi_data["all_attributes"].get("buyer_details", "")),
                "delivery_location": data.get("delivery_location", pi_data["all_attributes"].get("delivery_location", "")),
                "supplier_details": data.get("supplier_details", pi_data["all_attributes"].get("supplier_details", "")),
                "supplierLocation": data.get("supplierLocation", pi_data["all_attributes"].get("supplierLocation", "")),
                "primary_document_details": data.get("primary_document_details", pi_data["all_attributes"].get("primary_document_details", {})),
                "productlistDetails": data.get("productlistDetails", pi_data["all_attributes"].get("productlistDetails", {})),
                "total_amount": data.get("total_amount", pi_data["all_attributes"].get("total_amount", "")),
                "grand_total": data.get("grand_total", pi_data["all_attributes"].get("grand_total", "")),
                "Client_Purchaseorder_num": PI_no
            }

            # Validate and process so_date
            primary_document_details = update_fields.get("primary_document_details", {})
            so_date = primary_document_details.get("document_date", "")
            if so_date:
                try:
                    so_date = datetime.strptime(so_date, "%Y-%m-%d")
                except ValueError:
                    return {'statusCode': 400, 'body': 'Invalid document_date format'}
            else:
                return {'statusCode': 400, 'body': 'document_date is required'}

            so_month = so_date.month
            so_year = so_date.strftime("%y")
            so_next = (so_date.year + 1) % 100
            so_id = f"EPL/CFPO/{max_pk}/{so_month}/{so_year}-{so_next:02d}"

            # Update the new fields
            update_fields.update({
                "Client_Purchaseorder_num": so_id,
                "time_line_status": data.get("time_line_status", "PO"),
                "last_modified_date": sk_timeStamp[:10],
                "documents": documents  # Update documents field with the new format
            })

            # Delete the draft entry
            db_con.DraftClientForcastPurchaseOrder.delete_one({"all_attributes.Client_Purchaseorder_num": PI_no})

            # Insert the updated data into the ForcastPurchaseOrder table
            db_con.ForcastPurchaseOrder.insert_one({
                "pk_id": pk_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": update_fields,
                "gsipk_table": "ClientForcastPurchaseOrder",
                "gsisk_id": "open",
                "lsi_key": "Pending"
            })

            # Update the top_ids in all_tables
            db_con.all_tables.update_one({'pk_id': 'top_ids'}, {'$set': {'all_attributes.ClientForcastPurchaseOrder': pk_id}})

            conct.close_connection(client)
            return {'statusCode': 200, 'body': 'Client forecast updated successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'internal server error'}


        
    # def CmsClientForcastPurchaseOrderEdit(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         PI_no=data["Client_Purchaseorder_num"]
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         pi_data = db_con.DraftClientForcastPurchaseOrder.find_one({"all_attributes.Client_Purchaseorder_num": PI_no})
    #         if not pi_data:
    #             return {'statusCode': 404, 'body': 'client forecast not found'}
    #         filesLst = {}
    #         if "productlistdoc" in data and data["productlistdoc"].get('doc_body') and data["productlistdoc"].get(
    #                 'doc_name'):
    #             doc_name = data["productlistdoc"]["doc_name"][:-4]
    #             doc_body = data["productlistdoc"]["doc_body"]
    #             file_key = file_uploads.upload_file("ClientForecast", "PtgCms" + env_type, "",
    #                                                 "ClientforecastpurchaseOrder_" + PI_no,
    #                                                 data["productlistdoc"]["doc_name"], doc_body)
    #             filesLst['doc_body'] = file_key
    #             filesLst['doc_name']=doc_name
    #         update_fields = {
    #             "buyer_details": data.get("buyer_details", pi_data["all_attributes"].get("buyer_details", "")),
    #             "delivery_location": data.get("delivery_location", pi_data["all_attributes"].get("delivery_location", "")),
    #             "supplier_details": data.get("supplier_details", pi_data["all_attributes"].get("supplier_details", "")),
    #             "supplierLocation": data.get("supplierLocation", pi_data["all_attributes"].get("supplierLocation", "")),
    #             "primary_document_details": data.get("primary_document_details", pi_data["all_attributes"].get("primary_document_details", {})),
    #             "productlistDetails": data.get("productlistDetails", pi_data["all_attributes"].get("productlistDetails", {})),
    #             "total_amount": data.get("total_amount", pi_data["all_attributes"].get("total_amount", "")),
    #             "productlistdoc": filesLst,
    #             "grand_total": data.get("grand_total", pi_data["all_attributes"].get("grand_total", "")),
    #             "Client_Purchaseorder_num": PI_no 
    #         }
    #         # Update the service order in the database
    #         db_con.DraftClientForcastPurchaseOrder.update_one(
    #             {"all_attributes.Client_Purchaseorder_num": PI_no},
    #             {"$set": {
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": update_fields
    #             }}
    #         )

    #         conct.close_connection(client)
    #         return {'statusCode': 200, 'body': 'client forecast updated successfully'}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'internal server error'} 

    def CmsClientForcastPurchaseOrderEditGet(request_body):
        try:
            data = request_body
            # print(request_body)
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            pi_id = data['Client_Purchaseorder_num']
            proforma_record = db_con.DraftClientForcastPurchaseOrder.find_one({"all_attributes.Client_Purchaseorder_num":pi_id},{"_id":0,"all_attributes":1})
            if proforma_record:
                return {'statusCode': 400,'body': proforma_record['all_attributes']}
            else:
                return {'statusCode': 400,'body': 'No record found for this client forecast draft'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}



    
    def CmsEditGetForecastPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            fcpo_id = data.get('fcpo_id', '')

            if fcpo_id:
                forcast_record = db_con.ForcastPurchaseOrder.find_one({"all_attributes.fcpo_id": fcpo_id}, {"_id": 0, "all_attributes": 1})
                if forcast_record:
                    # Extract the document information
                    documents = forcast_record['all_attributes'].get('documents', {})

                    if documents:
                        doc_body = list(documents.values())[0]
                        doc_name = doc_body.split('/')[-1]
                        forcast_record['all_attributes']['documents'] = {
                            "doc_name": doc_name,
                            "doc_body": doc_body
                        }
                    
                    return {'statusCode': 200, 'body': forcast_record['all_attributes']}
                else:
                    forcast_record_record1 = db_con.DraftForcastPurchaseOrder.find_one({"all_attributes.dfcpo_id": fcpo_id}, {"_id": 0, "all_attributes": 1})
                    if forcast_record_record1:
                        documents = forcast_record_record1['all_attributes'].get('documents', {})
                        if documents:
                            doc_body = list(documents.values())[0]
                            doc_name = doc_body.split('/')[-1]
                            forcast_record_record1['all_attributes']['documents'] = {
                                "doc_name": doc_name,
                                "doc_body": doc_body
                            }
                        return {'statusCode': 200, 'body': forcast_record_record1['all_attributes']}
                    else:
                        return {'statusCode': 400, 'body': 'No record found for this fcpo_id'}
            else:
                return {'statusCode': 400, 'body': 'fcpo_id is required'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}


    
    def CmsEditUpdateForcastPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            PI_no = data["fcpo_id"]
            updatestatus = data["updatestatus"]
            sk_timeStamp = (datetime.now()).isoformat()

            # Fetch existing forecast purchase order data
            pi_data = db_con.ForcastPurchaseOrder.find_one({"all_attributes.fcpo_id": PI_no, "lsi_key": updatestatus})
            print(pi_data)
            if not pi_data:
                return {'statusCode': 404, 'body': 'client forecast not found'}

            # If the status is "Rejected", update it to "Pending"
            new_status = "Pending" if updatestatus == "Rejected" else updatestatus
            # new_status = "Approved" if updatestatus == "Approved" else updatestatus

            # Process forecast details to the new format
            forecast_details = {}
            for index, detail in enumerate(data.get("forecastDetails", []), start=1):
                forecast_key = f"forecast{index}"
                forecast_details[forecast_key] = detail

            # Process forecast invoice document to the new format
            documents = {}
            if "forecastInvoice" in data and data["forecastInvoice"].get('doc_body') and data["forecastInvoice"].get('doc_name'):
                doc_name = data["forecastInvoice"]["doc_name"]
                doc_body = data["forecastInvoice"]["doc_body"]
                file_key = file_uploads.upload_file("Forecast", "PtgCms" + env_type, "",
                                                    "forecastpurchaseOrder_" + PI_no,
                                                    doc_name, doc_body)
                documents[doc_name] = file_key

            # Prepare the fields to be updated
            update_fields = {
                "fcpo_id": PI_no,
                "buyer_details": data.get("buyerDetails", pi_data["all_attributes"].get("buyer_details", "")),
                "delivery_location": data.get("deliveryLocation", pi_data["all_attributes"].get("delivery_location", "")),
                "supplier_details": data.get("supplierDetails", pi_data["all_attributes"].get("supplier_details", "")),
                "supplierLocation": data.get("supplierLocation", pi_data["all_attributes"].get("supplierLocation", "")),
                "time_line_status": data.get("time_line_status", "PO"),
                "primary_document_details": data.get("primaryDocumentDetails", pi_data["all_attributes"].get("primary_document_details", {})),
                "forecast_details": forecast_details,
                "last_modified_date": sk_timeStamp[:10],
                "documents": documents
            }

            # Update the forecast purchase order in the database
            db_con.ForcastPurchaseOrder.update_one(
                {"all_attributes.fcpo_id": PI_no},
                {"$set": {
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": update_fields,
                    "lsi_key": new_status
                }}
            )

            conct.close_connection(client)
            return {'statusCode': 200, 'body': 'forecastpo updated successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'internal server error'}





    
    # def CmsEditUpdateForcastPurchaseOrder(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         PI_no = data["fcpo_id"]
    #         sk_timeStamp = (datetime.now()).isoformat()
            
    #         # Fetch existing forecast purchase order data
    #         pi_data = db_con.ForcastPurchaseOrder.find_one({"all_attributes.fcpo_id": PI_no})
    #         if not pi_data:
    #             return {'statusCode': 404, 'body': 'client forecast not found'}
            
    #         # Process forecast details to the new format
    #         forecast_details = {}
    #         for index, detail in enumerate(data.get("forecastDetails", []), start=1):
    #             forecast_key = f"forecast{index}"
    #             forecast_details[forecast_key] = detail
            
    #         # Process forecast invoice document to the new format
    #         documents = {}
    #         if "forecastInvoice" in data and data["forecastInvoice"].get('doc_body') and data["forecastInvoice"].get('doc_name'):
    #             doc_name = data["forecastInvoice"]["doc_name"]
    #             doc_body = data["forecastInvoice"]["doc_body"]
    #             file_key = file_uploads.upload_file("Forecast", "PtgCms" + env_type, "",
    #                                                 "forecastpurchaseOrder_" + PI_no,
    #                                                 doc_name, doc_body)
    #             documents[doc_name] = file_key
            
    #         # Prepare the fields to be updated
    #         update_fields = {
    #             "fcpo_id": PI_no,
    #             "buyer_details": data.get("buyerDetails", pi_data["all_attributes"].get("buyer_details", "")),
    #             "delivery_location": data.get("deliveryLocation", pi_data["all_attributes"].get("delivery_location", "")),
    #             "supplier_details": data.get("supplierDetails", pi_data["all_attributes"].get("supplier_details", "")),
    #             "supplierLocation": data.get("supplierLocation", pi_data["all_attributes"].get("supplierLocation", "")),
    #             "time_line_status": data.get("time_line_status", "PO"),
    #             "primary_document_details": data.get("primaryDocumentDetails", pi_data["all_attributes"].get("primary_document_details", {})),
    #             "forecast_details": forecast_details,
    #             "last_modified_date": sk_timeStamp[:10],
    #             "documents": documents
    #         }
            
    #         # Update the forecast purchase order in the database
    #         db_con.ForcastPurchaseOrder.update_one(
    #             {"all_attributes.fcpo_id": PI_no},
    #             {"$set": {
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": update_fields
    #             }}
    #         )

    #         conct.close_connection(client)
    #         return {'statusCode': 200, 'body': 'forecastpo updated successfully'}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'internal server error'}
        


    
    
    
    def CmsSaveDraftForecastPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
            document_name = data['forecastInvoice']["doc_name"]
            document_body = data['forecastInvoice']['doc_body']
            # Fetching existing forecast purchase orders
            ForcastPurchaseOrder_data = list(db_con.DraftForcastPurchaseOrder.find({}, {
                "pk_id": 1,
                "all_attributes.documents": 1,
                "all_attributes.primary_document_details.document_title": 1
            }))
            document_title = [i['all_attributes']['primary_document_details']['document_title'] for i in
                            ForcastPurchaseOrder_data]
            documents = [k for i in ForcastPurchaseOrder_data for k, j in i['all_attributes']['documents'].items()]
            if data["primaryDocumentDetails"]['document_date'] in ["N/A", "NA"]:
                data["primaryDocumentDetails"]['document_date'] = "0000-00-00"
            if data["primaryDocumentDetails"]['delivery_date'] in ["N/A", "NA"]:
                data["primaryDocumentDetails"]['delivery_date'] = "0000-00-00"
            if any(int(i['quantity']) <= 0 for i in data["forecastDetails"]):
                return {"statusCode": 400, "body": "Should not upload quantity less or equal to 0"}
            if any(float(i['order_value']) <= 0 for i in data["forecastDetails"]):
                return {"statusCode": 400, "body": "Should not upload order_value less than or equal 0"}
            if document_name[:-4] in documents:
                return {'statusCode': 400, "body": "Cannot upload duplicate file name"}
            draft_ForcastPurchaseOrder = list(db_con.DraftForcastPurchaseOrder.find({}, {
                "pk_id": 1,
                "all_attributes.documents": 1,
                "all_attributes.primary_document_details.document_title": 1
            }))
            document_title_draft = [i['all_attributes']['primary_document_details']['document_title'] for i in
                                    draft_ForcastPurchaseOrder]
            documents_draft = [k for i in draft_ForcastPurchaseOrder for k, j in
                            i['all_attributes']['documents'].items()]
            # Generate new forecast purchase order ID
            forecast_purchase_order_id = '1'
            if ForcastPurchaseOrder_data:
                update_id = list(db_con.all_tables.find({"pk_id": "top_ids"}))
                if "DraftForcastPurchaseOrder" in update_id[0]['all_attributes']:
                    update_id = (update_id[0]['all_attributes']['DraftForcastPurchaseOrder'][5:])
                else:
                    update_id = "1"
                forecast_purchase_order_id = str(int(update_id) + 1)
            print(forecast_purchase_order_id)
            filesLst = {"documents": {}}
            extra_type = ''
            if "forecastInvoice" in data and data["forecastInvoice"].get('doc_body') and data["forecastInvoice"].get(
                    'doc_name'):
                doc_name = data["forecastInvoice"]["doc_name"]
                doc_body = data["forecastInvoice"]["doc_body"]
                file_key = file_uploads.upload_file("DraftForecast", "PtgCms" + env_type, extra_type,
                                                    "DraftforecastpurchaseOrder_" + forecast_purchase_order_id,
                                                    data["forecastInvoice"]["doc_name"], doc_body)
                filesLst["documents"][doc_name] = file_key
            all_attributes = {}
            buyer_details = data['buyerDetails']
            delivery_location = data['deliveryLocation']
            supplier_details = data['supplierDetails']
            supplierLocation = data['supplierLocation']
            primary_document_details = data['primaryDocumentDetails']
            if primary_document_details['document_title'] in document_title:
                return {'statusCode': 400, "body": "Cannot upload duplicate document title"}
            if primary_document_details['document_title'] in document_title_draft:
                return {'statusCode': 200,
                        "message": "Cannot upload duplicate document title which is already present in drafts"}
            if document_name[:-4] in documents_draft:
                return {'statusCode': 200,
                        "message": "Cannot upload duplicate document file name which is already present in drafts"}
            forecastDetails = {f"forecast{inx + 1}": value.update(
                {"order_status": "", "payment_status": "", "po_name": "__",
                "cmts_atcmts": {}}) or value for inx, value in enumerate(data['forecastDetails'])}
            # document_month_year = datetime.strptime(primary_document_details['document_date'], '%Y-%m-%d').strftime(
            #     '%m-%y')

            document_date = primary_document_details['document_date']
            document_month = datetime.strptime(document_date, '%Y-%m-%d').strftime('%m')
            document_year = datetime.strptime(document_date, '%Y-%m-%d').strftime('%y')
            next_year = str(int(document_year) + 1).zfill(2)
            document_month_year = f"{document_month}/{document_year}-{next_year}"


            all_attributes["dfcpo_id"] = f"EPL/DFCPO/{forecast_purchase_order_id}/{document_month_year}"
            all_attributes['buyer_details'] = buyer_details
            all_attributes["delivery_location"] = delivery_location
            all_attributes["supplier_details"] = supplier_details
            all_attributes["supplierLocation"] = supplierLocation
            all_attributes["time_line_status"] = "PO"
            all_attributes["primary_document_details"] = primary_document_details
            all_attributes["forecast_details"] = forecastDetails
            all_attributes['last_modified_date'] = sk_timeStamp[:10]
            all_attributes.update(filesLst)
            item = {
                "pk_id": "DFCPO" + forecast_purchase_order_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": all_attributes,
                "gsipk_table": "DraftForcastPurchaseOrder",
                "gsisk_id": "open",
                "lsi_key": "Pending"
            }
            key = {'pk_id': "top_ids", 'sk_timeStamp': "123"}
            db_con.DraftForcastPurchaseOrder.insert_one(item)
            update_data = {
                '$set': {
                    'all_attributes.DraftForcastPurchaseOrder': "DFCPO" + forecast_purchase_order_id
                }
            }
            db_con.all_tables.update_one(key, update_data)
            response = {'statusCode': 200, 'body': 'Draft Forecast Purchase Order created successfully'}
            return response
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}
    



    
    def CmsDraftUpdateEditForecastPurchaseOrder(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            PI_no = data["fcpo_id"]
            sk_timeStamp = (datetime.now()).isoformat()

            pk_ids = list(db_con.ForcastPurchaseOrder.find({'pk_id': {'$regex': '^F'}}, {'pk_id': 1}))
            if len(pk_ids) == 0:
                pk_id = "FCPO1"
                max_pk = 1
            else:
                pk_filter = [int(x['pk_id'][4:]) for x in pk_ids]
                max_pk = max(pk_filter) + 1
                pk_id = "FCPO" + str(max_pk)

            # Fetch existing forecast purchase order data
            pi_data = db_con.DraftForcastPurchaseOrder.find_one({"all_attributes.dfcpo_id": PI_no})
            print(pi_data)
            if not pi_data:
                return {'statusCode': 404, 'body': 'client forecast not found'}

            # Process forecast details to the new format
            forecast_details = {}
            for index, detail in enumerate(data.get("forecastDetails", []), start=1):
                forecast_key = f"forecast{index}"
                forecast_details[forecast_key] = detail

            # Process forecast invoice document to the new format
            documents = {}
            if "forecastInvoice" in data and data["forecastInvoice"].get('doc_body') and data["forecastInvoice"].get('doc_name'):
                doc_name = data["forecastInvoice"]["doc_name"]
                doc_body = data["forecastInvoice"]["doc_body"]
                file_key = file_uploads.upload_file("Forecast", "PtgCms" + env_type, "",
                                                    "forecastpurchaseOrder_" + PI_no,
                                                    doc_name, doc_body)
                documents[doc_name] = file_key

            # Prepare the fields to be updated
            primary_document_details = data.get("primaryDocumentDetails", pi_data["all_attributes"].get("primaryDocumentDetails", {}))

            # Validate and process so_date
            so_date = primary_document_details.get("document_date", "")
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
            so_id = f"EPL/FCPO/{max_pk}/{so_month}/{so_year}-{so_next:02d}"

            update_fields = {
                "fcpo_id": so_id,
                "buyer_details": data.get("buyerDetails", pi_data["all_attributes"].get("buyer_details", "")),
                "delivery_location": data.get("deliveryLocation", pi_data["all_attributes"].get("delivery_location", "")),
                "supplier_details": data.get("supplierDetails", pi_data["all_attributes"].get("supplier_details", "")),
                "supplierLocation": data.get("supplierLocation", pi_data["all_attributes"].get("supplierLocation", "")),
                "time_line_status": data.get("time_line_status", "PO"),
                "primary_document_details": {
                    **primary_document_details  
                },
                "forecast_details": forecast_details,
                "last_modified_date": sk_timeStamp[:10],
                "documents": documents
            }
            db_con.DraftForcastPurchaseOrder.delete_one({"all_attributes.dfcpo_id": PI_no})
            db_con.DraftForcastPurchaseOrder.update_one(
                {"all_attributes.dfcpo_id": PI_no},
                {"$set": {
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": update_fields
                }}
            )
            

            db_con.all_tables.update_one({'pk_id': 'top_ids'}, {'$set': {'all_attributes.ForcastPurchaseOrder': pk_id}})
        # Insert the updated data into the ForcastPurchaseOrder table
            db_con.ForcastPurchaseOrder.insert_one({
                "pk_id": pk_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": update_fields,
                "gsipk_table": "ForcastPurchaseOrder",
                "gsisk_id": "open",
                "lsi_key": "Pending"
            })
            


            conct.close_connection(client)
            return {'statusCode': 200, 'body': 'draft forecastpo updated successfully'}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'internal server error'}



 
        


    

 
    def get_file_single_image(path):
            return path
    
    def get_files_for_image_pdf(paths):
            return paths